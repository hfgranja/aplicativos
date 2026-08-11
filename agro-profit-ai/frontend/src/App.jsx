import { Navigate, Route, Routes } from "react-router-dom";
import AppShell from "./components/AppShell.jsx";
import { useAuth } from "./context/AuthContext.jsx";
import Alerts from "./pages/Alerts.jsx";
import DataImport from "./pages/DataImport.jsx";
import Dashboard from "./pages/Dashboard.jsx";
import FarmMap from "./pages/FarmMap.jsx";
import FieldDetail from "./pages/FieldDetail.jsx";
import Login from "./pages/Login.jsx";

function ProtectedRoute({ children }) {
  const { isAuthenticated } = useAuth();
  if (!isAuthenticated) return <Navigate to="/login" replace />;
  return children;
}

export default function App() {
  const { isAuthenticated } = useAuth();

  return (
    <Routes>
      <Route path="/login" element={isAuthenticated ? <Navigate to="/" replace /> : <Login />} />
      <Route
        path="/*"
        element={
          <ProtectedRoute>
            <AppShell>
              <Routes>
                <Route path="/" element={<Dashboard />} />
                <Route path="/map" element={<FarmMap />} />
                <Route path="/fields/:fieldId" element={<FieldDetail />} />
                <Route path="/data" element={<DataImport />} />
                <Route path="/alerts" element={<Alerts />} />
              </Routes>
            </AppShell>
          </ProtectedRoute>
        }
      />
    </Routes>
  );
}
