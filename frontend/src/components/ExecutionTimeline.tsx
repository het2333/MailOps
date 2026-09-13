import { useI18n } from "../i18n";
import type { Execution } from "../types/api";

const steps = ["triage_email", "execute_tool", "draft_reply", "risk_check", "human_approval", "send_email"];

const riskKey = (reason: string) => {
  if (reason.includes("requires human approval")) return "risk.sensitive";
  if (reason.includes("cannot be automatically replied")) return "risk.unsupported";
  if (reason.includes("confidence is below")) return "risk.confidence";
  if (reason.includes("could not verify")) return "risk.unverified";
  return "";
};

export function ExecutionTimeline({ execution }: { execution?: Execution }) {
  const { language, t } = useI18n();
  if (!execution) return <section className="timeline empty-rail">{t("execution.empty")}</section>;
  const currentIndex = steps.indexOf(execution.current_node);
  return <section className="timeline"><div className="timeline-head"><div><p className="eyebrow">{t("execution.eyebrow")}</p><h2>{t(`status.${execution.status}`)}</h2></div>{execution.confidence !== undefined && <span className="confidence">{t("execution.confidence", { value: Math.round(execution.confidence * 100) })}</span>}</div>
    <ol>{steps.map((step, index) => <li className={index <= currentIndex || execution.status === "completed" ? "complete" : ""} key={step}><span>{index < currentIndex || execution.status === "completed" ? "✓" : index + 1}</span>{t(`step.${step}`)}</li>)}</ol>
    {execution.risk_reasons?.length ? <div className="risk-box"><b>{t("execution.reviewReason")}</b>{execution.risk_reasons.map((reason) => <p key={reason}>{language === "zh" && riskKey(reason) ? t(riskKey(reason)) : reason}</p>)}</div> : null}
    {execution.error_message ? <div className="error-box">{execution.error_message}</div> : null}
  </section>;
}
