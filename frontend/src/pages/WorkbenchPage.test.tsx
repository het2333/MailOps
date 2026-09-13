import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { expect, it, vi } from "vitest";

import { WorkbenchPage } from "./WorkbenchPage";

const inbox = [{ id: "email-1", sender: "buyer@example.com", subject: "Quote 100 MODEL-X", status: "awaiting_approval", received_at: "2026-09-08T09:00:00Z", execution_status: "waiting_for_approval" }];
const detail = { ...inbox[0], gmail_thread_id: "thread-1", body: "Please quote 100 MODEL-X.", execution: { id: "execution-1", status: "waiting_for_approval", current_node: "human_approval", intent: "quotation", confidence: 0.96, draft_reply: "The quote is USD 8,900.", tool_result: { total: "8900.00" }, risk_reasons: ["quotation requires human approval"] } };

it("loads an email from the API and reveals its execution context", async () => {
  vi.stubGlobal("fetch", vi.fn((input: RequestInfo | URL) => {
    const url = String(input);
    const body = url.startsWith("/api/emails/") ? detail : url === "/api/emails" ? inbox : url === "/api/runtime" ? { mode: "demo", delivery: "simulated", calendar: "simulated", description: "External delivery is simulated; workflow state and approvals are persisted.", reliability: [{ id: "single_send", label: "Single-send guard", verified_by: "pytest: workflow" }], evaluation: { case_count: 12, intent_accuracy: 1, argument_exact_match: 1, human_review_recall: 1, unsafe_auto_send_count: 0, latency_p50_ms: 0.01, latency_p95_ms: 0.02, provider: "deterministic-demo", dataset_version: "2026-09-14.1", generated_at: "2026-09-14T00:00:00Z" } } : url === "/api/demo/scenarios" ? [{ id: "quotation", title: "Quotation approval", description: "Calculate a verified quote and pause.", expected_outcome: "Waits for your approval" }] : url === "/api/integrations/status" ? { configured: true, connected: true, account_email: "demo@mailops.example.com", mode: "demo" } : url === "/api/approvals" ? [] : { counts: {}, activity: [] };
    return Promise.resolve(new Response(JSON.stringify(body), { status: 200 }));
  }));

  render(<WorkbenchPage />);
  await userEvent.click(await screen.findByText("Quote 100 MODEL-X"));

  await waitFor(() => expect(screen.getByRole("heading", { name: "等待审批" })).toBeInTheDocument());
  expect(screen.getByText("The quote is USD 8,900.")).toBeInTheDocument();
  expect(screen.getByText("安全演示")).toBeInTheDocument();
  expect(screen.getByText("12 条用例评估")).toBeInTheDocument();
  expect(screen.getByText("不会发送外部邮件")).toBeInTheDocument();
  expect(fetch).toHaveBeenCalledWith("/api/runtime", expect.objectContaining({ headers: expect.objectContaining({ "Accept-Language": "zh-CN" }) }));
});
