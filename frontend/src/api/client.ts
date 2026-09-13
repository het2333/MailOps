import type { Approval, Dashboard, DemoScenario, EmailDetail, EmailSummary, Execution, IntegrationStatus, RuntimeInfo } from "../types/api";

const sessionKey = "mailops_demo_session";
let memorySession = "";

function demoSession(): string {
  const cookie = typeof document === "undefined" ? "" : document.cookie.split("; ").find((item) => item.startsWith(`${sessionKey}=`));
  const existing = cookie?.split("=")[1] ?? memorySession;
  if (existing) return existing;
  const random = globalThis.crypto?.randomUUID?.().replaceAll("-", "").slice(0, 16) ?? Math.random().toString(36).slice(2, 18);
  const value = `web_${random}`;
  memorySession = value;
  if (typeof document !== "undefined") document.cookie = `${sessionKey}=${value}; Path=/; SameSite=Lax`;
  return value;
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(path, { headers: { "Content-Type": "application/json", "X-Demo-Session": demoSession(), ...(init?.headers ?? {}) }, ...init });
  if (!response.ok) {
    const payload = await response.json().catch(() => null) as { detail?: string } | null;
    throw new Error(payload?.detail ?? `Request failed (${response.status})`);
  }
  return response.json() as Promise<T>;
}

export const mailOpsApi = {
  listEmails: () => request<EmailSummary[]>("/api/emails"),
  getEmail: (emailId: string) => request<EmailDetail>(`/api/emails/${emailId}`),
  integrationStatus: () => request<IntegrationStatus>("/api/integrations/status"),
  dashboard: () => request<Dashboard>("/api/dashboard"),
  listApprovals: () => request<Approval[]>("/api/approvals"),
  runtime: () => request<RuntimeInfo>("/api/runtime"),
  demoScenarios: () => request<DemoScenario[]>("/api/demo/scenarios"),
  launchDemo: (scenarioId: string) => request<EmailDetail>(`/api/demo/scenarios/${scenarioId}`, { method: "POST" }),
  resetDemo: () => request<{ deleted: number }>("/api/demo/reset", { method: "POST" }),
  sync: () => request<{ scanned: number; ingested: number; started: number }>("/api/integrations/sync", { method: "POST" }),
  connectGoogle: () => request<{ authorization_url: string }>("/api/integrations/google/connect", { method: "POST" }),
  decideApproval: (approvalId: string, decision: "approve" | "reject" | "edit_and_approve", editedReply?: string) =>
    request<Execution>(`/api/approvals/${approvalId}/decision`, { method: "POST", body: JSON.stringify({ decision, edited_reply: editedReply }) }),
};
