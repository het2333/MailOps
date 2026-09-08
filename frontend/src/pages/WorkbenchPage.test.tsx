import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { expect, it, vi } from "vitest";

import { WorkbenchPage } from "./WorkbenchPage";

const inbox = [{ id: "email-1", sender: "buyer@example.com", subject: "Quote 100 MODEL-X", status: "awaiting_approval", received_at: "2026-09-08T09:00:00Z", execution_status: "waiting_for_approval" }];
const detail = { ...inbox[0], gmail_thread_id: "thread-1", body: "Please quote 100 MODEL-X.", execution: { id: "execution-1", status: "waiting_for_approval", current_node: "human_approval", intent: "quotation", confidence: 0.96, draft_reply: "The quote is USD 8,900.", tool_result: { total: "8900.00" }, risk_reasons: ["quotation requires human approval"] } };

it("loads an email from the API and reveals its execution context", async () => {
  vi.stubGlobal("fetch", vi.fn((input: RequestInfo | URL) => {
    const url = String(input);
    const body = url.startsWith("/api/emails/") ? detail : url === "/api/emails" ? inbox : url === "/api/integrations/status" ? { configured: true, connected: true, account_email: "ops@example.com" } : { counts: {}, activity: [] };
    return Promise.resolve(new Response(JSON.stringify(body), { status: 200 }));
  }));

  render(<WorkbenchPage />);
  await userEvent.click(await screen.findByText("Quote 100 MODEL-X"));

  await waitFor(() => expect(screen.getByText("Awaiting approval")).toBeInTheDocument());
  expect(screen.getByText("The quote is USD 8,900.")).toBeInTheDocument();
});
