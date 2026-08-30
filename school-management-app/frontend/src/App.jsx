import { Routes, Route } from "react-router-dom";
import Layout from "./components/Layout";
import Login from "./pages/Login";
import Dashboard from "./pages/Dashboard";
import Students from "./pages/Students";
import Classes from "./pages/Classes";
import Teachers from "./pages/Teachers";
import Attendance from "./pages/Attendance";
import Grades from "./pages/Grades";
import Occurrences from "./pages/Occurrences";
import Announcements from "./pages/Announcements";

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route element={<Layout />}>
        <Route path="/" element={<Dashboard />} />
        <Route path="/alunos" element={<Students />} />
        <Route path="/turmas" element={<Classes />} />
        <Route path="/professores" element={<Teachers />} />
        <Route path="/frequencia" element={<Attendance />} />
        <Route path="/notas" element={<Grades />} />
        <Route path="/ocorrencias" element={<Occurrences />} />
        <Route path="/comunicados" element={<Announcements />} />
      </Route>
    </Routes>
  );
}
