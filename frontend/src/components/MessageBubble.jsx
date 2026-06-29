/**
 * MessageBubble.jsx
 *
 * Renders rich bot responses styled to match the Insurix navy/blue design system.
 * Uses the app's existing color palette:
 *   #001F5B  — navy headings
 *   #0057A8  — primary blue
 *   #4A9EE0  — light blue accent
 *   #EEF2FA  — bot bubble bg
 *   #C3D3F0  — card borders
 *   #DDE3EF  — dividers
 *   #F0F4FF  — card surfaces
 *   #718096  — muted text
 *   #1A1A2E  — body text
 */

// ─── Status Badge ───────────────────────────────────────────────────────────

function StatusBadge({ status }) {
  const map = {
    SUBMITTED:  { bg: "#E8EFFF", color: "#0057A8", border: "#C3D3F0" },
    APPROVED:   { bg: "#E6F2ED", color: "#1A6B3A", border: "#B0D9C0" },
    REJECTED:   { bg: "#FDE8E8", color: "#B91C1C", border: "#F5C0C0" },
    PENDING:    { bg: "#FEF3E2", color: "#92400E", border: "#FAD7A0" },
    PROCESSING: { bg: "#EDE9FE", color: "#5B21B6", border: "#C4B5FD" },
  };
  const cfg = map[status?.toUpperCase()] ?? { bg: "#E8EFFF", color: "#0057A8", border: "#C3D3F0" };
  return (
    <span style={{
      display: "inline-block",
      padding: "2px 9px",
      borderRadius: 20,
      fontSize: 11,
      fontWeight: 700,
      letterSpacing: "0.4px",
      textTransform: "uppercase",
      background: cfg.bg,
      color: cfg.color,
      border: `1px solid ${cfg.border}`,
    }}>
      {status}
    </span>
  );
}

// ─── KV Row ─────────────────────────────────────────────────────────────────

function KVRow({ label, value, last }) {
  const isStatus = label.toLowerCase() === "status";
  return (
    <div style={{
      display: "flex",
      alignItems: "flex-start",
      gap: 10,
      padding: "5px 0",
      borderBottom: last ? "none" : "1px solid #DDE3EF",
    }}>
      <span style={{
        minWidth: 92,
        fontSize: 10,
        fontWeight: 700,
        color: "#718096",
        textTransform: "uppercase",
        letterSpacing: "0.5px",
        paddingTop: 2,
        flexShrink: 0,
      }}>
        {label}
      </span>
      <span style={{ fontSize: 13, color: "#1A1A2E", fontWeight: 500, lineHeight: 1.5 }}>
        {isStatus ? <StatusBadge status={value} /> : value}
      </span>
    </div>
  );
}

// ─── Section parser ──────────────────────────────────────────────────────────

const kvRegex = /^([A-Za-z][A-Za-z\s]{0,30}):\s+(.+)$/;

function parseSection(raw) {
  const text = raw.trim();
  const isClaimDetails = /^claim details/i.test(text);
  const isPolicyAnswer = /^policy answer/i.test(text);
  const isPrompt       = /please\s+(select|provide|enter|reply)/i.test(text);

  const stripLabel = (str, re) => str.replace(re, "").trimStart();
  let body = text;
  if (isClaimDetails) body = stripLabel(text, /^claim details\s*:?\s*/i);
  if (isPolicyAnswer) body = stripLabel(text, /^policy answer\s*:?\s*/i);

  const lines     = body.split("\n").filter(l => l.trim() !== "");
  const kvLines   = lines.filter(l => kvRegex.test(l.trim()));
  const isKVBlock = kvLines.length >= Math.ceil(lines.length * 0.5);
  const listItems = lines.filter(l => /^\d+\.\s+/.test(l.trim()));

  return { text, body, lines, isClaimDetails, isPolicyAnswer, isPrompt, isKVBlock, listItems };
}

// ─── Card: Claim Details ─────────────────────────────────────────────────────

