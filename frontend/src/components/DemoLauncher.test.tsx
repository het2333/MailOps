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

  await userEvent.click(screen.getByRole("button", { name: "运行Quotation approval" }));

  expect(screen.getByRole("status")).toHaveTextContent("正在运行真实工作流…");
  await waitFor(() => expect(onLaunch).toHaveBeenCalledWith("quotation"));
});


it("offers a session-scoped reset action", async () => {
  const onReset = vi.fn().mockResolvedValue(undefined);
  render(<DemoLauncher scenarios={[]} onLaunch={vi.fn()} onReset={onReset} />);

  await userEvent.click(screen.getByRole("button", { name: "重置我的演示" }));

  await waitFor(() => expect(onReset).toHaveBeenCalledOnce());
});
