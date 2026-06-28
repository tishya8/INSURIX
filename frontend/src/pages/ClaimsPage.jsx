import { useState, useContext } from "react";
import { PolicyContext } from "../components/PolicyContext";
import { createClaim, getClaimStatus } from "../api/insurix";

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
  greenMid:  "#A7F3D0",
  red:       "#C53030",
  redSoft:   "#FFF5F5",
  redBorder: "#FEB2B2",
  amber:     "#92400E",
  amberSoft: "#FEF3C7",
};

const INCIDENT_TYPES = [
  { value: "accident",       label: "Accident"},
  { value: "theft",          label: "Theft" },
  { value: "natural_damage", label: "Flood"},
  { value: "fire",           label: "Fire"},
  { value: "other",          label: "Other"},
];

const CLAIM_STATUS_STYLES = {
  SUBMITTED:    { bg: C.blueSoft,  color: C.blue,   label: "Submitted" },
  UNDER_REVIEW: { bg: C.amberSoft, color: C.amber,  label: "Under Review" },
  APPROVED:     { bg: C.greenSoft, color: C.green,  label: "Approved" },
  REJECTED:     { bg: C.redSoft,   color: C.red,    label: "Rejected" },
};

export default function ClaimsPage() {
  const { policies, policyId, setPolicyId, loadingPolicies } =
    useContext(PolicyContext);

  // File claim
  const [incidentType,  setIncidentType]  = useState("");
  const [description,   setDescription]   = useState("");
  const [submitting,    setSubmitting]     = useState(false);
  const [submitError,   setSubmitError]    = useState("");
  const [submitSuccess, setSubmitSuccess]  = useState(null);

  // Track claim
  const [trackId,     setTrackId]     = useState("");
  const [tracking,    setTracking]    = useState(false);
  const [trackResult, setTrackResult] = useState(null);
  const [trackError,  setTrackError]  = useState("");

  const handleSubmit = async (e) => {
    e.preventDefault();
    setSubmitError("");
    setSubmitSuccess(null);

    if (!policyId)             { setSubmitError("Please select a policy first."); return; }
    if (!incidentType)         { setSubmitError("Please choose an incident type."); return; }
    if (description.length < 10) { setSubmitError("Description must be at least 10 characters."); return; }

    setSubmitting(true);
    try {
      const result = await createClaim(policyId, incidentType, description);
      setSubmitSuccess(result);
      setIncidentType("");
      setDescription("");
    } catch (err) {
      setSubmitError(err.message);
    } finally {
      setSubmitting(false);
    }
  };

  const handleTrack = async (e) => {
    e.preventDefault();
    setTrackError("");
    setTrackResult(null);

    if (!trackId.trim()) { setTrackError("Please enter a claim ID."); return; }

    setTracking(true);
    try {
      const result = await getClaimStatus(Number(trackId));
      if (!result) throw new Error("Claim not found.");
      setTrackResult(result);
    } catch (err) {
      setTrackError(err.message);
    } finally {
      setTracking(false);
    }
  };

  const activePolicies = policies.filter(p => p.status === "ACTIVE");

  return (
    <div style={s.page}>

      {/* ── Header ── */}
      <div style={s.header}>
        <div>
          <h1 style={s.title}>Claims</h1>
          <p style={s.subtitle}>File a new claim or track an existing one</p>
        </div>
      </div>

      <div style={s.twoCol}>

        {/* ══ LEFT: File a Claim ══ */}
        <div style={s.card}>
          <div style={s.cardHeader}>
            <div style={{ ...s.cardIconWrap, background: C.blueSoft }}>
              <span style={s.cardIcon}>📝</span>
            </div>
            <div>
              <div style={s.cardTitle}>File a Claim</div>
              <div style={s.cardSub}>Submit a new insurance claim</div>
            </div>
          </div>

          <form onSubmit={handleSubmit}>

            {/* Policy selector */}
            <div style={s.field}>
              <label style={s.label}>Policy</label>
              {loadingPolicies ? (
                <div style={s.skeletonInput} />
              ) : (
                <select
                  value={policyId || ""}
                  onChange={e => setPolicyId(e.target.value)}
                  style={s.select}
                >
                  <option value="">Select a policy…</option>
                  {activePolicies.map(p => (
                    <option key={p.policy_id} value={String(p.policy_id)}>
                      {p.policy_number} — {p.vehicle_model}
                    </option>
                  ))}
                </select>
              )}
              {!loadingPolicies && activePolicies.length === 0 && (
                <p style={s.fieldHint}>No active policies found.</p>
              )}
            </div>

            {/* Incident type */}
            <div style={s.field}>
              <label style={s.label}>Incident Type</label>
              <select
                value={incidentType}
                onChange={e => setIncidentType(e.target.value)}
                style={s.select}
              >
                <option value="">Select type…</option>
                {INCIDENT_TYPES.map(t => (
                  <option key={t.value} value={t.value}>
                    {t.icon}  {t.label}
                  </option>
                ))}
              </select>
            </div>

            {/* Description */}
            <div style={s.field}>
              <label style={s.label}>Description</label>
              <textarea
                value={description}
                onChange={e => setDescription(e.target.value)}
                placeholder="Describe what happened in detail — date, location, circumstances…"
                rows={4}
                style={s.textarea}
              />
              <p style={s.charCount}>{description.length} characters {description.length < 10 ? `(min 10)` : "✓"}</p>
            </div>

            {submitError && (
              <div style={s.alertError}>⚠️ {submitError}</div>
            )}

            {submitSuccess && (
              <div style={s.alertSuccess}>
                <strong>✓ Claim #{submitSuccess.claim_id} submitted!</strong>
                <br />
                Status: <strong>{submitSuccess.status}</strong>. Use the claim ID to track progress.
              </div>
            )}

            <button
              type="submit"
              disabled={submitting}
              style={{ ...s.btnPrimary, opacity: submitting ? 0.7 : 1 }}
            >
              {submitting ? "Submitting…" : "Submit Claim"}
            </button>
          </form>
        </div>

        {/* ══ RIGHT: Track a Claim ══ */}
        <div>
          <div style={s.card}>
            <div style={s.cardHeader}>
              <div style={{ ...s.cardIconWrap, background: "#EEF2FA" }}>
                <span style={s.cardIcon}>🔍</span>
              </div>
              <div>
                <div style={s.cardTitle}>Track a Claim</div>
                <div style={s.cardSub}>Check status using your claim ID</div>
              </div>
            </div>

            <form onSubmit={handleTrack}>
              <div style={s.field}>
                <label style={s.label}>Claim ID</label>
                <input
                  type="number"
                  value={trackId}
                  onChange={e => setTrackId(e.target.value)}
                  placeholder="e.g. 42"
                  style={s.input}
                  min="1"
                />
              </div>

              {trackError && (
                <div style={s.alertError}>⚠️ {trackError}</div>
              )}

              <button
                type="submit"
                disabled={tracking}
                style={{ ...s.btnOutline, opacity: tracking ? 0.7 : 1 }}
              >
                {tracking ? "Searching…" : "Track Claim"}
              </button>
            </form>

            {/* Track result */}
            {trackResult && (() => {
              const sc = CLAIM_STATUS_STYLES[trackResult.claim_status]
                || { bg: C.bg, color: C.textMid, label: trackResult.claim_status };
              return (
                <div style={s.trackResult}>
                  <div style={s.trackResultTitle}>Claim Details</div>

                  {[
                    { label: "Claim ID",   value: `#${trackResult.claim_id}` },
                    { label: "Policy ID",  value: trackResult.policy_id },
                    { label: "Type",       value: trackResult.incident_type?.replace("_", " ") },
                  ].map(row => (
                    <div key={row.label} style={s.trackRow}>
                      <span style={s.trackLabel}>{row.label}</span>
                      <span style={s.trackValue}>{row.value}</span>
                    </div>
                  ))}

                  <div style={s.trackRow}>
                    <span style={s.trackLabel}>Status</span>
                    <span style={{ ...s.statusBadge, background: sc.bg, color: sc.color }}>
                      {sc.label}
                    </span>
                  </div>

                  {trackResult.description && (
                    <div style={s.trackDesc}>{trackResult.description}</div>
                  )}
                </div>
              );
            })()}
          </div>

          {/* Info box */}
          <div style={s.infoBox}>
            <div style={s.infoTitle}>💡 How claims work</div>
            <ol style={s.infoList}>
              <li>Submit your claim with incident details</li>
              <li>Our team reviews within 2–3 business days</li>
              <li>Track status anytime using your claim ID</li>
              <li>Approved claims are processed within 7 days</li>
            </ol>
          </div>
        </div>

      </div>
    </div>
  );
}

