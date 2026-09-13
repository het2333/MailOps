import { useCallback, useEffect, useState } from "react";

import { mailOpsApi } from "../api/client";
import { ApprovalPanel } from "../components/ApprovalPanel";
import { ConnectionBanner } from "../components/ConnectionBanner";
import { DemoLauncher } from "../components/DemoLauncher";
import { EmailDetail } from "../components/EmailDetail";
import { EvidencePanel } from "../components/EvidencePanel";
import { ExecutionTimeline } from "../components/ExecutionTimeline";
import { InboxList } from "../components/InboxList";
import type { Approval, Dashboard, DemoScenario, EmailDetail as EmailDetailType, EmailSummary, IntegrationStatus, RuntimeInfo } from "../types/api";

export function WorkbenchPage() {
  const [emails, setEmails] = useState<EmailSummary[]>([]);
  const [selected, setSelected] = useState<EmailDetailType>();
  const [approvals, setApprovals] = useState<Approval[]>([]);
  const [integration, setIntegration] = useState<IntegrationStatus>();
  const [dashboard, setDashboard] = useState<Dashboard>();
  const [runtime, setRuntime] = useState<RuntimeInfo>();
  const [scenarios, setScenarios] = useState<DemoScenario[]>([]);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);

  const refresh = useCallback(async () => {
    setError("");
    try {
      const nextRuntime = await mailOpsApi.runtime();
      const [nextEmails, nextIntegration, nextDashboard, nextApprovals, nextScenarios] = await Promise.all([mailOpsApi.listEmails(), mailOpsApi.integrationStatus(), mailOpsApi.dashboard(), mailOpsApi.listApprovals(), nextRuntime.mode === "demo" ? mailOpsApi.demoScenarios() : Promise.resolve([])]);
      setRuntime(nextRuntime);
      setEmails(Array.isArray(nextEmails) ? nextEmails : []);
      setIntegration(nextIntegration);
      setDashboard(nextDashboard);
      setApprovals(Array.isArray(nextApprovals) ? nextApprovals : []);
      setScenarios(nextScenarios);
    } catch (reason) { setError(reason instanceof Error ? reason.message : "MailOps could not load the inbox"); }
    finally { setLoading(false); }
  }, []);

  useEffect(() => { void refresh(); }, [refresh]);
  const selectEmail = async (emailId: string) => { try { setSelected(await mailOpsApi.getEmail(emailId)); } catch (reason) { setError(reason instanceof Error ? reason.message : "Email could not be loaded"); } };
  const approval = selected ? approvals.find((item) => item.email_id === selected.id && item.status === "pending") : undefined;
  const count = (name: string) => dashboard?.counts[name as keyof Dashboard["counts"]] ?? 0;
  const launchDemo = async (scenarioId: string) => {
    const email = await mailOpsApi.launchDemo(scenarioId);
    setSelected(email);
    await refresh();
  };
  const resetDemo = async () => {
    await mailOpsApi.resetDemo();
    setSelected(undefined);
    await refresh();
  };

  return <main className="app-shell"><header className="topbar"><div className="brand"><span>✦</span><b>MailOps</b><small>Agent</small>{runtime && <em>{runtime.mode === "demo" ? "DEMO" : "LIVE"}</em>}</div><div className="header-metrics"><span><b>{count("completed")}</b> resolved</span><span><b>{count("awaiting_approval")}</b> awaiting review</span></div></header>
    <ConnectionBanner integration={integration} onSync={refresh} />
    {error && <div className="page-error">{error}</div>}
    {runtime?.mode === "demo" && <div className="demo-stage"><DemoLauncher scenarios={scenarios} onLaunch={launchDemo} onReset={resetDemo} /><EvidencePanel runtime={runtime} /></div>}
    <section className="workbench"><aside className="inbox-column"><div className="column-heading"><div><p className="eyebrow">INBOX</p><h2>{loading ? "Loading…" : `${emails.length} conversations`}</h2></div><span className="filter-pill">All</span></div><InboxList emails={emails} selectedId={selected?.id} onSelect={selectEmail} /></aside>
      <div className="detail-column"><EmailDetail email={selected} /></div>
      <aside className="execution-column"><ExecutionTimeline execution={selected?.execution} /><ApprovalPanel approval={approval} onResolved={() => { void refresh(); if (selected) void selectEmail(selected.id); }} /></aside>
    </section>
  </main>;
}
