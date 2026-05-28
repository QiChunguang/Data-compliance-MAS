import { useState } from "react";
import { DiagnosticDashboard } from "./pages/DiagnosticDashboard";
import { ProductChatWorkbench } from "./pages/ProductChatWorkbench";

export default function App() {
  const [activeView, setActiveView] = useState("chat");

  const productViews = ['chat', 'agents', 'knowledge', 'risk', 'import', 'jobs', 'report', 'boundaries'];

  if (productViews.includes(activeView)) {
    return <ProductChatWorkbench activeView={activeView} onSelectView={setActiveView} />;
  }

  return <DiagnosticDashboard activeView={activeView} onSelectView={setActiveView} />;
}
