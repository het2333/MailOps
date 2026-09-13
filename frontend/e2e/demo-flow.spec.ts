import { expect, test } from "@playwright/test";


test("quotation workflow persists, pauses, and completes after approval", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByText("Safe demo")).toBeVisible();

  await page.getByRole("button", { name: "Run quotation approval" }).click();
  await expect(page.getByRole("heading", { name: "Pricing request for MODEL-X" })).toBeVisible();
  await expect(page.getByText("Approval required")).toBeVisible();

  await page.reload();
  await page.getByText("Pricing request for MODEL-X", { exact: true }).click();
  await page.getByRole("button", { name: "Approve & send" }).click();

  await expect(page.getByRole("heading", { name: "completed" })).toBeVisible();
  await expect(page.getByText("1 resolved")).toBeVisible();
});
