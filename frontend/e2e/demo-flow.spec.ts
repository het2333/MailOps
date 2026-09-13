import { expect, test } from "@playwright/test";


test("quotation workflow persists, pauses, and completes after approval", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByText("安全演示")).toBeVisible();

  await page.getByRole("button", { name: "运行报价审批" }).click();
  await expect(page.getByRole("heading", { name: "MODEL-X 报价请求" })).toBeVisible();
  await expect(page.getByText("需要审批")).toBeVisible();

  await page.reload();
  await page.getByText("MODEL-X 报价请求", { exact: true }).click();
  await page.getByRole("button", { name: "批准并发送" }).click();

  await expect(page.getByRole("heading", { name: "已完成" })).toBeVisible();
  await expect(page.getByText("1 已处理")).toBeVisible();
  await page.getByRole("button", { name: "切换到英文" }).click();
  await expect(page.getByText("Safe demo")).toBeVisible();
});
