/**
 * MessageBubble.jsx
 *
 * Renders rich bot responses styled to match the Insurix navy/blue design system.
 *
 * Color palette (matches ChatPage.jsx):
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

// ─── Status Badge ────────────────────────────────────────────────────────────

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
      display: "inline-block", padding: "2px 9px", borderRadius: 20,
      fontSize: 11, fontWeight: 700, letterSpacing: "0.4px", textTransform: "uppercase",
      background: cfg.bg, color: cfg.color, border: `1px solid ${cfg.border}`,
    }}>
      {status}
    </span>
  );
}

// ─── KV Row ──────────────────────────────────────────────────────────────────

function KVRow({ label, value, last }) {
  const isStatus = label.toLowerCase() === "status";
  return (
    <div style={{
      display: "flex", alignItems: "flex-start", gap: 10, padding: "5px 0",
      borderBottom: last ? "none" : "1px solid #DDE3EF",
    }}>
      <span style={{
        minWidth: 92, fontSize: 10, fontWeight: 700, color: "#718096",
        textTransform: "uppercase", letterSpacing: "0.5px", paddingTop: 2, flexShrink: 0,
      }}>
        {label}
      </span>
      <span style={{ fontSize: 13, color: "#1A1A2E", fontWeight: 500, lineHeight: 1.5 }}>
        {isStatus ? <StatusBadge status={value} /> : value}
      </span>
    </div>
  );
}

// ─── Section parser ───────────────────────────────────────────────────────────

const kvRegex = /^([A-Za-z][A-Za-z\s]{0,30}):\s+(.+)$/;

/**
 * isPrompt: only true when the bot is actively waiting for user input.
 *
 * Requires one of:
 *   • "please select" / "please enter" / "please choose"  — choosing from a list
 *   • "please provide a … description"                    — freeform input
 *   • "reply with"                                        — explicit reply cue
 *
 * Deliberately excluded:
 *   • "please select the correct policy or provide a valid claim ID"
 *     → that's an error/info message, not a prompt for selection
 *
 * The key distinguishing rule: a genuine prompt either (a) has a numbered
 * list of options in the same section, or (b) asks for a "description" /
 * "details" as the next message. We therefore also require the section to
 * contain a numbered list OR an explicit "description"/"details" ask.
 */
function detectPrompt(text) {
  const lower = text.toLowerCase();

  // Must contain an explicit input request phrase
  const hasSelectOrChoose = /please\s+(select|choose|enter)\b/.test(lower);
  const hasDescriptionAsk = /please\s+provide\s+a\s+(brief\s+)?description/i.test(lower);
  const hasReplyWith      = /\breply\s+with\b/.test(lower);

  if (!hasSelectOrChoose && !hasDescriptionAsk && !hasReplyWith) return false;

  // "please select the correct policy" is an error redirect, not a prompt.
  // Detect by checking if the numbered-list options follow.
  const hasNumberedOptions = /^\s*\d+\.\s+\S/m.test(text);

  // For select/choose: only a prompt if options are present
  if (hasSelectOrChoose && !hasNumberedOptions) return false;

  // For "provide a description": always a prompt (user must type next)
  if (hasDescriptionAsk) return true;

  // For "reply with": always a prompt
  if (hasReplyWith) return true;

  return hasNumberedOptions;
}

function parseSection(raw) {
  const text = raw.trim();
  const isClaimDetails = /^claim details/i.test(text);
  const isPolicyAnswer = /^policy answer/i.test(text);
  const isPrompt       = detectPrompt(text);

  const stripLabel = (str, re) => str.replace(re, "").trimStart();
  let body = text;
  if (isClaimDetails) body = stripLabel(text, /^claim details\s*:?\s*/i);
  if (isPolicyAnswer) body = stripLabel(text, /^policy answer\s*:?\s*/i);

  const lines   = body.split("\n").filter(l => l.trim() !== "");
  const kvLines = lines.filter(l => kvRegex.test(l.trim()));
  const isKVBlock = kvLines.length >= Math.ceil(lines.length * 0.5);

  return { text, body, lines, isClaimDetails, isPolicyAnswer, isPrompt, isKVBlock };
}

