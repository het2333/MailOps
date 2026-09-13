import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { expect, it } from "vitest";

import { LanguageProvider, useI18n } from "./i18n";


function Probe() {
  const { language, setLanguage, t } = useI18n();
  return <><p>{t("demo.safe")}</p><button onClick={() => setLanguage(language === "zh" ? "en" : "zh")}>{t("language.switch")}</button></>;
}


it("defaults to Chinese and can switch to English", async () => {
  render(<LanguageProvider><Probe /></LanguageProvider>);

  expect(screen.getByText("安全演示")).toBeInTheDocument();
  await userEvent.click(screen.getByRole("button", { name: "English" }));
  expect(screen.getByText("Safe demo")).toBeInTheDocument();
});
