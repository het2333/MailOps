import { useState } from "react";

import { mailOpsApi } from "../api/client";
import { useI18n } from "../i18n";
import type { IntegrationStatus } from "../types/api";

export function ConnectionBanner({ integration, onSync }: { integration?: IntegrationStatus; onSync: () => Promise<void> }) {
  const { t } = useI18n();
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const connect = async () => { setBusy(true); setError(""); try { const result = await mailOpsApi.connectGoogle(); window.location.assign(result.authorization_url); } catch (reason) { setError(reason instanceof Error ? reason.message : t("connection.failed")); setBusy(false); } };
  const sync = async () => { setBusy(true); setError(""); try { await mailOpsApi.sync(); await onSync(); } catch (reason) { setError(reason instanceof Error ? reason.message : t("connection.syncFailed")); } finally { setBusy(false); } };
  if (!integration) return <div className="connection-banner">{t("connection.checking")}</div>;
  if (integration.mode === "demo") return <div className="connection-banner demo-connection"><span className="connection-dot connected" /><b>{t("connection.demoReady")}</b><span>{t("connection.demoDescription")}</span></div>;
  return <div className="connection-banner"><span className={integration.connected ? "connection-dot connected" : "connection-dot"} />{integration.connected ? <><b>{t("connection.connected")}</b><span>{integration.account_email}</span><button onClick={sync} disabled={busy}>{busy ? t("connection.syncing") : t("connection.syncNow")}</button></> : <><b>{t("connection.notConnected")}</b><span>{t(integration.configured ? "connection.connectHint" : "connection.configHint")}</span><button onClick={connect} disabled={busy || !integration.configured}>{t("connection.connect")}</button></>}{error && <span className="banner-error">{error}</span>}</div>;
}
