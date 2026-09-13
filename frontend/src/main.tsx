import { StrictMode } from "react";
import { createRoot } from "react-dom/client";

import "./styles.css";
import { LanguageProvider } from "./i18n";
import { WorkbenchPage } from "./pages/WorkbenchPage";

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <LanguageProvider><WorkbenchPage /></LanguageProvider>
  </StrictMode>,
);
