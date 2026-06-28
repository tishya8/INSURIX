import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

// Insurance color palette
const C = {
  navy:       "#001F5B",
  blue:       "#0057A8",
  blueMid:    "#0066CC",
  blueLight:  "#E8F0FB",
  white:      "#FFFFFF",
  textDark:   "#1A1A2E",
  textMid:    "#4A5568",
  textLight:  "#718096",
  border:     "#CBD5E0",
  red:        "#C53030",
  redLight:   "#FFF5F5",
  redBorder:  "#FEB2B2",
};

export default function LoginPage() {
  const { login } = useAuth();
  const navigate  = useNavigate();

  const [email,    setEmail]    = useState("");
  const [password, setPassword] = useState("");
  const [error,    setError]    = useState("");
  const [loading,  setLoading]  = useState(false);

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

      {/* Left panel — brand hero */}
      <div style={s.left}>
        <div style={s.leftContent}>
          <div style={s.logoRow}>
            <ShieldSVG size={44} />
            <span style={s.logoText}>INSURIX</span>
          </div>

          <h1 style={s.heroTitle}>
            Protection you can<br />count on.
          </h1>

          <p style={s.heroSub}>
            Manage your policies, file claims, and get instant
            AI-powered answers from your policy documents.
          </p>

          <div style={s.pills}>
            {["AI Policy Assistant", "Instant Claims", "Real-time Tracking"].map(t => (
              <span key={t} style={s.pill}>{t}</span>
            ))}
          </div>

          <div style={s.divider} />

          <p style={s.footerNote}>
            Powered by Insurance
          </p>
        </div>
      </div>

      {/* Right panel — login form */}
      <div style={s.right}>
        <div style={s.card}>
          <div style={s.cardLogoRow}>
            <ShieldSVG size={28} />
            <span style={s.cardLogoText}>INSURIX</span>
          </div>

          <h2 style={s.cardTitle}>Welcome back</h2>
          <p style={s.cardSub}>Sign in to access your policies</p>

          <form onSubmit={handleSubmit} noValidate>
            <div style={s.field}>
              <label style={s.label} htmlFor="email">Email address</label>
              <input
                id="email"
                type="email"
                value={email}
                onChange={e => setEmail(e.target.value)}
                placeholder="you@example.com"
                autoComplete="email"
                autoFocus
                style={s.input}
              />
            </div>

            <div style={s.field}>
              <label style={s.label} htmlFor="password">Password</label>
              <input
                id="password"
                type="password"
                value={password}
                onChange={e => setPassword(e.target.value)}
                placeholder="••••••••"
                autoComplete="current-password"
                style={s.input}
              />
            </div>

            {error && (
              <div style={s.errorBox} role="alert">
                {error}
              </div>
            )}

            <button
              type="submit"
              disabled={loading}
              style={{ ...s.btn, opacity: loading ? 0.75 : 1 }}
            >
              {loading ? "Signing in…" : "Sign in"}
            </button>
          </form>
        </div>
      </div>
    </div>
  );
}

