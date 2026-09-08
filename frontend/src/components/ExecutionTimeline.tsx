import type { Execution } from "../types/api";

const steps = ["triage_email", "execute_tool", "draft_reply", "risk_check", "human_approval", "send_email"];
const label = (step: string) => step.replaceAll("_", " ").replace(/\b\w/g, (letter) => letter.toUpperCase());

export function ExecutionTimeline({ execution }: { execution?: Execution }) {
  if (!execution) return <section className="timeline empty-rail">Execution begins after the email is synced.</section>;
  const currentIndex = steps.indexOf(execution.current_node);
  return <section className="timeline"><div className="timeline-head"><div><p className="eyebrow">AGENT EXECUTION</p><h2>{execution.status.replaceAll("_", " ")}</h2></div>{execution.confidence !== undefined && <span className="confidence">{Math.round(execution.confidence * 100)}% confident</span>}</div>
    <ol>{steps.map((step, index) => <li className={index <= currentIndex || execution.status === "completed" ? "complete" : ""} key={step}><span>{index < currentIndex || execution.status === "completed" ? "✓" : index + 1}</span>{label(step)}</li>)}</ol>
    {execution.risk_reasons?.length ? <div className="risk-box"><b>Why review is required</b>{execution.risk_reasons.map((reason) => <p key={reason}>{reason}</p>)}</div> : null}
    {execution.error_message ? <div className="error-box">{execution.error_message}</div> : null}
  </section>;
}