// ─── Card: Claim Details ──────────────────────────────────────────────────────

function ClaimCard({ section }) {
  const rows = section.lines
    .map(l => l.trim().match(kvRegex))
    .filter(Boolean)
    .map(m => ({ label: m[1], value: m[2] }));

  return (
    <div style={{ border: "1px solid #C3D3F0", borderRadius: 9, overflow: "hidden", background: "#fff" }}>
      <div style={{
        background: "#F0F4FF", borderBottom: "1px solid #C3D3F0",
        padding: "7px 13px", display: "flex", alignItems: "center", gap: 7,
      }}>
        <svg width="13" height="13" viewBox="0 0 28 28" fill="none" aria-hidden="true">
          <path d="M14 2L4 6.5V14c0 5.25 4.2 9.8 10 11 5.8-1.2 10-5.75 10-11V6.5L14 2Z" fill="#4A9EE0"/>
          <path d="M10 14l3 3 5-6" stroke="#fff" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
        </svg>
        <span style={{ fontSize: 10, fontWeight: 700, letterSpacing: "0.6px", textTransform: "uppercase", color: "#001F5B" }}>
          Claim Details
        </span>
      </div>
      <div style={{ padding: "4px 13px 8px" }}>
        {rows.map((r, i) => <KVRow key={i} label={r.label} value={r.value} last={i === rows.length - 1} />)}
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
      border: "1px solid #C3D3F0", borderLeft: "3px solid #0057A8",
      borderRadius: "0 9px 9px 0", background: "#fff", padding: "10px 13px",
    }}>
      <div style={{ display: "flex", alignItems: "center", gap: 6, marginBottom: 6 }}>
        <svg width="12" height="12" viewBox="0 0 16 16" fill="none" aria-hidden="true">
          <circle cx="8" cy="8" r="6.5" stroke="#4A9EE0" strokeWidth="1.4"/>
          <path d="M5 8l2 2 4-4" stroke="#4A9EE0" strokeWidth="1.4" strokeLinecap="round" strokeLinejoin="round"/>
        </svg>
        <span style={{ fontSize: 10, fontWeight: 700, letterSpacing: "0.6px", textTransform: "uppercase", color: "#4A6FA5" }}>
          Policy Answer
          {subLabel && <span style={{ color: "#0057A8" }}> &middot; {subLabel}</span>}
        </span>
      </div>
      <p style={{ fontSize: 14, fontWeight: 600, color: "#001F5B", margin: 0, lineHeight: 1.55 }}>
        {content}
      </p>
    </div>
  );
}

// ─── Card: Reply Needed (genuine input prompt) ────────────────────────────────

