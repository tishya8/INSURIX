import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

function LoginPage() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const [email, setEmail]       = useState("");
  const [password, setPassword] = useState("");
  const [error, setError]       = useState("");
  const [loading, setLoading]   = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    if (!email.trim() || !password) {
      setError("Please enter your email and password.");
      return;
    }
    setLoading(true);
    try {
      await login(email.trim(), password);
      navigate("/");
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={s.page}>
      <div style={s.left}>
        <div style={s.leftInner}>
          <ShieldIcon />
          <h1 style={s.heroTitle}>Insurance,<br />simplified.</h1>
          <p style={s.heroSub}>
            Manage your policies, file claims, and get instant answers
            from your policy documents — all in one place.
          </p>
          <div style={s.pillRow}>
            {["AI Policy Assistant", "Instant Claims", "Real-time Status"].map(t => (
              <span key={t} style={s.pill}>{t}</span>
            ))}
          </div>
        </div>
      </div>

      <div style={s.right}>
        <div style={s.card}>
          <div style={s.cardBrand}>
            <ShieldIconSmall />
            <span style={s.brandName}>INSURIX</span>
          </div>

          <h2 style={s.cardTitle}>Welcome back</h2>
          <p style={s.cardSub}>Sign in to your account</p>

          <form onSubmit={handleSubmit}>
            <div style={s.field}>
              <label style={s.label}>Email address</label>
              <input
                type="email"
                value={email}
                onChange={e => setEmail(e.target.value)}
                placeholder="you@example.com"
                style={s.input}
                autoFocus
              />
            </div>

            <div style={s.field}>
              <label style={s.label}>Password</label>
              <input
                type="password"
                value={password}
                onChange={e => setPassword(e.target.value)}
                placeholder="••••••••"
                style={s.input}
              />
            </div>

            {error && <div style={s.error}>{error}</div>}

            <button
              type="submit"
              disabled={loading}
              style={{ ...s.btn, opacity: loading ? 0.7 : 1 }}
            >
              {loading ? "Signing in…" : "Sign in"}
            </button>
          </form>
        </div>
      </div>
    </div>
  );
}

function ShieldIcon() {
  return (
    <svg width="48" height="48" viewBox="0 0 28 28" fill="none" style={{ marginBottom: 24 }}>
      <path d="M14 2L4 6.5V14c0 5.25 4.2 9.8 10 11 5.8-1.2 10-5.75 10-11V6.5L14 2Z" fill="#10B981" fillOpacity="0.9"/>
      <path d="M10 14l3 3 5-6" stroke="#fff" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round"/>
    </svg>
  );
}

function ShieldIconSmall() {
  return (
    <svg width="22" height="22" viewBox="0 0 28 28" fill="none">
      <path d="M14 2L4 6.5V14c0 5.25 4.2 9.8 10 11 5.8-1.2 10-5.75 10-11V6.5L14 2Z" fill="#10B981"/>
      <path d="M10 14l3 3 5-6" stroke="#fff" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round"/>
    </svg>
  );
}

const s = {
  page: {
    display: "flex",
    minHeight: "100vh",
    fontFamily: "Inter, -apple-system, sans-serif",
  },
  left: {
    flex: 1,
    background: "#0F172A",
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    padding: "60px 48px",
  },
  leftInner: { maxWidth: 400 },
  heroTitle: {
    fontSize: "42px",
    fontWeight: 800,
    color: "#F1F5F9",
    lineHeight: 1.15,
    letterSpacing: "-1px",
    marginBottom: 16,
  },
  heroSub: {
    fontSize: "16px",
    color: "#94A3B8",
    lineHeight: 1.7,
    marginBottom: 32,
  },
  pillRow: { display: "flex", flexWrap: "wrap", gap: 8 },
  pill: {
    padding: "5px 14px",
    background: "#1E293B",
    border: "1px solid #334155",
    borderRadius: 20,
    fontSize: 12,
    color: "#10B981",
    fontWeight: 500,
  },
  right: {
    width: 440,
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    padding: "40px 32px",
    background: "#F7F8FA",
  },
  card: {
    background: "#fff",
    border: "1px solid #E5E7EB",
    borderRadius: 16,
    padding: "36px 32px",
    width: "100%",
    boxShadow: "0 4px 20px rgba(0,0,0,0.07)",
  },
  cardBrand: { display: "flex", alignItems: "center", gap: 8, marginBottom: 28 },
  brandName: { fontSize: 16, fontWeight: 700, color: "#0F172A", letterSpacing: "0.5px" },
  cardTitle: { fontSize: 22, fontWeight: 700, color: "#111827", marginBottom: 4 },
  cardSub:   { fontSize: 14, color: "#6B7280", marginBottom: 24 },
  field:     { marginBottom: 16 },
  label:     { display: "block", fontSize: 13, fontWeight: 500, color: "#374151", marginBottom: 6 },
  input: {
    width: "100%",
    padding: "10px 12px",
    border: "1px solid #D1D5DB",
    borderRadius: 8,
    fontSize: 14,
    color: "#111827",
    background: "#F9FAFB",
    outline: "none",
    boxSizing: "border-box",
    fontFamily: "inherit",
  },
  error: {
    background: "#FEE2E2",
    border: "1px solid #FECACA",
    color: "#991B1B",
    borderRadius: 8,
    padding: "10px 12px",
    fontSize: 13,
    marginBottom: 14,
  },
  btn: {
    width: "100%",
    padding: "11px",
    background: "#10B981",
    color: "#fff",
    border: "none",
    borderRadius: 8,
    fontSize: 15,
    fontWeight: 600,
    cursor: "pointer",
    marginTop: 4,
    fontFamily: "inherit",
  },
};

export default LoginPage;