function ClaimCard({ section }) {
  const rows = section.lines
    .map(l => l.trim().match(kvRegex))
    .filter(Boolean)
    .map(m => ({ label: m[1], value: m[2] }));

  return (
    <div style={{
      border: "1px solid #C3D3F0",
      borderRadius: 9,
      overflow: "hidden",
      background: "#fff",
    }}>
      {/* Header */}
      <div style={{
        background: "#F0F4FF",
        borderBottom: "1px solid #C3D3F0",
        padding: "7px 13px",
        display: "flex",
        alignItems: "center",
        gap: 7,
      }}>
        {/* Mini shield icon matching app */}
        <svg width="13" height="13" viewBox="0 0 28 28" fill="none" aria-hidden="true">
          <path d="M14 2L4 6.5V14c0 5.25 4.2 9.8 10 11 5.8-1.2 10-5.75 10-11V6.5L14 2Z" fill="#4A9EE0"/>
          <path d="M10 14l3 3 5-6" stroke="#fff" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
        </svg>
        <span style={{
          fontSize: 10,
          fontWeight: 700,
          letterSpacing: "0.6px",
          textTransform: "uppercase",
          color: "#001F5B",
        }}>
          Claim Details
        </span>
      </div>
      {/* Rows */}
      <div style={{ padding: "4px 13px 8px" }}>
        {rows.map((r, i) => (
          <KVRow key={i} label={r.label} value={r.value} last={i === rows.length - 1} />
        ))}
      </div>
    </div>
  );
}

// ─── Card: Policy Answer ──────────────────────────────────────────────────────

function PolicyCard({ section }) {
  const body = section.body.trim();
  const subLabelMatch = body.match(/^([A-Za-z][A-Za-z\s]{0,40}):\s+([\s\S]+)/);
  const subLabel = subLabelMatch ? subLabelMatch[1] : null;
  const content  = subLabelMatch ? subLabelMatch[2].trim() : body;

  return (
    <div style={{
      border: "1px solid #C3D3F0",
      borderLeft: "3px solid #0057A8",
      borderRadius: "0 9px 9px 0",
      background: "#fff",
      padding: "10px 13px",
    }}>
      {/* Label row */}
      <div style={{
        display: "flex",
        alignItems: "center",
        gap: 6,
        marginBottom: 6,
      }}>
        <svg width="12" height="12" viewBox="0 0 16 16" fill="none" aria-hidden="true">
          <circle cx="8" cy="8" r="6.5" stroke="#4A9EE0" strokeWidth="1.4"/>
          <path d="M5 8l2 2 4-4" stroke="#4A9EE0" strokeWidth="1.4" strokeLinecap="round" strokeLinejoin="round"/>
        </svg>
        <span style={{
          fontSize: 10,
          fontWeight: 700,
          letterSpacing: "0.6px",
          textTransform: "uppercase",
          color: "#4A6FA5",
        }}>
          Policy Answer
          {subLabel && (
            <span style={{ color: "#0057A8" }}> &middot; {subLabel}</span>
          )}
        </span>
      </div>
      {/* Answer text */}
      <p style={{
        fontSize: 14,
        fontWeight: 600,
        color: "#001F5B",
        margin: 0,
        lineHeight: 1.55,
      }}>
        {content}
      </p>
    </div>
  );
}

// ─── Numbered list (used outside PromptCard) ────────────────────────────────

function NumberedList({ items }) {
  return (
    <div style={{ marginTop: 8 }}>
      {items.map((item, i) => {
        const text = item.replace(/^\d+\.\s*/, "").trim();
        return (
          <div key={i} style={{
            display: "flex",
            alignItems: "center",
            gap: 10,
            padding: "5px 0",
            borderBottom: i < items.length - 1 ? "1px solid #DDE3EF" : "none",
          }}>
            <span style={{
              width: 22, height: 22, borderRadius: "50%",
              background: "#0057A8", color: "#fff",
              fontSize: 11, fontWeight: 700,
              display: "flex", alignItems: "center", justifyContent: "center",
              flexShrink: 0,
            }}>
              {i + 1}
            </span>
            <span style={{ fontSize: 13, color: "#1A1A2E", fontWeight: 500 }}>{text}</span>
          </div>
        );
      })}
    </div>
  );
}

// ─── Card: Action Required / Prompt ──────────────────────────────────────────
// Matches the rounded card style of ClaimCard — blue header strip, white body,
// plain numbered list rows with #0057A8 dots, no inline hints.

