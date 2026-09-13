from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import HTMLResponse
from google_auth_oauthlib.flow import Flow

from app.core.config import get_settings
from app.providers.gmail import GmailProvider
from app.providers.google_credentials import GOOGLE_SCOPES, GoogleCredentialStore
from app.services.sync_service import SyncService

router = APIRouter(prefix="/api/integrations", tags=["integrations"])


def _store(request: Request) -> GoogleCredentialStore:
    return GoogleCredentialStore(request.app.state.email_service.session, get_settings())


def _flow() -> Flow:
    settings = get_settings()
    if not settings.google_configured:
        raise HTTPException(status_code=400, detail="Google OAuth is not configured")
    flow = Flow.from_client_config(
        {
            "web": {
                "client_id": settings.google_client_id,
                "client_secret": settings.google_client_secret.get_secret_value() if settings.google_client_secret else "",
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "redirect_uris": [settings.google_redirect_uri],
            }
        },
        scopes=GOOGLE_SCOPES,
        redirect_uri=settings.google_redirect_uri,
    )
    return flow


@router.get("/status")
def status(request: Request) -> dict[str, object]:
    if request.app.state.settings.demo_mode:
        return {"configured": True, "connected": True, "account_email": "demo@mailops.example.com", "last_sync_cursor": None, "mode": "demo"}
    state = _store(request).state()
    settings = get_settings()
    return {
        "configured": settings.google_configured,
        "connected": bool(state and state.credential_blob),
        "account_email": state.account_email if state else None,
        "last_sync_cursor": state.sync_cursor if state else None,
    }


@router.post("/google/connect")
def connect(request: Request) -> dict[str, str]:
    if request.app.state.settings.demo_mode:
        raise HTTPException(status_code=409, detail="Google OAuth is disabled in demo mode")
    flow = _flow()
    url, state = flow.authorization_url(access_type="offline", include_granted_scopes="true", prompt="consent")
    request.app.state.oauth_state = state
    return {"authorization_url": url}


@router.get("/google/callback", response_class=HTMLResponse)
def callback(request: Request, code: str, state: str) -> HTMLResponse:
    expected_state = getattr(request.app.state, "oauth_state", None)
    if not expected_state or state != expected_state:
        raise HTTPException(status_code=400, detail="OAuth state did not match")
    flow = _flow()
    flow.fetch_token(code=code)
    provider = GmailProvider(flow.credentials)
    account_email = provider.service.users().getProfile(userId="me").execute()["emailAddress"]
    _store(request).save(flow.credentials, account_email)
    return HTMLResponse("<script>window.close()</script><p>MailOps connected to Gmail. You can return to the app.</p>")


@router.post("/sync")
def sync(request: Request):
    if request.app.state.settings.demo_mode:
        raise HTTPException(status_code=409, detail="Gmail sync is disabled in demo mode; launch a catalog scenario")
    service = SyncService(_store(request), request.app.state.email_service, request.app.state.execution_service_factory)
    try:
        return service.run_once()
    except RuntimeError as error:
        raise HTTPException(status_code=409, detail=str(error)) from error