const s = {
  page:    { maxWidth: 920, margin: "0 auto" },
  header:  { marginBottom: 24 },
  title:   { fontSize: 20, fontWeight: 700, color: C.navy, letterSpacing: "-0.3px" },
  subtitle:{ fontSize: 13, color: C.textLight, marginTop: 4 },

  twoCol: { display: "grid", gridTemplateColumns: "1fr 1fr", gap: 20, alignItems: "start" },

  card: {
    background: C.white, border: `1px solid ${C.border}`,
    borderRadius: 12, padding: 24,
    boxShadow: "0 1px 4px rgba(0,31,91,0.06)",
    marginBottom: 16,
  },
  cardHeader: { display: "flex", alignItems: "center", gap: 12, marginBottom: 20 },
  cardIconWrap: { width: 40, height: 40, borderRadius: 10, display: "flex", alignItems: "center", justifyContent: "center" },
  cardIcon:    { fontSize: 20 },
  cardTitle:   { fontSize: 15, fontWeight: 700, color: C.navy },
  cardSub:     { fontSize: 12, color: C.textLight, marginTop: 2 },

  field:       { marginBottom: 14 },
  label: {
    display: "block", fontSize: 12, fontWeight: 600,
    color: C.textMid, marginBottom: 5,
    textTransform: "uppercase", letterSpacing: "0.4px",
  },
  select: {
    width: "100%", padding: "9px 12px",
    border: `1px solid ${C.border}`, borderRadius: 8,
    fontSize: 14, color: C.textDark, background: "#FAFBFD",
    outline: "none", fontFamily: "inherit", boxSizing: "border-box",
  },
  input: {
    width: "100%", padding: "9px 12px",
    border: `1px solid ${C.border}`, borderRadius: 8,
    fontSize: 14, color: C.textDark, background: "#FAFBFD",
    outline: "none", fontFamily: "inherit", boxSizing: "border-box",
  },
  textarea: {
    width: "100%", padding: "9px 12px",
    border: `1px solid ${C.border}`, borderRadius: 8,
    fontSize: 14, color: C.textDark, background: "#FAFBFD",
    outline: "none", fontFamily: "inherit",
    resize: "vertical", minHeight: 100, boxSizing: "border-box",
    lineHeight: 1.6,
  },
  charCount:    { fontSize: 11, color: C.textLight, marginTop: 4, textAlign: "right" },
  fieldHint:    { fontSize: 11, color: C.textLight, marginTop: 4 },
  skeletonInput:{ height: 38, borderRadius: 8, background: "#EEF2FA" },

  alertError: {
    background: C.redSoft, border: `1px solid ${C.redBorder}`,
    color: C.red, borderRadius: 8,
    padding: "10px 12px", fontSize: 13, marginBottom: 12,
  },
  alertSuccess: {
    background: C.greenSoft, border: `1px solid ${C.greenMid}`,
    color: C.green, borderRadius: 8,
    padding: "10px 12px", fontSize: 13, marginBottom: 12, lineHeight: 1.6,
  },

  btnPrimary: {
    width: "100%", padding: "10px",
    background: C.blue, color: C.white,
    border: "none", borderRadius: 8,
    fontSize: 14, fontWeight: 600, cursor: "pointer",
    fontFamily: "inherit",
  },
  btnOutline: {
    width: "100%", padding: "10px",
    background: "transparent", color: C.blue,
    border: `2px solid ${C.blue}`, borderRadius: 8,
    fontSize: 14, fontWeight: 600, cursor: "pointer",
    fontFamily: "inherit",
  },

  trackResult: {
    marginTop: 20, padding: 16,
    background: C.bg, border: `1px solid ${C.border}`,
    borderRadius: 10, display: "flex", flexDirection: "column", gap: 10,
  },
  trackResultTitle: { fontSize: 12, fontWeight: 700, color: C.navy, textTransform: "uppercase", letterSpacing: "0.5px", marginBottom: 4 },
  trackRow:   { display: "flex", justifyContent: "space-between", alignItems: "center" },
  trackLabel: { fontSize: 12, color: C.textLight },
  trackValue: { fontSize: 13, fontWeight: 600, color: C.textDark },
  statusBadge:{
    fontSize: 11, fontWeight: 700, padding: "3px 10px",
    borderRadius: 20, textTransform: "uppercase", letterSpacing: "0.5px",
  },
  trackDesc: {
    fontSize: 13, color: C.textMid, lineHeight: 1.6,
    borderTop: `1px solid ${C.border}`, paddingTop: 10, marginTop: 4,
  },

  infoBox: {
    background: C.blueSoft, border: `1px solid ${C.blueMid}`,
    borderRadius: 10, padding: "14px 16px",
  },
  infoTitle: { fontSize: 13, fontWeight: 600, color: C.navy, marginBottom: 8 },
  infoList: {
    paddingLeft: 18, fontSize: 12,
    color: C.textMid, lineHeight: 2,
  },
};

// function ClaimsPage() {
//   return (
//     <div>
//       <h2>Claims</h2>
//       <p>View and track insurance claims.</p>
//     </div>
//   );
// }

// export default ClaimsPage;