import type { RuntimeInfo } from "../types/api";


const asPercent = (value: number) => `${Math.round(value * 100)}%`;

export function EvidencePanel({ runtime }: { runtime: RuntimeInfo }) {
  const evaluation = runtime.evaluation;
  return (
    <aside className="evidence-panel">
      <div className="evidence-heading">
        <div>
          <p className="eyebrow">MEASURED EVIDENCE</p>
          <h2>{evaluation ? `${evaluation.case_count}-case evaluation` : "Evaluation unavailable"}</h2>
        </div>
        {evaluation && <span>{evaluation.provider}</span>}
      </div>
      {evaluation && (
        <div className="metric-grid">
          <div><b>{asPercent(evaluation.intent_accuracy)}</b><span>Intent accuracy</span></div>
          <div><b>{asPercent(evaluation.human_review_recall)}</b><span>Review recall</span></div>
          <div><b>{evaluation.unsafe_auto_send_count}</b><span>Unsafe sends</span></div>
        </div>
      )}
      <ul className="evidence-list">
        {runtime.reliability.map((item) => (
          <li key={item.id}>
            <span>✓</span>
            <div><b>{item.label}</b><small>{item.verified_by}</small></div>
          </li>
        ))}
      </ul>
    </aside>
  );
}
