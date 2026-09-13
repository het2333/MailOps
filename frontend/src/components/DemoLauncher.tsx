import { useState } from "react";

import type { DemoScenario } from "../types/api";


const icons: Record<string, string> = { order: "↗", quotation: "$", meeting: "◷", injection: "⌁" };

export function DemoLauncher({ scenarios, onLaunch, onReset }: {
  scenarios: DemoScenario[];
  onLaunch: (scenarioId: string) => Promise<void>;
  onReset: () => Promise<void>;
}) {
  const [busy, setBusy] = useState("");
  const [status, setStatus] = useState("");
  const launch = async (scenarioId: string) => {
    setBusy(scenarioId);
    setStatus("Running the real workflow…");
    try {
      await onLaunch(scenarioId);
      setStatus("Workflow persisted. Inspect the email and execution trace below.");
    } catch {
      setStatus("The workflow could not start. Try again.");
    } finally {
      setBusy("");
    }
  };
  const reset = async () => {
    setBusy("reset");
    setStatus("Resetting your demo session…");
    try {
      await onReset();
      setStatus("Your demo session is ready for a fresh run.");
    } catch {
      setStatus("The demo could not reset. Try again.");
    } finally {
      setBusy("");
    }
  };
  return <section className="demo-hero">
    <div className="demo-intro">
      <div className="mode-line"><span className="mode-badge">Safe demo</span><span>No external email is sent</span></div>
      <h1>Turn customer email into verified action.</h1>
      <p>Pick a scenario. MailOps will classify it, query business data, apply policy, and show every persisted step.</p>
      <button className="text-action" onClick={reset} disabled={Boolean(busy)} aria-label="Reset my demo">Reset my demo</button>
    </div>
    <div className="scenario-grid">
      {scenarios.map((scenario) => <article className="scenario-card" key={scenario.id}>
        <span className={`scenario-icon ${scenario.id}`}>{icons[scenario.id] ?? "→"}</span>
        <div><h2>{scenario.title}</h2><p>{scenario.description}</p><small>{scenario.expected_outcome}</small></div>
        <button onClick={() => void launch(scenario.id)} disabled={Boolean(busy)} aria-label={`Run ${scenario.title.toLowerCase()}`}>{busy === scenario.id ? "Running…" : "Run"}</button>
      </article>)}
    </div>
    {status && <p className="demo-status" role="status">{status}</p>}
  </section>;
}