function PromptCard({ text }) {
  const lines      = text.split("\n").filter(l => l.trim());
  const numbered   = lines.filter(l => /^\d+\./.test(l.trim()));
  const prose      = lines.filter(l => !/^\d+\./.test(l.trim()));
  const hasOptions = numbered.length > 0;

  return (
    <div style={{
      border: "1px solid #C3D3F0",
      borderRadius: 9,
      overflow: "hidden",
      background: "#fff",
    }}>
      {/* Header strip — same style as ClaimCard */}
      <div style={{
        background: "#F0F4FF",
        borderBottom: "1px solid #C3D3F0",
        padding: "7px 13px",
        display: "flex",
        alignItems: "center",
        gap: 7,
      }}>
        {/* Info circle icon */}
        <svg width="13" height="13" viewBox="0 0 16 16" fill="none" aria-hidden="true">
          <circle cx="8" cy="8" r="6.5" stroke="#4A9EE0" strokeWidth="1.4"/>
          <path d="M8 7v4M8 5v.01" stroke="#4A9EE0" strokeWidth="1.5" strokeLinecap="round"/>
        </svg>
        <span style={{
          fontSize: 10,
          fontWeight: 700,
          letterSpacing: "0.6px",
          textTransform: "uppercase",
          color: "#001F5B",
        }}>
          Action Required
        </span>
      </div>

      {/* Prose lines */}
      <div style={{ padding: hasOptions ? "10px 13px 6px" : "10px 13px" }}>
        {prose.map((line, i) => (
          <p key={i} style={{
            fontSize: 13,
            color: "#1A1A2E",
            margin: "0 0 4px",
            lineHeight: 1.6,
          }}>
            {line}
          </p>
        ))}
      </div>

      {/* Numbered option rows */}
      {hasOptions && (
        <div style={{ padding: "0 13px 10px", display: "flex", flexDirection: "column" }}>
          {numbered.map((item, i) => {
            const label = item.replace(/^\d+\.\s*/, "").trim();
            return (
              <div key={i} style={{
                display: "flex",
                alignItems: "center",
                gap: 10,
                padding: "7px 0",
                borderBottom: i < numbered.length - 1 ? "1px solid #DDE3EF" : "none",
              }}>
                <span style={{
                  width: 24, height: 24,
                  borderRadius: "50%",
                  background: "#0057A8",
                  color: "#fff",
                  fontSize: 11,
                  fontWeight: 700,
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  flexShrink: 0,
                }}>
                  {i + 1}
                </span>
                <span style={{ fontSize: 14, color: "#1A1A2E", fontWeight: 500 }}>
                  {label}
                </span>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}

// ─── Generic plain / fallback ────────────────────────────────────────────────

function PlainBlock({ text }) {
  const lines      = text.split("\n").filter(l => l.trim());
  const isNumbered = lines.length > 1 && lines.every(l => /^\d+\./.test(l.trim()));
  if (isNumbered) return <NumberedList items={lines} />;
  return (
    <p style={{ fontSize: 13, color: "#1A1A2E", margin: 0, lineHeight: 1.7 }}>
      {text.trim()}
    </p>
  );
}

// ─── Section divider ─────────────────────────────────────────────────────────

function SectionDivider() {
  return (
    <div style={{
      display: "flex",
      alignItems: "center",
      gap: 6,
      padding: "2px 0",
    }}>
      <div style={{ flex: 1, height: "1px", background: "#DDE3EF" }} />
      <div style={{ width: 4, height: 4, borderRadius: "50%", background: "#C3D3F0" }} />
      <div style={{ flex: 1, height: "1px", background: "#DDE3EF" }} />
    </div>
  );
}

// ─── Main content renderer ───────────────────────────────────────────────────

function BotMessageContent({ text }) {
  const sections = text.split(/\n\s*---\s*\n/).map(parseSection);

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
      {sections.map((sec, i) => (
        <div key={i}>
          {i > 0 && <SectionDivider />}
          {sec.isClaimDetails ? (
            <ClaimCard section={sec} />
          ) : sec.isPolicyAnswer ? (
            <PolicyCard section={sec} />
          ) : sec.isPrompt ? (
            <PromptCard text={sec.text} />
          ) : sec.isKVBlock ? (
            <div style={{
              border: "1px solid #C3D3F0",
              borderRadius: 9,
              background: "#fff",
              padding: "8px 13px",
            }}>
              {sec.lines.map((line, j) => {
                const m = line.trim().match(kvRegex);
                if (m) return <KVRow key={j} label={m[1]} value={m[2]} last={j === sec.lines.length - 1} />;
                return <p key={j} style={{ fontSize: 13, color: "#1A1A2E", margin: "4px 0" }}>{line}</p>;
              })}
            </div>
          ) : (
            <PlainBlock text={sec.text} />
          )}
        </div>
      ))}
    </div>
  );
}

// ─── Export ──────────────────────────────────────────────────────────────────

function MessageBubble({ sender, text }) {
  // Bot: render rich content; ChatPage supplies the outer bubble shell
  if (sender === "bot") return <BotMessageContent text={text} />;

  // User fallback (ChatPage handles this directly)
  return (
    <div style={{ display: "flex", justifyContent: "flex-end" }}>
      <div style={{
        maxWidth: "72%",
        padding: "10px 14px",
        borderRadius: "12px 12px 3px 12px",
        background: "#0057A8",
        color: "#fff",
        fontSize: 14,
        lineHeight: 1.6,
      }}>
        {text}
      </div>
    </div>
  );
}

export default MessageBubble;