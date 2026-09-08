import base64
import time
from dataclasses import dataclass
from email.mime.text import MIMEText
from typing import Any

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from app.domain.schemas import InboundMessage


@dataclass
class SyncResult:
    messages: list[InboundMessage]
    cursor: str | None
    account_email: str


def _header(payload: dict[str, Any], name: str) -> str:
    return next((item["value"] for item in payload.get("headers", []) if item["name"].lower() == name.lower()), "")


def _body(payload: dict[str, Any]) -> str:
    if payload.get("mimeType") == "text/plain" and payload.get("body", {}).get("data"):
        return base64.urlsafe_b64decode(payload["body"]["data"] + "===").decode("utf-8", errors="replace")
    for part in payload.get("parts", []):
        text = _body(part)
        if text:
            return text
    return ""


class GmailProvider:
    def __init__(self, credentials: Credentials):
        self.service = build("gmail", "v1", credentials=credentials, cache_discovery=False)

    def sync_since(self, cursor: str | None) -> SyncResult:
        profile = self.service.users().getProfile(userId="me").execute()
        message_ids: list[str] = []
        next_cursor = profile.get("historyId", cursor)
        if cursor:
            try:
                history = self.service.users().history().list(userId="me", startHistoryId=cursor, historyTypes=["messageAdded"]).execute()
                message_ids = [item["message"]["id"] for event in history.get("history", []) for item in event.get("messagesAdded", [])]
                next_cursor = history.get("historyId", next_cursor)
            except HttpError as error:
                if error.resp.status != 404:
                    raise
        if not message_ids:
            listing = self.service.users().messages().list(userId="me", labelIds=["INBOX"], maxResults=25).execute()
            message_ids = [item["id"] for item in listing.get("messages", [])]
        messages: list[InboundMessage] = []
        for message_id in dict.fromkeys(message_ids):
            raw = self.service.users().messages().get(userId="me", id=message_id, format="full").execute()
            payload = raw.get("payload", {})
            messages.append(
                InboundMessage(
                    gmail_message_id=raw["id"],
                    gmail_thread_id=raw["threadId"],
                    sender=_header(payload, "From"),
                    subject=_header(payload, "Subject"),
                    body=_body(payload),
                )
            )
        return SyncResult(messages=messages, cursor=next_cursor, account_email=profile["emailAddress"])

    def send_reply(self, *, thread_id: str, to: str, subject: str, body: str) -> str:
        message = MIMEText(body, "plain", "utf-8")
        message["to"] = to
        message["subject"] = subject if subject.lower().startswith("re:") else f"Re: {subject}"
        encoded = base64.urlsafe_b64encode(message.as_bytes()).decode("ascii")
        for attempt in range(3):
            try:
                result = self.service.users().messages().send(userId="me", body={"raw": encoded, "threadId": thread_id}).execute()
                return result["id"]
            except HttpError as error:
                if error.resp.status not in {429, 500, 502, 503, 504} or attempt == 2:
                    raise
                time.sleep(0.25 * (2**attempt))
        raise RuntimeError("Gmail send retry loop exhausted")
