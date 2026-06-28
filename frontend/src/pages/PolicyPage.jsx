import { useContext } from "react";
import { PolicyContext } from "../components/PolicyContext";

// Allstate India colors (matches rest of app)
const C = {
  navy:      "#001F5B",
  blue:      "#0057A8",
  blueSoft:  "#E8F0FB",
  blueMid:   "#C3D3F0",
  bg:        "#F4F6FA",
  white:     "#FFFFFF",
  border:    "#DDE3EF",
  textDark:  "#1A1A2E",
  textMid:   "#4A5568",
  textLight: "#718096",
  green:     "#1A7F4B",
  greenSoft: "#DCFCE7",
  red:       "#C53030",
  redSoft:   "#FFF5F5",
  gray:      "#6B7280",
  graySoft:  "#F3F4F6",
};

const STATUS_STYLES = {
  ACTIVE:   { bg: C.greenSoft, color: C.green,  dot: "#22C55E" },
  INACTIVE: { bg: C.graySoft,  color: C.gray,   dot: "#9CA3AF" },
  EXPIRED:  { bg: C.redSoft,   color: C.red,    dot: "#EF4444" },
};

// Vehicle icon based on model name keywords
function vehicleIcon(model = "") {
  const m = model.toLowerCase();
  if (m.includes("bike") || m.includes("cb") || m.includes("royal") || m.includes("pulsar")) return "🏍️";
  return "🚗";
}

