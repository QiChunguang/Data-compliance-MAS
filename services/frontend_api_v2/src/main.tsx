import React from "react";
import ReactDOM from "react-dom/client";
import App from "./App";
import "./styles/global.css";
import "./styles/design-tokens.css";
import "./styles/product-shell.css";
import "./styles/chat-workspace.css";
import "./styles/artifact-drawer.css";
import "./styles/workbench.css";
import "./styles/product-views.css";
import "./styles/fe8-3-1a-clean-pass.css";

ReactDOM.createRoot(document.getElementById("root") as HTMLElement).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
);
