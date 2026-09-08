import { useState } from "react";

import { mailOpsApi } from "../api/client";
import type { Approval, Execution } from "../types/api";

export function ApprovalPanel({ approval, onResolved }: { approval?: Approval; onResolved: (execution: Execution) => void }) {
  const [draft, setDraft] = useState(approval?.draft_reply ?? "");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  if (!approval) return null;
  const resolve = async (decision: "approve" | "reject" | "edit_and_approve") => {
    setBusy(true); setError("");
    try { onResolved(await mailOpsApi.decideApproval(approval.id, decision, decision === "edit_and_approve" ? draft : undefined)); }
    catch (reason) { setError(reason instanceof Error ? reason.message : "Approval could not be saved"); }
    finally { setBusy(false); }
  };
  const changed = draft.trim() !== approval.draft_reply.trim();
  return <section className="approval-panel"><p className="eyebrow">HUMAN CHECKPOINT</p><h2>Approval required</h2><textarea aria-label="Editable reply" value={draft} onChange={(event) => setDraft(event.target.value)} rows={6} />
    {error && <p className="error-box">{error}</p>}<div className="approval-actions"><button className="secondary" disabled={busy} onClick={() => resolve("reject")}>Reject</button><button className="primary" disabled={busy} onClick={() => resolve(changed ? "edit_and_approve" : "approve")}>{busy ? "Sending…" : changed ? "Approve edit & send" : "Approve & send"}</button></div>
  </section>;
}
