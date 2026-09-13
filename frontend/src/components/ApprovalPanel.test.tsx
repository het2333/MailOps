import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { expect, it, vi } from "vitest";

import { ApprovalPanel } from "./ApprovalPanel";

const approval = {
  id: "approval-1",
  status: "pending" as const,
  draft_reply: "The quote is USD 8,900.",
  action_summary: "quotation email to buyer@example.com",
  risk_reasons: ["quotation requires human approval"],
  email_id: "email-1",
  email_subject: "Quote 100 MODEL-X",
  email_sender: "buyer@example.com",
};

it("approves a pending quote and returns the persisted execution", async () => {
  const onResolved = vi.fn();
  vi.stubGlobal(
    "fetch",
    vi.fn().mockResolvedValue(
      new Response(JSON.stringify({ id: "execution-1", status: "completed", current_node: "completed" }), { status: 200 }),
    ),
  );

  render(<ApprovalPanel approval={approval} onResolved={onResolved} />);
  await userEvent.click(screen.getByRole("button", { name: "Approve & send" }));

  await waitFor(() => expect(onResolved).toHaveBeenCalledWith(expect.objectContaining({ status: "completed" })));
});

it("hydrates the draft when an approval arrives after the page loads", () => {
  const { rerender } = render(<ApprovalPanel approval={undefined} onResolved={vi.fn()} />);

  rerender(<ApprovalPanel approval={approval} onResolved={vi.fn()} />);

  expect(screen.getByRole("textbox", { name: "Editable reply" })).toHaveValue("The quote is USD 8,900.");
  expect(screen.getByRole("button", { name: "Approve & send" })).toBeInTheDocument();
});
