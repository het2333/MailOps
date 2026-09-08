from datetime import datetime, timedelta, timezone

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build


class CalendarProvider:
    """Google Calendar adapter used only after the graph has validated a meeting flow."""

    def __init__(self, credentials: Credentials):
        self.service = build("calendar", "v3", credentials=credentials, cache_discovery=False)

    def list_free_slots(self, _request: str) -> list[str]:
        now = datetime.now(timezone.utc).replace(minute=0, second=0, microsecond=0)
        start = now + timedelta(days=1)
        end = start + timedelta(days=7)
        busy = self.service.freebusy().query(
            body={"timeMin": start.isoformat(), "timeMax": end.isoformat(), "items": [{"id": "primary"}]}
        ).execute()["calendars"]["primary"].get("busy", [])
        busy_ranges = [(item["start"], item["end"]) for item in busy]
        candidates: list[str] = []
        for day in range(5):
            for hour in (10, 14):
                candidate = (start + timedelta(days=day)).replace(hour=hour)
                candidate_end = candidate + timedelta(hours=1)
                if not any(begin < candidate_end.isoformat() and end_value > candidate.isoformat() for begin, end_value in busy_ranges):
                    candidates.append(candidate.isoformat())
        return candidates[:3]

    def create_event(self, request: str) -> str:
        start = (datetime.now(timezone.utc) + timedelta(days=1)).replace(hour=14, minute=0, second=0, microsecond=0)
        event = self.service.events().insert(
            calendarId="primary",
            body={
                "summary": "Customer meeting via MailOps",
                "description": request,
                "start": {"dateTime": start.isoformat()},
                "end": {"dateTime": (start + timedelta(hours=1)).isoformat()},
            },
        ).execute()
        return event["id"]
