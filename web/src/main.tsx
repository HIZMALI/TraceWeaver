import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { App } from "./App";
import { isPublicDemo } from "./deployment";
import "@xyflow/react/dist/style.css";
import "./styles.css";
createRoot(document.getElementById("root")!).render(
  isPublicDemo() ? (
    <App />
  ) : (
    <StrictMode>
      <App />
    </StrictMode>
  ),
);
