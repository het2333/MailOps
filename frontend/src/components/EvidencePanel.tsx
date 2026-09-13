import { useI18n } from "../i18n";
import type { RuntimeInfo } from "../types/api";


const asPercent = (value: number) => `${Math.round(value * 100)}%`;

export function EvidencePanel({ runtime }: { runtime: RuntimeInfo }) {
  const { t } = useI18n();
  const evaluation = runtime.evaluation;
  return (
    <aside className="evidence-panel">
      <div className="evidence-heading">
        <div>
          <p className="eyebrow">{t("evidence.eyebrow")}</p>
          <h2>{evaluation ? t("evidence.evaluation", { count: evaluation.case_count }) : t("evidence.unavailable")}</h2>
        </div>
        {evaluation && <span>{evaluation.provider}</span>}
      </div>
      {evaluation && (
        <div className="metric-grid">
          <div><b>{asPercent(evaluation.intent_accuracy)}</b><span>{t("evidence.intent")}</span></div>
          <div><b>{asPercent(evaluation.human_review_recall)}</b><span>{t("evidence.review")}</span></div>
          <div><b>{evaluation.unsafe_auto_send_count}</b><span>{t("evidence.unsafe")}</span></div>
        </div>
      )}
      <ul className="evidence-list">
        {runtime.reliability.map((item) => (
          <li key={item.id}>
            <span>✓</span>
            <div><b>{t(`reliability.${item.id}`) || item.label}</b><small>{item.verified_by}</small></div>
          </li>
        ))}
      </ul>
    </aside>
  );
}