export default function PolicyPage() {
  const { policies, policyId, setPolicyId, loadingPolicies, policiesError } =
    useContext(PolicyContext);

  return (
    <div style={s.page}>

      {/* ── Header ── */}
      <div style={s.header}>
        <div>
          <h1 style={s.title}>My Policies</h1>
          <p style={s.subtitle}>
            {loadingPolicies
              ? "Loading your policies…"
              : `${policies.length} polic${policies.length === 1 ? "y" : "ies"} on your account`}
          </p>
        </div>
        {!loadingPolicies && policies.length > 0 && (
          <div style={s.summaryBadge}>
            <span style={s.summaryDot} />
            {policies.filter(p => p.status === "ACTIVE").length} Active
          </div>
        )}
      </div>

      {/* ── Loading skeletons ── */}
      {loadingPolicies && (
        <div style={s.grid}>
          {[1, 2, 3].map(i => (
            <div key={i} style={s.skeleton}>
              <div style={s.skeletonTop} />
              <div style={s.skeletonLine} />
              <div style={{ ...s.skeletonLine, width: "60%" }} />
            </div>
          ))}
        </div>
      )}

      {/* ── Error ── */}
      {!loadingPolicies && policiesError && (
        <div style={s.errorBox}>
          <span style={s.errorIcon}>⚠️</span>
          {policiesError}
        </div>
      )}

      {/* ── Empty state ── */}
      {!loadingPolicies && !policiesError && policies.length === 0 && (
        <div style={s.empty}>
          <div style={s.emptyIcon}>📋</div>
          <div style={s.emptyTitle}>No policies found</div>
          <div style={s.emptyText}>
            Contact support to link a policy to your account.
          </div>
        </div>
      )}

      {/* ── Policy grid ── */}
      {!loadingPolicies && !policiesError && policies.length > 0 && (
        <div style={s.grid}>
          {policies.map(p => {
            const selected = String(p.policy_id) === policyId;
            const sc = STATUS_STYLES[p.status] || STATUS_STYLES.INACTIVE;

            return (
              <div
                key={p.policy_id}
                onClick={() => setPolicyId(String(p.policy_id))}
                style={{
                  ...s.card,
                  ...(selected ? s.cardSelected : {}),
                }}
              >
                {/* Top row: icon + status badge */}
                <div style={s.cardTop}>
                  <span style={s.vIcon}>{vehicleIcon(p.vehicle_model)}</span>
                  <span style={{ ...s.badge, background: sc.bg, color: sc.color }}>
                    <span style={{ ...s.badgeDot, background: sc.dot }} />
                    {p.status}
                  </span>
                </div>

                {/* Vehicle details */}
                <div style={s.vehicleModel}>{p.vehicle_model}</div>
                <div style={s.vehicleReg}>{p.vehicle_number}</div>

                <div style={s.divider} />

                {/* Policy number */}
                <div style={s.detailRow}>
                  <span style={s.detailLabel}>Policy No.</span>
                  <span style={s.detailValue}>{p.policy_number}</span>
                </div>

                {/* Selected indicator */}
                {selected && (
                  <div style={s.selectedPill}>
                    ✓ Active in Policy Assistant
                  </div>
                )}

                {/* Hover CTA when not selected */}
                {!selected && p.status === "ACTIVE" && (
                  <div style={s.selectCta}>Click to select for chat →</div>
                )}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}

const s = {
  page:    { maxWidth: 920, margin: "0 auto" },
  header:  {
    display: "flex", justifyContent: "space-between",
    alignItems: "flex-start", marginBottom: 24,
  },
  title:   { fontSize: 20, fontWeight: 700, color: C.navy, letterSpacing: "-0.3px" },
  subtitle:{ fontSize: 13, color: C.textLight, marginTop: 4 },
  summaryBadge: {
    display: "flex", alignItems: "center", gap: 6,
    background: C.greenSoft, border: `1px solid #BBF7D0`,
    borderRadius: 20, padding: "5px 14px",
    fontSize: 12, color: C.green, fontWeight: 600,
  },
  summaryDot: { width: 7, height: 7, borderRadius: "50%", background: "#22C55E" },

  grid: {
    display: "grid",
    gridTemplateColumns: "repeat(auto-fill, minmax(250px, 1fr))",
    gap: 16,
  },

  card: {
    background: C.white,
    border: `1px solid ${C.border}`,
    borderRadius: 12, padding: 20,
    cursor: "pointer",
    transition: "border-color 0.15s, box-shadow 0.15s, transform 0.1s",
    boxShadow: "0 1px 4px rgba(0,31,91,0.06)",
  },
  cardSelected: {
    border: `2px solid ${C.blue}`,
    boxShadow: `0 0 0 3px rgba(0,87,168,0.1)`,
  },

  cardTop:     { display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 14 },
  vIcon:       { fontSize: 30 },
  badge: {
    display: "inline-flex", alignItems: "center", gap: 5,
    fontSize: 10, fontWeight: 700, padding: "3px 10px",
    borderRadius: 20, textTransform: "uppercase", letterSpacing: "0.5px",
  },
  badgeDot:    { width: 5, height: 5, borderRadius: "50%" },

  vehicleModel:{ fontSize: 16, fontWeight: 700, color: C.navy, marginBottom: 3 },
  vehicleReg:  { fontSize: 13, color: C.textLight, marginBottom: 14 },

  divider:     { borderTop: `1px solid ${C.border}`, marginBottom: 12 },
  detailRow:   { display: "flex", justifyContent: "space-between", alignItems: "center" },
  detailLabel: { fontSize: 11, color: C.textLight },
  detailValue: {
    fontSize: 12, fontWeight: 700, color: C.navy,
    fontFamily: "monospace", letterSpacing: "0.3px",
  },

  selectedPill: {
    marginTop: 12, textAlign: "center",
    background: C.blueSoft, color: C.blue,
    fontSize: 11, fontWeight: 600,
    borderRadius: 6, padding: "5px 0",
    border: `1px solid ${C.blueMid}`,
  },
  selectCta: {
    marginTop: 12, fontSize: 11,
    color: C.textLight, textAlign: "right",
  },

  // Skeleton
  skeleton: {
    background: C.white, border: `1px solid ${C.border}`,
    borderRadius: 12, padding: 20,
    boxShadow: "0 1px 4px rgba(0,31,91,0.04)",
  },
  skeletonTop: {
    height: 36, width: 36, borderRadius: "50%",
    background: "#EEF2FA", marginBottom: 16,
  },
  skeletonLine: {
    height: 12, borderRadius: 6,
    background: "#EEF2FA", marginBottom: 10, width: "80%",
  },

  empty: { textAlign: "center", padding: "60px 20px" },
  emptyIcon:  { fontSize: 44, marginBottom: 12 },
  emptyTitle: { fontSize: 16, fontWeight: 700, color: C.navy, marginBottom: 6 },
  emptyText:  { fontSize: 13, color: C.textLight, lineHeight: 1.6 },

  errorBox: {
    display: "flex", alignItems: "center", gap: 10,
    background: "#FFF5F5", border: "1px solid #FEB2B2",
    color: C.red, borderRadius: 10,
    padding: "14px 16px", fontSize: 13,
  },
  errorIcon: { fontSize: 18 },
};



// function PolicyPage() {
//   return (
//     <div>
//       <h2>Policies</h2>
//       <p>View available insurance policies.</p>
//     </div>
//   );
// }

// export default PolicyPage;