import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext.jsx";

export default function Login() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const [email, setEmail] = useState("demo@agroprofit.ai");
  const [password, setPassword] = useState("agro123");
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e) {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      await login(email, password);
      navigate("/");
    } catch (err) {
      setError(err.message || "Falha ao autenticar");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="login-page">
      <form className="login-card" onSubmit={handleSubmit}>
        <div className="brand" style={{ marginBottom: 24 }}>
          <span className="brand-mark">AP</span>
          <div>
            <div className="brand-name">Agro Profit AI</div>
            <div className="brand-tagline">motor de decisão econômica geoespacial</div>
          </div>
        </div>
        <label>
          E-mail
          <input type="email" value={email} onChange={(e) => setEmail(e.target.value)} required />
        </label>
        <div style={{ height: 12 }} />
        <label>
          Senha
          <input type="password" value={password} onChange={(e) => setPassword(e.target.value)} required />
        </label>
        {error && <div className="login-error">{error}</div>}
        <button className="btn-primary" type="submit" disabled={loading} style={{ width: "100%", marginTop: 20 }}>
          {loading ? "Entrando..." : "Entrar"}
        </button>
        <p className="muted" style={{ fontSize: 12, marginTop: 16 }}>
          Ambiente de demonstração pré-carregado: demo@agroprofit.ai / agro123
        </p>
      </form>
    </div>
  );
}
