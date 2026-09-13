import { useEffect, useState } from "react";

import { mailOpsApi } from "../api/client";
import { useI18n } from "../i18n";
import type { Approval, Execution } from "../types/api";

export function ApprovalPanel({ approval, onResolved }: { approval?: Approval; onResolved: (execution: Execution) => void }) {
  const { t } = useI18n();
  const [draft, setDraft] = useState(approval?.draft_reply ?? "");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  useEffect(() => { setDraft(approval?.draft_reply ?? ""); }, [approval?.id, approval?.draft_reply]);
  if (!approval) return null;
  const resolve = async (decision: "approve" | "reject" | "edit_and_approve") => {
    setBusy(true); setError("");
    try { onResolved(await mailOpsApi.decideApproval(approval.id, decision, decision === "edit_and_approve" ? draft : undefined)); }
    catch (reason) { setError(reason instanceof Error ? reason.message : t("approval.failed")); }
    finally { setBusy(false); }
  };
  const changed = draft.trim() !== approval.draft_reply.trim();
  return <section className="approval-panel"><p className="eyebrow">{t("approval.eyebrow")}</p><h2>{t("approval.required")}</h2><textarea aria-label={t("approval.editable")} value={draft} onChange={(event) => setDraft(event.target.value)} rows={6} />
    {error && <p className="error-box">{error}</p>}<div className="approval-actions"><button className="secondary" disabled={busy} onClick={() => resolve("reject")}>{t("approval.reject")}</button><button className="primary" disabled={busy} onClick={() => resolve(changed ? "edit_and_approve" : "approve")}>{busy ? t("approval.sending") : changed ? t("approval.approveEdit") : t("approval.approve")}</button></div>
  </section>;
}
