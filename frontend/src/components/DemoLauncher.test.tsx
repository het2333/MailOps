import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { expect, it, vi } from "vitest";

import { DemoLauncher } from "./DemoLauncher";


it("launches a named scenario with immediate progress feedback", async () => {
  const onLaunch = vi.fn().mockImplementation(() => new Promise<void>(() => undefined));
  render(<DemoLauncher scenarios={[{
    id: "quotation",
    title: "Quotation approval",
    description: "Calculate a verified quote and pause.",
    expected_outcome: "Waits for your approval",
  }]} onLaunch={onLaunch} onReset={vi.fn()} />);

  await userEvent.click(screen.getByRole("button", { name: "Run quotation approval" }));

  expect(screen.getByText("Running the real workflow…")).toBeInTheDocument();
  await waitFor(() => expect(onLaunch).toHaveBeenCalledWith("quotation"));
});


it("offers a session-scoped reset action", async () => {
  const onReset = vi.fn().mockResolvedValue(undefined);
  render(<DemoLauncher scenarios={[]} onLaunch={vi.fn()} onReset={onReset} />);

  await userEvent.click(screen.getByRole("button", { name: "Reset my demo" }));

  await waitFor(() => expect(onReset).toHaveBeenCalledOnce());
});
