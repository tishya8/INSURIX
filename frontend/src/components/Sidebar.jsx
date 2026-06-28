import { Link, useLocation, useNavigate } from "react-router-dom";
import { useContext } from "react";
import { PolicyContext } from "./PolicyContext";
import { useAuth } from "../context/AuthContext";

const NAV_ITEMS = [
  { path: "/",         label: "Policy Assistant", icon: "💬" },
  { path: "/policies", label: "My Policies",      icon: "📋" },
  { path: "/claims",   label: "Claims",           icon: "📝" },
];

export default function Sidebar() {
  const { user, logout }                             = useAuth();
  const { policies, policyId, setPolicyId,
          loadingPolicies, policiesError }            = useContext(PolicyContext);
  const location = useLocation();
  const navigate = useNavigate();

  const handleLogout = () => { logout(); navigate("/login"); };

  const initials = user?.name
    ? user.name.split(" ").map(w => w[0]).slice(0, 2).join("").toUpperCase()
    : "?";

  return (
    <aside style={s.sidebar}>

      {/* Brand */}
      <div style={s.brand}>
        <ShieldSVG />
        <span style={s.brandName}>INSURIX</span>
      </div>

      {/* Navigation */}
      <div style={s.section}>
        <p style={s.sectionLabel}>Menu</p>
        {NAV_ITEMS.map(item => {
          const active = location.pathname === item.path;
          return (
            <Link key={item.path} to={item.path} style={{ textDecoration: "none" }}>
              <div style={{ ...s.navItem, ...(active ? s.navItemActive : {}) }}>
                <span style={s.navIcon}>{item.icon}</span>
                <span style={active ? s.navLabelActive : s.navLabel}>{item.label}</span>
                {active && <div style={s.activeDot} />}
              </div>
            </Link>
          );
        })}
      </div>

      <div style={s.divider} />

      {/* Policies */}
      <div style={s.section}>
        <p style={s.sectionLabel}>Your Policies</p>

        {loadingPolicies && (
          <div style={s.skeletonWrap}>
            <div style={s.skeleton} />
            <div style={{ ...s.skeleton, opacity: 0.5 }} />
          </div>
        )}

        {!loadingPolicies && policiesError && (
          <p style={s.errorTxt}>{policiesError}</p>
        )}

        {!loadingPolicies && !policiesError && policies.length === 0 && (
          <p style={s.mutedTxt}>No policies found.</p>
        )}

        {!loadingPolicies && policies.map(p => {
          const active = String(p.policy_id) === policyId;
          return (
            <button
              key={p.policy_id}
              onClick={() => setPolicyId(String(p.policy_id))}
              style={{ ...s.policyBtn, ...(active ? s.policyBtnActive : {}) }}
            >
              <div style={s.policyTop}>
                <span style={s.policyNum}>{p.policy_number}</span>
                <span style={{
                  ...s.statusDot,
                  background: p.status === "ACTIVE" ? "#4CAF82" : "#6B7280"
                }} />
              </div>
              <div style={active ? s.policyModelActive : s.policyModel}>
                {p.vehicle_model}
              </div>
              <div style={s.policyReg}>{p.vehicle_number}</div>
            </button>
          );
        })}
      </div>

      {/* User footer */}
      <div style={s.userFooter}>
        <div style={s.avatar}>{initials}</div>
        <div style={s.userInfo}>
          <div style={s.userName}>{user?.name || "User"}</div>
          <div style={s.userEmail}>{user?.email}</div>
        </div>
        <button onClick={handleLogout} style={s.logoutBtn} title="Sign out">
          ↪
        </button>
      </div>
    </aside>
  );
}

function ShieldSVG() {
  return (
    <svg width="22" height="22" viewBox="0 0 28 28" fill="none">
      <path d="M14 2L4 6.5V14c0 5.25 4.2 9.8 10 11 5.8-1.2 10-5.75 10-11V6.5L14 2Z" fill="#4A9EE0"/>
      <path d="M10 14l3 3 5-6" stroke="#fff" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round"/>
    </svg>
  );
}

