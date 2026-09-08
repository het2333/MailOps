import { useState } from "react";

import { mailOpsApi } from "../api/client";
import type { IntegrationStatus } from "../types/api";

export function ConnectionBanner({ integration, onSync }: { integration?: IntegrationStatus; onSync: () => Promise<void> }) {
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const connect = async () => { setBusy(true); setError(""); try { const result = await mailOpsApi.connectGoogle(); window.location.assign(result.authorization_url); } catch (reason) { setError(reason instanceof Error ? reason.message : "Connection failed"); setBusy(false); } };
  const sync = async () => { setBusy(true); setError(""); try { await mailOpsApi.sync(); await onSync(); } catch (reason) { setError(reason instanceof Error ? reason.message : "Sync failed"); } finally { setBusy(false); } };
  if (!integration) return <div className="connection-banner">Checking Gmail connection…</div>;
  return <div className="connection-banner"><span className={integration.connected ? "connection-dot connected" : "connection-dot"} />{integration.connected ? <><b>Gmail connected</b><span>{integration.account_email}</span><button onClick={sync} disabled={busy}>{busy ? "Syncing…" : "Sync now"}</button></> : <><b>Gmail not connected</b><span>{integration.configured ? "Connect the company account to activate MailOps." : "Add Google OAuth settings to connect Gmail."}</span><button onClick={connect} disabled={busy || !integration.configured}>Connect Gmail</button></>}{error && <span className="banner-error">{error}</span>}</div>;
}
