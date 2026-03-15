import { BrowserRouter, Routes, Route } from 'react-router-dom'
import { AppShell } from './components/layout/AppShell'
import { HomePage } from './pages/HomePage'
import { TeachersPage } from './pages/TeachersPage'
import { NewObservationPage } from './pages/NewObservationPage'
import { ObservationDetailPage } from './pages/ObservationDetailPage'
import { HistoryPage } from './pages/HistoryPage'
import { EvolutionPage } from './pages/EvolutionPage'
import { C } from './colors'

const globalStyles = `
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body { background: ${C.bg}; color: ${C.text}; font-family: 'JetBrains Mono', monospace; }
  ::-webkit-scrollbar { width: 6px; height: 6px; }
  ::-webkit-scrollbar-track { background: ${C.surface}; }
  ::-webkit-scrollbar-thumb { background: ${C.surface3}; border-radius: 3px; }
  input, textarea, select { outline: none; }
  input::placeholder, textarea::placeholder { color: rgba(232,232,240,0.3); }
`

export default function App() {
  return (
    <>
      <style>{globalStyles}</style>
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<AppShell />}>
            <Route index element={<HomePage />} />
            <Route path="professores" element={<TeachersPage />} />
            <Route path="nova-observacao" element={<NewObservationPage />} />
            <Route path="observacoes/:id" element={<ObservationDetailPage />} />
            <Route path="historico" element={<HistoryPage />} />
            <Route path="evolucao" element={<EvolutionPage />} />
          </Route>
        </Routes>
      </BrowserRouter>
    </>
  )
}