const s = {
  sidebar: {
    width: 256, minHeight: "100vh",
    background: "#001F5B",
    display: "flex", flexDirection: "column",
    padding: "18px 12px",
    position: "sticky", top: 0,
    fontFamily: "-apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif",
  },
  brand: {
    display: "flex", alignItems: "center", gap: 9,
    padding: "6px 10px 20px",
  },
  brandName: {
    fontSize: 15, fontWeight: 800,
    color: "#FFFFFF", letterSpacing: "1.5px",
  },
  section: { marginBottom: 4 },
  sectionLabel: {
    fontSize: 10, fontWeight: 700,
    color: "#3B5998", textTransform: "uppercase",
    letterSpacing: "1.2px", padding: "0 10px", marginBottom: 4,
  },
  navItem: {
    display: "flex", alignItems: "center", gap: 10,
    padding: "9px 10px", borderRadius: 8,
    cursor: "pointer", position: "relative",
    transition: "background 0.15s",
    marginBottom: 2,
  },
  navItemActive: { background: "#0A3080" },
  navIcon:       { fontSize: 15, width: 20, textAlign: "center" },
  navLabel:      { fontSize: 13, color: "#7A9CC8", fontWeight: 400 },
  navLabelActive:{ fontSize: 13, color: "#FFFFFF", fontWeight: 600 },
  activeDot: {
    marginLeft: "auto", width: 6, height: 6,
    borderRadius: "50%", background: "#4A9EE0",
  },
  divider: { borderTop: "1px solid #0A2A6E", margin: "12px 0" },
  skeletonWrap: { display: "flex", flexDirection: "column", gap: 8, padding: "0 4px" },
  skeleton: {
    height: 58, borderRadius: 8,
    background: "#0A2A6E",
    animation: "pulse 1.5s ease-in-out infinite",
  },
  mutedTxt:  { fontSize: 12, color: "#3B5998", padding: "6px 10px" },
  errorTxt:  { fontSize: 12, color: "#FCA5A5", padding: "6px 10px" },
  policyBtn: {
    width: "100%", background: "transparent",
    border: "1px solid transparent",
    borderRadius: 8, padding: "10px 10px",
    cursor: "pointer", textAlign: "left",
    fontFamily: "inherit", marginBottom: 4,
    transition: "all 0.15s",
  },
  policyBtnActive: { background: "#0A3080", border: "1px solid #1A4DB8" },
  policyTop:  { display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 2 },
  policyNum:  { fontSize: 10, color: "#4A9EE0", fontWeight: 700, letterSpacing: "0.5px", textTransform: "uppercase" },
  statusDot:  { width: 6, height: 6, borderRadius: "50%" },
  policyModel:      { fontSize: 13, color: "#5C7AA8", fontWeight: 500 },
  policyModelActive:{ fontSize: 13, color: "#FFFFFF", fontWeight: 600 },
  policyReg:  { fontSize: 11, color: "#3B5998", marginTop: 2 },
  userFooter: {
    marginTop: "auto",
    display: "flex", alignItems: "center", gap: 10,
    padding: "12px 8px", borderTop: "1px solid #0A2A6E",
  },
  avatar: {
    width: 32, height: 32, borderRadius: "50%",
    background: "#0057A8", color: "#fff",
    fontSize: 12, fontWeight: 700,
    display: "flex", alignItems: "center", justifyContent: "center",
    flexShrink: 0,
  },
  userInfo:  { flex: 1, overflow: "hidden" },
  userName:  { fontSize: 12, fontWeight: 600, color: "#E2EAF8", whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" },
  userEmail: { fontSize: 10, color: "#3B5998", whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" },
  logoutBtn: {
    background: "none", border: "none",
    color: "#3B5998", fontSize: 16,
    cursor: "pointer", padding: 4,
    borderRadius: 6, flexShrink: 0,
  },
};

// import { Link } from "react-router-dom";
// import { useContext, useEffect, useState } from "react";
// import { useNavigate } from "react-router-dom";

// import { PolicyContext } from "../components/PolicyContext";
// import { useAuth } from "../context/AuthContext";
// import PolicyCard from "./PolicyCard";

// function Sidebar() {
//   const { policyId, setPolicyId } = useContext(PolicyContext);
//   const { user, logout } = useAuth();
//   const navigate = useNavigate();

//   const [policies, setPolicies] = useState([]);
//   const [loadingPolicies, setLoadingPolicies] = useState(true);
//   const [policiesError, setPoliciesError] = useState("");

//   // Fetch this user's policies from the backend
//   useEffect(() => {
//     if (!user?.user_id) return;

//     setLoadingPolicies(true);
//     setPoliciesError("");

//     fetch(`http://localhost:8000/users/${user.user_id}/policies`)
//       .then((res) => {
//         if (!res.ok) throw new Error("Failed to load policies");
//         return res.json();
//       })
//       .then((data) => {
//         setPolicies(data);
//         // Auto-select the first active policy
//         const first = data.find((p) => p.status === "ACTIVE");
//         if (first) setPolicyId(String(first.policy_id));
//       })
//       .catch((err) => setPoliciesError(err.message))
//       .finally(() => setLoadingPolicies(false));
//   }, [user?.user_id]);

//   const handleLogout = () => {
//     logout();
//     navigate("/login");
//   };

//   return (
//     <div style={styles.sidebar}>

//       {/* Brand */}
//       <h2 style={styles.brand}>INSURIX</h2>

//       {/* User session */}
//       <div style={styles.session}>
//         <div style={styles.sessionLabel}>Signed in as</div>
//         <div style={styles.sessionName}>{user?.name || user?.email}</div>
//         <button onClick={handleLogout} style={styles.logoutBtn}>
//           Sign out
//         </button>
//       </div>

//       {/* Policies */}
//       <h4 style={styles.sectionTitle}>Policies</h4>

//       {loadingPolicies && (
//         <p style={styles.muted}>Loading policies…</p>
//       )}

//       {policiesError && (
//         <p style={styles.errorText}>{policiesError}</p>
//       )}

//       {!loadingPolicies && !policiesError && policies.length === 0 && (
//         <p style={styles.muted}>No policies found.</p>
//       )}

//       {policies.map((p) => (
//         <PolicyCard
//           key={p.policy_id}
//           policyId={p.policy_number}
//           title={p.vehicle_model}
//           selected={policyId === String(p.policy_id)}
//           onClick={() => setPolicyId(String(p.policy_id))}
//         />
//       ))}

//       <hr style={styles.divider} />

//       {/* Navigation */}
//       <ul style={styles.nav}>
//         <li style={styles.navItem}>
//           <Link to="/" style={styles.navLink}>Policy Assistant</Link>
//         </li>
//         <li style={styles.navItem}>
//           <Link to="/claims" style={styles.navLink}>Claims</Link>
//         </li>
//         <li style={styles.navItem}>
//           <Link to="/policies" style={styles.navLink}>Policies</Link>
//         </li>
//       </ul>

//     </div>
//   );
// }

// const styles = {
//   sidebar: {
//     width: "280px",
//     background: "#1f2937",
//     color: "white",
//     padding: "20px",
//     minHeight: "100vh",
//     position: "sticky",
//     top: 0,
//     display: "flex",
//     flexDirection: "column",
//   },
//   brand: {
//     marginBottom: "20px",
//     fontSize: "20px",
//     letterSpacing: "1px",
//   },
//   session: {
//     marginBottom: "25px",
//     padding: "12px",
//     background: "#374151",
//     borderRadius: "10px",
//   },
//   sessionLabel: {
//     fontSize: "11px",
//     color: "#9ca3af",
//     marginBottom: "3px",
//   },
//   sessionName: {
//     fontWeight: "600",
//     fontSize: "14px",
//     marginBottom: "10px",
//     wordBreak: "break-all",
//   },
//   logoutBtn: {
//     background: "none",
//     border: "1px solid #4b5563",
//     color: "#d1d5db",
//     padding: "4px 10px",
//     borderRadius: "6px",
//     fontSize: "12px",
//     cursor: "pointer",
//   },
//   sectionTitle: {
//     marginBottom: "10px",
//     color: "#9ca3af",
//     fontSize: "12px",
//     textTransform: "uppercase",
//     letterSpacing: "0.5px",
//   },
//   muted: {
//     fontSize: "13px",
//     color: "#6b7280",
//     padding: "8px 0",
//   },
//   errorText: {
//     fontSize: "12px",
//     color: "#f87171",
//     padding: "8px 0",
//   },
//   divider: {
//     margin: "20px 0",
//     borderColor: "#374151",
//   },
//   nav: {
//     listStyle: "none",
//     padding: 0,
//   },
//   navItem: {
//     marginBottom: "15px",
//   },
//   navLink: {
//     color: "white",
//     textDecoration: "none",
//     fontSize: "14px",
//   },
// };

// export default Sidebar;