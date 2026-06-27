import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

function LoginPage() {
  const { login } = useAuth();
  const navigate = useNavigate();

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

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
    <div style={styles.page}>
      <div style={styles.card}>

        {/* Brand */}
        <div style={styles.brand}>
          <svg width="32" height="32" viewBox="0 0 28 28" fill="none">
            <path
              d="M14 2L4 6.5V14c0 5.25 4.2 9.8 10 11 5.8-1.2 10-5.75 10-11V6.5L14 2Z"
              fill="#1D9E75"
            />
            <path
              d="M10 14l3 3 5-6"
              stroke="#fff"
              strokeWidth="1.8"
              strokeLinecap="round"
              strokeLinejoin="round"
            />
          </svg>
          <span style={styles.brandName}>INSURIX</span>
        </div>

        <p style={styles.tagline}>Sign in to your account</p>

        <form onSubmit={handleSubmit} style={styles.form}>
          <div style={styles.field}>
            <label style={styles.label}>Email</label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="you@example.com"
              style={styles.input}
              autoComplete="email"
              autoFocus
            />
          </div>

          <div style={styles.field}>
            <label style={styles.label}>Password</label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="••••••••"
              style={styles.input}
              autoComplete="current-password"
            />
          </div>

          {error && <p style={styles.error}>{error}</p>}

          <button
            type="submit"
            disabled={loading}
            style={{
              ...styles.btn,
              opacity: loading ? 0.7 : 1,
              cursor: loading ? "not-allowed" : "pointer",
            }}
          >
            {loading ? "Signing in…" : "Sign in"}
          </button>
        </form>
      </div>
    </div>
  );
}

const styles = {
  page: {
    minHeight: "100vh",
    background: "#111827",
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    fontFamily: "-apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif",
  },
  card: {
    background: "#1f2937",
    borderRadius: "14px",
    padding: "40px 36px",
    width: "100%",
    maxWidth: "380px",
    border: "1px solid #374151",
  },
  brand: {
    display: "flex",
    alignItems: "center",
    gap: "10px",
    marginBottom: "6px",
  },
  brandName: {
    fontSize: "22px",
    fontWeight: "700",
    color: "#ffffff",
    letterSpacing: "1px",
  },
  tagline: {
    fontSize: "14px",
    color: "#9ca3af",
    marginBottom: "28px",
  },
  form: {
    display: "flex",
    flexDirection: "column",
    gap: "16px",
  },
  field: {
    display: "flex",
    flexDirection: "column",
    gap: "6px",
  },
  label: {
    fontSize: "13px",
    fontWeight: "500",
    color: "#d1d5db",
  },
  input: {
    padding: "10px 12px",
    background: "#374151",
    border: "1px solid #4b5563",
    borderRadius: "8px",
    color: "#f9fafb",
    fontSize: "14px",
    outline: "none",
    transition: "border-color 0.15s",
  },
  error: {
    fontSize: "13px",
    color: "#f87171",
    background: "#450a0a",
    border: "1px solid #7f1d1d",
    borderRadius: "8px",
    padding: "10px 12px",
    margin: "0",
  },
  btn: {
    padding: "11px",
    background: "#1D9E75",
    color: "#fff",
    border: "none",
    borderRadius: "8px",
    fontSize: "15px",
    fontWeight: "600",
    marginTop: "4px",
    transition: "background 0.15s",
  },
};

export default LoginPage;