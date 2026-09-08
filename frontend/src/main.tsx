import { StrictMode } from "react";
import { createRoot } from "react-dom/client";

import "./styles.css";
import { WorkbenchPage } from "./pages/WorkbenchPage";

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <WorkbenchPage />
  </StrictMode>,
);
