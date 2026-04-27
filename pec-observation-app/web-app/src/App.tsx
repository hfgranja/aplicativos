import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { LoginPage }         from './pages/LoginPage'
import { ObservationsPage }  from './pages/ObservationsPage'
import { SchoolsPage }       from './pages/SchoolsPage'
import { KnowledgePage }     from './pages/KnowledgePage'
import { BestPracticesPage } from './pages/BestPracticesPage'
import { SyncPage }          from './pages/SyncPage'

function RequireAuth({ children }: { children: React.ReactNode }) {
  const token = localStorage.getItem('pec_access_token')
  return token ? <>{children}</> : <Navigate to="/login" replace />
}

export function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login"         element={<LoginPage />} />
        <Route path="/"              element={<Navigate to="/observacoes" replace />} />
        <Route path="/observacoes"   element={<RequireAuth><ObservationsPage /></RequireAuth>} />
        <Route path="/escolas"       element={<RequireAuth><SchoolsPage /></RequireAuth>} />
        <Route path="/biblioteca"    element={<RequireAuth><KnowledgePage /></RequireAuth>} />
        <Route path="/boas-praticas" element={<RequireAuth><BestPracticesPage /></RequireAuth>} />
        <Route path="/sincronizar"   element={<RequireAuth><SyncPage /></RequireAuth>} />
        <Route path="*"              element={<Navigate to="/observacoes" replace />} />
      </Routes>
    </BrowserRouter>
  )
}
