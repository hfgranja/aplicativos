import { Route, Routes } from "react-router-dom";
import AppShell from "./components/layout/AppShell.jsx";
import { MerchantProvider } from "./context/MerchantContext.jsx";
import Alerts from "./pages/Alerts.jsx";
import AuditLog from "./pages/AuditLog.jsx";
import CreateIntent from "./pages/CreateIntent.jsx";
import DashboardCost from "./pages/DashboardCost.jsx";
import DashboardPerformance from "./pages/DashboardPerformance.jsx";
import DashboardReconciliation from "./pages/DashboardReconciliation.jsx";
import DashboardSettlement from "./pages/DashboardSettlement.jsx";
import IntentDetail from "./pages/IntentDetail.jsx";
import IntentsList from "./pages/IntentsList.jsx";
import PolicyConfig from "./pages/PolicyConfig.jsx";

export default function App() {
  return (
    <MerchantProvider>
      <AppShell>
        <Routes>
          <Route path="/" element={<CreateIntent />} />
          <Route path="/intents" element={<IntentsList />} />
          <Route path="/intents/:intentId" element={<IntentDetail />} />
          <Route path="/policy" element={<PolicyConfig />} />
          <Route path="/dashboard/performance" element={<DashboardPerformance />} />
          <Route path="/dashboard/cost" element={<DashboardCost />} />
          <Route path="/dashboard/settlement" element={<DashboardSettlement />} />
          <Route path="/dashboard/reconciliation" element={<DashboardReconciliation />} />
          <Route path="/alerts" element={<Alerts />} />
          <Route path="/audit" element={<AuditLog />} />
        </Routes>
      </AppShell>
    </MerchantProvider>
  );
}
