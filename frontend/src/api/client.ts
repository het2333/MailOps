import type { Approval, Dashboard, EmailDetail, EmailSummary, Execution, IntegrationStatus } from "../types/api";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(path, { headers: { "Content-Type": "application/json", ...(init?.headers ?? {}) }, ...init });
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
  sync: () => request<{ scanned: number; ingested: number; started: number }>("/api/integrations/sync", { method: "POST" }),
  connectGoogle: () => request<{ authorization_url: string }>("/api/integrations/google/connect", { method: "POST" }),
  decideApproval: (approvalId: string, decision: "approve" | "reject" | "edit_and_approve", editedReply?: string) =>
    request<Execution>(`/api/approvals/${approvalId}/decision`, { method: "POST", body: JSON.stringify({ decision, edited_reply: editedReply }) }),
};
