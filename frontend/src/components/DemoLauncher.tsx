import { useState } from "react";

import { useI18n } from "../i18n";
import type { DemoScenario } from "../types/api";


const icons: Record<string, string> = { order: "↗", quotation: "$", meeting: "◷", injection: "⌁" };

export function DemoLauncher({ scenarios, onLaunch, onReset }: {
  scenarios: DemoScenario[];
  onLaunch: (scenarioId: string) => Promise<void>;
  onReset: () => Promise<void>;
}) {
  const { t } = useI18n();
  const [busy, setBusy] = useState("");
  const [status, setStatus] = useState("");
  const launch = async (scenarioId: string) => {
    setBusy(scenarioId);
    setStatus(t("demo.running"));
    try {
      await onLaunch(scenarioId);
      setStatus(t("demo.completed"));
    } catch {
      setStatus(t("demo.failed"));
    } finally {
      setBusy("");
    }
  };
  const reset = async () => {
    setBusy("reset");
    setStatus(t("demo.resetting"));
    try {
      await onReset();
      setStatus(t("demo.resetDone"));
    } catch {
      setStatus(t("demo.resetFailed"));
    } finally {
      setBusy("");
    }
  };
  return <section className="demo-hero">
    <div className="demo-intro">
      <div className="mode-line"><span className="mode-badge">{t("demo.safe")}</span><span>{t("demo.noExternal")}</span></div>
      <h1>{t("demo.title")}</h1>
      <p>{t("demo.description")}</p>
      <button className="text-action" onClick={reset} disabled={Boolean(busy)} aria-label={t("demo.reset")}>{t("demo.reset")}</button>
    </div>
    <div className="scenario-grid">
      {scenarios.map((scenario) => <article className="scenario-card" key={scenario.id}>
        <span className={`scenario-icon ${scenario.id}`}>{icons[scenario.id] ?? "→"}</span>
        <div><h2>{scenario.title}</h2><p>{scenario.description}</p><small>{scenario.expected_outcome}</small></div>
        <button onClick={() => void launch(scenario.id)} disabled={Boolean(busy)} aria-label={t("demo.runLabel", { title: scenario.title })}>{busy === scenario.id ? t("demo.runningShort") : t("demo.run")}</button>
      </article>)}
    </div>
    {status && <p className="demo-status" role="status">{status}</p>}
  </section>;
}