function ShieldSVG({ size = 32 }) {
  return (
    <svg width={size} height={size} viewBox="0 0 28 28" fill="none">
      <path
        d="M14 2L4 6.5V14c0 5.25 4.2 9.8 10 11 5.8-1.2 10-5.75 10-11V6.5L14 2Z"
        fill={C.blue}
      />
      <path
        d="M10 14l3 3 5-6"
        stroke="#fff"
        strokeWidth="1.8"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
}

const s = {
  page: {
    display: "flex",
    minHeight: "100vh",
    fontFamily: "-apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif",
  },

  /* Left */
  left: {
    flex: 1,
    background: C.navy,
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    padding: "60px 48px",
  },
  leftContent: { maxWidth: 420 },
  logoRow: { display: "flex", alignItems: "center", gap: 10, marginBottom: 36 },
  logoText: {
    fontSize: 22, fontWeight: 800,
    color: C.white, letterSpacing: "1.5px",
  },
  heroTitle: {
    fontSize: 40, fontWeight: 800,
    color: C.white, lineHeight: 1.2,
    letterSpacing: "-0.5px", marginBottom: 16,
  },
  heroSub: {
    fontSize: 15, color: "#A0B4D6",
    lineHeight: 1.75, marginBottom: 28,
  },
  pills: { display: "flex", flexWrap: "wrap", gap: 8, marginBottom: 36 },
  pill: {
    padding: "5px 14px",
    background: "rgba(255,255,255,0.08)",
    border: "1px solid rgba(255,255,255,0.15)",
    borderRadius: 20, fontSize: 12,
    color: "#90CAF9", fontWeight: 500,
  },
  divider: { borderTop: "1px solid rgba(255,255,255,0.1)", marginBottom: 20 },
  footerNote: { fontSize: 12, color: "#5C7AA8" },

  /* Right */
  right: {
    width: 460,
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    padding: "40px 32px",
    background: "#F4F6FA",
  },
  card: {
    width: "100%",
    background: C.white,
    border: "1px solid #DDE3EF",
    borderRadius: 14,
    padding: "36px 32px",
    boxShadow: "0 4px 24px rgba(0,31,91,0.08)",
  },
  cardLogoRow: {
    display: "flex", alignItems: "center", gap: 8, marginBottom: 24,
  },
  cardLogoText: {
    fontSize: 15, fontWeight: 700,
    color: C.navy, letterSpacing: "0.5px",
  },
  cardTitle: {
    fontSize: 22, fontWeight: 700,
    color: C.textDark, marginBottom: 4,
  },
  cardSub: {
    fontSize: 14, color: C.textLight, marginBottom: 24,
  },
  field: { marginBottom: 16 },
  label: {
    display: "block", fontSize: 13,
    fontWeight: 600, color: C.textMid,
    marginBottom: 6,
  },
  input: {
    width: "100%", padding: "10px 12px",
    border: `1px solid ${C.border}`,
    borderRadius: 8, fontSize: 14,
    color: C.textDark, background: "#FAFBFD",
    outline: "none", fontFamily: "inherit",
    boxSizing: "border-box",
    transition: "border-color 0.15s",
  },
  errorBox: {
    background: C.redLight,
    border: `1px solid ${C.redBorder}`,
    color: C.red,
    borderRadius: 8, padding: "10px 12px",
    fontSize: 13, marginBottom: 14,
  },
  btn: {
    width: "100%", padding: "11px",
    background: C.blue, color: C.white,
    border: "none", borderRadius: 8,
    fontSize: 15, fontWeight: 600,
    cursor: "pointer", fontFamily: "inherit",
    marginTop: 4,
    transition: "background 0.15s",
  },
};






// import { useState } from "react";
// import { useNavigate } from "react-router-dom";
// import { useAuth } from "../context/AuthContext";

// function LoginPage() {
//   const { login } = useAuth();
//   const navigate = useNavigate();
//   const [email, setEmail]       = useState("");
//   const [password, setPassword] = useState("");
//   const [error, setError]       = useState("");
//   const [loading, setLoading]   = useState(false);

//   const handleSubmit = async (e) => {
//     e.preventDefault();
//     setError("");
//     if (!email.trim() || !password) {
//       setError("Please enter your email and password.");
//       return;
//     }
//     setLoading(true);
//     try {
//       await login(email.trim(), password);
//       navigate("/");
//     } catch (err) {
//       setError(err.message);
//     } finally {
//       setLoading(false);
//     }
//   };

//   return (
//     <div style={s.page}>
//       <div style={s.left}>
//         <div style={s.leftInner}>
//           <ShieldIcon />
//           <h1 style={s.heroTitle}>Insurance,<br />simplified.</h1>
//           <p style={s.heroSub}>
//             Manage your policies, file claims, and get instant answers
//             from your policy documents — all in one place.
//           </p>
//           <div style={s.pillRow}>
//             {["AI Policy Assistant", "Instant Claims", "Real-time Status"].map(t => (
//               <span key={t} style={s.pill}>{t}</span>
//             ))}
//           </div>
//         </div>
//       </div>

//       <div style={s.right}>
//         <div style={s.card}>
//           <div style={s.cardBrand}>
//             <ShieldIconSmall />
//             <span style={s.brandName}>INSURIX</span>
//           </div>

//           <h2 style={s.cardTitle}>Welcome back</h2>
//           <p style={s.cardSub}>Sign in to your account</p>

//           <form onSubmit={handleSubmit}>
//             <div style={s.field}>
//               <label style={s.label}>Email address</label>
//               <input
//                 type="email"
//                 value={email}
//                 onChange={e => setEmail(e.target.value)}
//                 placeholder="you@example.com"
//                 style={s.input}
//                 autoFocus
//               />
//             </div>

//             <div style={s.field}>
//               <label style={s.label}>Password</label>
//               <input
//                 type="password"
//                 value={password}
//                 onChange={e => setPassword(e.target.value)}
//                 placeholder="••••••••"
//                 style={s.input}
//               />
//             </div>

//             {error && <div style={s.error}>{error}</div>}

//             <button
//               type="submit"
//               disabled={loading}
//               style={{ ...s.btn, opacity: loading ? 0.7 : 1 }}
//             >
//               {loading ? "Signing in…" : "Sign in"}
//             </button>
//           </form>
//         </div>
//       </div>
//     </div>
//   );
// }

// function ShieldIcon() {
//   return (
//     <svg width="48" height="48" viewBox="0 0 28 28" fill="none" style={{ marginBottom: 24 }}>
//       <path d="M14 2L4 6.5V14c0 5.25 4.2 9.8 10 11 5.8-1.2 10-5.75 10-11V6.5L14 2Z" fill="#10B981" fillOpacity="0.9"/>
//       <path d="M10 14l3 3 5-6" stroke="#fff" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round"/>
//     </svg>
//   );
// }

// function ShieldIconSmall() {
//   return (
//     <svg width="22" height="22" viewBox="0 0 28 28" fill="none">
//       <path d="M14 2L4 6.5V14c0 5.25 4.2 9.8 10 11 5.8-1.2 10-5.75 10-11V6.5L14 2Z" fill="#10B981"/>
//       <path d="M10 14l3 3 5-6" stroke="#fff" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round"/>
//     </svg>
//   );
// }

// const s = {
//   page: {
//     display: "flex",
//     minHeight: "100vh",
//     fontFamily: "Inter, -apple-system, sans-serif",
//   },
//   left: {
//     flex: 1,
//     background: "#0F172A",
//     display: "flex",
//     alignItems: "center",
//     justifyContent: "center",
//     padding: "60px 48px",
//   },
//   leftInner: { maxWidth: 400 },
//   heroTitle: {
//     fontSize: "42px",
//     fontWeight: 800,
//     color: "#F1F5F9",
//     lineHeight: 1.15,
//     letterSpacing: "-1px",
//     marginBottom: 16,
//   },
//   heroSub: {
//     fontSize: "16px",
//     color: "#94A3B8",
//     lineHeight: 1.7,
//     marginBottom: 32,
//   },
//   pillRow: { display: "flex", flexWrap: "wrap", gap: 8 },
//   pill: {
//     padding: "5px 14px",
//     background: "#1E293B",
//     border: "1px solid #334155",
//     borderRadius: 20,
//     fontSize: 12,
//     color: "#10B981",
//     fontWeight: 500,
//   },
//   right: {
//     width: 440,
//     display: "flex",
//     alignItems: "center",
//     justifyContent: "center",
//     padding: "40px 32px",
//     background: "#F7F8FA",
//   },
//   card: {
//     background: "#fff",
//     border: "1px solid #E5E7EB",
//     borderRadius: 16,
//     padding: "36px 32px",
//     width: "100%",
//     boxShadow: "0 4px 20px rgba(0,0,0,0.07)",
//   },
//   cardBrand: { display: "flex", alignItems: "center", gap: 8, marginBottom: 28 },
//   brandName: { fontSize: 16, fontWeight: 700, color: "#0F172A", letterSpacing: "0.5px" },
//   cardTitle: { fontSize: 22, fontWeight: 700, color: "#111827", marginBottom: 4 },
//   cardSub:   { fontSize: 14, color: "#6B7280", marginBottom: 24 },
//   field:     { marginBottom: 16 },
//   label:     { display: "block", fontSize: 13, fontWeight: 500, color: "#374151", marginBottom: 6 },
//   input: {
//     width: "100%",
//     padding: "10px 12px",
//     border: "1px solid #D1D5DB",
//     borderRadius: 8,
//     fontSize: 14,
//     color: "#111827",
//     background: "#F9FAFB",
//     outline: "none",
//     boxSizing: "border-box",
//     fontFamily: "inherit",
//   },
//   error: {
//     background: "#FEE2E2",
//     border: "1px solid #FECACA",
//     color: "#991B1B",
//     borderRadius: 8,
//     padding: "10px 12px",
//     fontSize: 13,
//     marginBottom: 14,
//   },
//   btn: {
//     width: "100%",
//     padding: "11px",
//     background: "#10B981",
//     color: "#fff",
//     border: "none",
//     borderRadius: 8,
//     fontSize: 15,
//     fontWeight: 600,
//     cursor: "pointer",
//     marginTop: 4,
//     fontFamily: "inherit",
//   },
// };

// export default LoginPage;