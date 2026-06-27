import { Link } from "react-router-dom";
import { useContext, useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";

import { PolicyContext } from "../components/PolicyContext";
import { useAuth } from "../context/AuthContext";
import PolicyCard from "./PolicyCard";

function Sidebar() {
  const { policyId, setPolicyId } = useContext(PolicyContext);
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const [policies, setPolicies] = useState([]);
  const [loadingPolicies, setLoadingPolicies] = useState(true);
  const [policiesError, setPoliciesError] = useState("");

  // Fetch this user's policies from the backend
  useEffect(() => {
    if (!user?.user_id) return;

    setLoadingPolicies(true);
    setPoliciesError("");

    fetch(`http://localhost:8000/users/${user.user_id}/policies`)
      .then((res) => {
        if (!res.ok) throw new Error("Failed to load policies");
        return res.json();
      })
      .then((data) => {
        setPolicies(data);
        // Auto-select the first active policy
        const first = data.find((p) => p.status === "ACTIVE");
        if (first) setPolicyId(String(first.policy_id));
      })
      .catch((err) => setPoliciesError(err.message))
      .finally(() => setLoadingPolicies(false));
  }, [user?.user_id]);

  const handleLogout = () => {
    logout();
    navigate("/login");
  };

  return (
    <div style={styles.sidebar}>

      {/* Brand */}
      <h2 style={styles.brand}>INSURIX</h2>

      {/* User session */}
      <div style={styles.session}>
        <div style={styles.sessionLabel}>Signed in as</div>
        <div style={styles.sessionName}>{user?.name || user?.email}</div>
        <button onClick={handleLogout} style={styles.logoutBtn}>
          Sign out
        </button>
      </div>

      {/* Policies */}
      <h4 style={styles.sectionTitle}>Policies</h4>

      {loadingPolicies && (
        <p style={styles.muted}>Loading policies…</p>
      )}

      {policiesError && (
        <p style={styles.errorText}>{policiesError}</p>
      )}

      {!loadingPolicies && !policiesError && policies.length === 0 && (
        <p style={styles.muted}>No policies found.</p>
      )}

      {policies.map((p) => (
        <PolicyCard
          key={p.policy_id}
          policyId={p.policy_number}
          title={p.vehicle_model}
          selected={policyId === String(p.policy_id)}
          onClick={() => setPolicyId(String(p.policy_id))}
        />
      ))}

      <hr style={styles.divider} />

      {/* Navigation */}
      <ul style={styles.nav}>
        <li style={styles.navItem}>
          <Link to="/" style={styles.navLink}>Policy Assistant</Link>
        </li>
        <li style={styles.navItem}>
          <Link to="/claims" style={styles.navLink}>Claims</Link>
        </li>
        <li style={styles.navItem}>
          <Link to="/policies" style={styles.navLink}>Policies</Link>
        </li>
      </ul>

    </div>
  );
}

const styles = {
  sidebar: {
    width: "280px",
    background: "#1f2937",
    color: "white",
    padding: "20px",
    minHeight: "100vh",
    position: "sticky",
    top: 0,
    display: "flex",
    flexDirection: "column",
  },
  brand: {
    marginBottom: "20px",
    fontSize: "20px",
    letterSpacing: "1px",
  },
  session: {
    marginBottom: "25px",
    padding: "12px",
    background: "#374151",
    borderRadius: "10px",
  },
  sessionLabel: {
    fontSize: "11px",
    color: "#9ca3af",
    marginBottom: "3px",
  },
  sessionName: {
    fontWeight: "600",
    fontSize: "14px",
    marginBottom: "10px",
    wordBreak: "break-all",
  },
  logoutBtn: {
    background: "none",
    border: "1px solid #4b5563",
    color: "#d1d5db",
    padding: "4px 10px",
    borderRadius: "6px",
    fontSize: "12px",
    cursor: "pointer",
  },
  sectionTitle: {
    marginBottom: "10px",
    color: "#9ca3af",
    fontSize: "12px",
    textTransform: "uppercase",
    letterSpacing: "0.5px",
  },
  muted: {
    fontSize: "13px",
    color: "#6b7280",
    padding: "8px 0",
  },
  errorText: {
    fontSize: "12px",
    color: "#f87171",
    padding: "8px 0",
  },
  divider: {
    margin: "20px 0",
    borderColor: "#374151",
  },
  nav: {
    listStyle: "none",
    padding: 0,
  },
  navItem: {
    marginBottom: "15px",
  },
  navLink: {
    color: "white",
    textDecoration: "none",
    fontSize: "14px",
  },
};

export default Sidebar;