function PromptCard({ text }) {
  const lines      = text.split("\n").filter(l => l.trim());
  const numbered   = lines.filter(l => /^\d+\./.test(l.trim()));
  const prose      = lines.filter(l => !/^\d+\./.test(l.trim()));
  const hasOptions = numbered.length > 0;

  return (
    <div style={{ border: "1px solid #C3D3F0", borderRadius: 9, overflow: "hidden", background: "#fff" }}>
      {/* Header */}
      <div style={{
        background: "#F0F4FF", borderBottom: "1px solid #C3D3F0",
        padding: "7px 13px", display: "flex", alignItems: "center", gap: 7,
      }}>
        <svg width="13" height="13" viewBox="0 0 16 16" fill="none" aria-hidden="true">
          <path d="M2 3a1 1 0 011-1h10a1 1 0 011 1v7a1 1 0 01-1 1H5l-3 2V3z" fill="#4A9EE0"/>
        </svg>
        <span style={{ fontSize: 10, fontWeight: 700, letterSpacing: "0.6px", textTransform: "uppercase", color: "#001F5B" }}>
          Reply Needed
        </span>
        <span style={{
          marginLeft: "auto", fontSize: 11, fontWeight: 600,
          background: "#4A6FA5", color: "#fff", borderRadius: 20,
          padding: "3px 10px", whiteSpace: "nowrap",
        }}>
          Type your answer ↓
        </span>
      </div>
      {/* Prose */}
      <div style={{ padding: hasOptions ? "10px 13px 6px" : "10px 13px" }}>
        {prose.map((line, i) => (
          <p key={i} style={{ fontSize: 13, color: "#1A1A2E", margin: "0 0 4px", lineHeight: 1.6 }}>
            {line}
          </p>
        ))}
      </div>
      {/* Numbered options */}
      {hasOptions && (
        <div style={{ padding: "0 13px 10px", display: "flex", flexDirection: "column" }}>
          {numbered.map((item, i) => {
            const label = item.replace(/^\d+\.\s*/, "").trim();
            return (
              <div key={i} style={{
                display: "flex", alignItems: "center", gap: 10, padding: "7px 0",
                borderBottom: i < numbered.length - 1 ? "1px solid #DDE3EF" : "none",
              }}>
                <span style={{
                  width: 24, height: 24, borderRadius: "50%",
                  background: "#0057A8", color: "#fff",
                  fontSize: 11, fontWeight: 700,
                  display: "flex", alignItems: "center", justifyContent: "center", flexShrink: 0,
                }}>
                  {i + 1}
                </span>
                <span style={{ fontSize: 14, color: "#1A1A2E", fontWeight: 500 }}>{label}</span>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}

// ─── Card: Info / Generic structured response ─────────────────────────────────
//
// Handles free-form responses that have:
//   • A leading prose line (title/summary)
//   • Bullet sections (lines starting with •)
//   • Sub-headers (short lines ending with ":")
//   • Plain paragraphs
//
// Renders as a clean card with a subtle left border so it looks at home
// alongside the other card types.

function BulletItem({ text }) {
  return (
    <div style={{ display: "flex", alignItems: "flex-start", gap: 8, padding: "3px 0" }}>
      <span style={{
        width: 6, height: 6, borderRadius: "50%",
        background: "#4A9EE0", flexShrink: 0, marginTop: 6,
      }} />
      <span style={{ fontSize: 13, color: "#1A1A2E", lineHeight: 1.6 }}>{text}</span>
    </div>
  );
}

function InfoCard({ text }) {
  const rawLines = text.split("\n");

  // Group lines into logical blocks
  const blocks = [];
  let currentGroup = null;

  for (const raw of rawLines) {
    const line = raw.trim();
    if (!line) {
      // Blank line → flush current group
      if (currentGroup) { blocks.push(currentGroup); currentGroup = null; }
      continue;
    }

    const isBullet      = /^[•\-\*]\s+/.test(line);
    const isSubHeader   = /^[A-Za-z][^:]{1,40}:$/.test(line);  // e.g. "Currently I can help with:"
    const isNumbered    = /^\d+\.\s+/.test(line);

    if (isBullet || isNumbered) {
      if (!currentGroup || currentGroup.type !== "list") {
        if (currentGroup) blocks.push(currentGroup);
        currentGroup = { type: "list", items: [] };
      }
      currentGroup.items.push(line.replace(/^[•\-\*\d+\.]\s+/, "").trim());
    } else if (isSubHeader) {
      if (currentGroup) blocks.push(currentGroup);
      currentGroup = { type: "subheader", text: line.replace(/:$/, "") };
      blocks.push(currentGroup);
      currentGroup = null;
    } else {
      // Plain prose — attach to current prose group or start new one
      if (!currentGroup || currentGroup.type !== "prose") {
        if (currentGroup) blocks.push(currentGroup);
        currentGroup = { type: "prose", lines: [] };
      }
      currentGroup.lines.push(line);
    }
  }
  if (currentGroup) blocks.push(currentGroup);

  // First prose block becomes the summary line (slightly emphasised)
  const firstProseIdx = blocks.findIndex(b => b.type === "prose");

  return (
    <div style={{
      border: "1px solid #C3D3F0",
      borderLeft: "3px solid #4A9EE0",
      borderRadius: "0 9px 9px 0",
      background: "#fff",
      padding: "12px 14px",
      display: "flex",
      flexDirection: "column",
      gap: 10,
    }}>
      {blocks.map((block, i) => {
        if (block.type === "prose") {
          const isFirst = i === firstProseIdx;
          return (
            <div key={i}>
              {block.lines.map((line, j) => (
                <p key={j} style={{
                  fontSize: isFirst && j === 0 ? 14 : 13,
                  fontWeight: isFirst && j === 0 ? 500 : 400,
                  color: isFirst && j === 0 ? "#001F5B" : "#1A1A2E",
                  margin: j < block.lines.length - 1 ? "0 0 4px" : 0,
                  lineHeight: 1.6,
                }}>
                  {line}
                </p>
              ))}
            </div>
          );
        }

        if (block.type === "subheader") {
          return (
            <p key={i} style={{
              fontSize: 10, fontWeight: 700, letterSpacing: "0.5px",
              textTransform: "uppercase", color: "#4A6FA5",
              margin: 0, paddingTop: i > 0 ? 4 : 0,
            }}>
              {block.text}
            </p>
          );
        }

        if (block.type === "list") {
          return (
            <div key={i} style={{ display: "flex", flexDirection: "column", gap: 2, paddingLeft: 2 }}>
              {block.items.map((item, j) => <BulletItem key={j} text={item} />)}
            </div>
          );
        }

        return null;
      })}
    </div>
  );
}

// ─── Section divider ─────────────────────────────────────────────────────────

function SectionDivider() {
  return (
    <div style={{ display: "flex", alignItems: "center", gap: 6, padding: "2px 0" }}>
      <div style={{ flex: 1, height: "1px", background: "#DDE3EF" }} />
      <div style={{ width: 4, height: 4, borderRadius: "50%", background: "#C3D3F0" }} />
      <div style={{ flex: 1, height: "1px", background: "#DDE3EF" }} />
    </div>
  );
}

// ─── Decide whether a section is "structured enough" to use InfoCard ─────────
// Plain single-sentence responses (no bullets, no sub-headers, no blank lines)
// are rendered as bare text to avoid over-engineering simple answers.

function isStructuredText(text) {
  return (
    /\n\s*\n/.test(text) ||          // has paragraph breaks
    /^[•\-\*]\s+/m.test(text) ||     // has bullet points
    /^[A-Za-z][^:]{1,40}:$/m.test(text) // has sub-headers
  );
}

// ─── Main content renderer ────────────────────────────────────────────────────

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
            <div style={{ border: "1px solid #C3D3F0", borderRadius: 9, background: "#fff", padding: "8px 13px" }}>
              {sec.lines.map((line, j) => {
                const m = line.trim().match(kvRegex);
                if (m) return <KVRow key={j} label={m[1]} value={m[2]} last={j === sec.lines.length - 1} />;
                return <p key={j} style={{ fontSize: 13, color: "#1A1A2E", margin: "4px 0" }}>{line}</p>;
              })}
            </div>
          ) : isStructuredText(sec.text) ? (
            <InfoCard text={sec.text} />
          ) : (
            <p style={{ fontSize: 13, color: "#1A1A2E", margin: 0, lineHeight: 1.7 }}>
              {sec.text.trim()}
            </p>
          )}
        </div>
      ))}
    </div>
  );
}

// ─── Export ───────────────────────────────────────────────────────────────────

function MessageBubble({ sender, text }) {
  if (sender === "bot") return <BotMessageContent text={text} />;
  return (
    <div style={{ display: "flex", justifyContent: "flex-end" }}>
      <div style={{
        maxWidth: "72%", padding: "10px 14px",
        borderRadius: "12px 12px 3px 12px",
        background: "#0057A8", color: "#fff", fontSize: 14, lineHeight: 1.6,
      }}>
        {text}
      </div>
    </div>
  );
}

export default MessageBubble;