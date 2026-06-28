import { useState, useContext, useRef, useEffect } from "react";
import { PolicyContext } from "../components/PolicyContext";
import { useAuth } from "../context/AuthContext";
import { askPolicy } from "../api/insurix";

const SUGGESTIONS = [
  "What is excluded from this policy?",
  "Create a claim",
  "Track claim status <YOUR_CLAIM_ID>",
];

export default function ChatPage() {
  const { policyId, selectedPolicy, loadingPolicies } = useContext(PolicyContext);
  const { user } = useAuth();

  const [question, setQuestion] = useState("");
  const [messages, setMessages] = useState([]);
  const [loading,  setLoading]  = useState(false);
  const bottomRef = useRef(null);

  // Auto-scroll to latest message
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  const handleSend = async () => {
    const q = question.trim();
    if (!q || !policyId) return;

    setMessages(prev => [...prev, { sender: "user", text: q }]);
    setQuestion("");
    setLoading(true);

    try {
      const result = await askPolicy(policyId, q);
      setMessages(prev => [...prev, { sender: "bot", text: result.answer || "No answer returned." }]);
    } catch (err) {
      setMessages(prev => [...prev, { sender: "bot", text: "Unable to connect to the backend. Please try again.", isError: true }]);
    } finally {
      setLoading(false);
    }
  };

  const handleKey = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const policyLabel = selectedPolicy
    ? `${selectedPolicy.policy_number} — ${selectedPolicy.vehicle_model}`
    : loadingPolicies ? "Loading…" : "No policy selected";

  return (
    <div style={s.page}>

      {/* ── Header ── */}
      <div style={s.header}>
        <div>
          <h1 style={s.title}>Policy Assistant</h1>
          <p style={s.subtitle}>Ask anything about your insurance policy</p>
        </div>
        <div style={s.userBadge}>
          <span style={s.userDot} />
          {user?.name || "User"}
        </div>
      </div>

      {/* ── Active policy banner ── */}
      <div style={s.policyBanner}>
        <span style={s.bannerIcon}>📋</span>
        <div>
          <div style={s.bannerLabel}>Active Policy</div>
          <div style={s.bannerValue}>{policyLabel}</div>
        </div>
        {!policyId && !loadingPolicies && (
          <span style={s.bannerHint}>← Select a policy from the sidebar</span>
        )}
      </div>

      {/* ── Chat window ── */}
      <div style={s.chatWindow}>

        {/* Empty state */}
        {messages.length === 0 && !loading && (
          <div style={s.emptyState}>
            <div style={s.emptyIcon}><ShieldSVGBig /></div>
            <div style={s.emptyTitle}>Start a conversation</div>
            <div style={s.emptySubtitle}>
              Ask anything about your selected insurance policy.
            </div>
            <div style={s.suggestions}>
              {SUGGESTIONS.map(q => (
                <button
                  key={q}
                  style={s.suggestionBtn}
                  onClick={() => setQuestion(q)}
                >
                  {q}
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Messages */}
        {messages.map((msg, i) => (
          <div
            key={i}
            style={{
              ...s.msgRow,
              justifyContent: msg.sender === "user" ? "flex-end" : "flex-start",
            }}
          >
            {msg.sender === "bot" && <div style={s.botAvatar}><ShieldSVG /></div>}
            <div style={{
              ...s.bubble,
              ...(msg.sender === "user" ? s.bubbleUser : s.bubbleBot),
              ...(msg.isError ? s.bubbleError : {}),
            }}>
              {msg.text}
            </div>
          </div>
        ))}

        {/* Typing indicator */}
        {loading && (
          <div style={{ ...s.msgRow, justifyContent: "flex-start" }}>
            <div style={s.botAvatar}><ShieldSVG /></div>
            <div style={s.bubbleBot}>
              <div style={s.typingDots}>
                <span style={s.dot} /><span style={s.dot} /><span style={s.dot} />
              </div>
            </div>
          </div>
        )}

        <div ref={bottomRef} />
      </div>

      {/* ── Input row ── */}
      <div style={s.inputRow}>
        <textarea
          value={question}
          onChange={e => setQuestion(e.target.value)}
          onKeyDown={handleKey}
          placeholder={policyId ? "Ask a question about your policy…" : "Select a policy first"}
          disabled={!policyId || loading}
          rows={1}
          style={s.textarea}
        />
        <button
          onClick={handleSend}
          disabled={!question.trim() || !policyId || loading}
          style={{
            ...s.sendBtn,
            opacity: (!question.trim() || !policyId || loading) ? 0.4 : 1,
          }}
        >
          ↑
        </button>
      </div>

    </div>
  );
}

function ShieldSVGBig() {
  return (
    <svg width="44" height="44" viewBox="0 0 28 28" fill="none">
      <path d="M14 2L4 6.5V14c0 5.25 4.2 9.8 10 11 5.8-1.2 10-5.75 10-11V6.5L14 2Z" fill="#4A9EE0"/>
      <path d="M10 14l3 3 5-6" stroke="#fff" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round"/>
    </svg>
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
  page: {
    display: "flex",
    flexDirection: "column",
    height: "calc(100vh - 56px)",
    maxWidth: 860,
    margin: "0 auto",
  },
  header: {
    display: "flex",
    justifyContent: "space-between",
    alignItems: "flex-start",
    marginBottom: 18,
  },
  title: {
    fontSize: 20, fontWeight: 700,
    color: "#001F5B", letterSpacing: "-0.3px",
  },
  subtitle: { fontSize: 13, color: "#718096", marginTop: 3 },
  userBadge: {
    display: "flex", alignItems: "center", gap: 6,
    background: "#fff", border: "1px solid #DDE3EF",
    borderRadius: 8, padding: "6px 12px",
    fontSize: 13, color: "#1A1A2E", fontWeight: 500,
    boxShadow: "0 1px 3px rgba(0,31,91,0.06)",
  },
  userDot: { width: 8, height: 8, borderRadius: "50%", background: "#4CAF82" },

  policyBanner: {
    display: "flex", alignItems: "center", gap: 12,
    background: "#fff", border: "1px solid #DDE3EF",
    borderRadius: 10, padding: "12px 16px", marginBottom: 14,
    boxShadow: "0 1px 4px rgba(0,31,91,0.05)",
  },
  bannerIcon:  { fontSize: 18 },
  bannerLabel: { fontSize: 10, color: "#A0AEC0", fontWeight: 600, textTransform: "uppercase", letterSpacing: "0.5px" },
  bannerValue: { fontSize: 14, fontWeight: 700, color: "#001F5B" },
  bannerHint:  { marginLeft: "auto", fontSize: 12, color: "#E38A00", fontWeight: 500 },

  chatWindow: {
    flex: 1, overflowY: "auto",
    background: "#fff", border: "1px solid #DDE3EF",
    borderRadius: 12, padding: 20, marginBottom: 12,
    display: "flex", flexDirection: "column", gap: 14,
    boxShadow: "0 1px 4px rgba(0,31,91,0.05)",
  },
  emptyState: {
    margin: "auto", textAlign: "center", padding: "40px 20px",
  },
  emptyIcon:     { fontSize: 40, marginBottom: 12 },
  emptyTitle:    { fontSize: 16, fontWeight: 700, color: "#001F5B", marginBottom: 6 },
  emptySubtitle: { fontSize: 13, color: "#A0AEC0", marginBottom: 20 },
  suggestions:   { display: "flex", flexDirection: "column", gap: 8, alignItems: "center" },
  suggestionBtn: {
    background: "#F0F4FF", border: "1px solid #C3D3F0",
    borderRadius: 8, padding: "8px 18px",
    fontSize: 13, color: "#0057A8", cursor: "pointer",
    fontFamily: "inherit", fontWeight: 500,
  },

  msgRow: { display: "flex", alignItems: "flex-end", gap: 8 },
  botAvatar: { fontSize: 20, flexShrink: 0, marginBottom: 2 },
  bubble: {
    maxWidth: "72%", padding: "10px 14px",
    borderRadius: 12, fontSize: 14, lineHeight: 1.7,
  },
  bubbleUser: {
    background: "#0057A8", color: "#fff",
    borderBottomRightRadius: 3,
  },
  bubbleBot: {
    background: "#EEF2FA", color: "#1A1A2E",
    borderBottomLeftRadius: 3,
  },
  bubbleError: { background: "#FFF5F5", color: "#C53030" },
  typingDots: { display: "flex", gap: 5, padding: "3px 2px" },
  dot: {
    width: 7, height: 7, borderRadius: "50%",
    background: "#A0AEC0", display: "inline-block",
  },

  inputRow: { display: "flex", gap: 10, alignItems: "flex-end" },
  textarea: {
    flex: 1, padding: "11px 14px",
    border: "1px solid #C3D3F0", borderRadius: 10,
    fontSize: 14, fontFamily: "inherit",
    resize: "none", outline: "none",
    lineHeight: 1.5, color: "#1A1A2E", background: "#fff",
    boxShadow: "0 1px 3px rgba(0,31,91,0.05)",
  },
  sendBtn: {
    width: 44, height: 44,
    background: "#0057A8", color: "#fff",
    border: "none", borderRadius: 10,
    fontSize: 18, cursor: "pointer",
    display: "flex", alignItems: "center", justifyContent: "center",
    flexShrink: 0,
  },
};


// import { useState } from "react";
// import { askPolicy } from "../api/insurix";
// import MessageBubble from "../components/MessageBubble";
// import ChatInput from "../components/ChatInput";
// import ChatWindow from "../components/ChatWindow";
// import { useContext } from "react";
// import { PolicyContext } from "../components/PolicyContext";

// function ChatPage() {
//   //const [policyId, setPolicyId] = useState("1");
//   const [question, setQuestion] = useState("");
//   const [messages, setMessages] = useState([]);
//   const [loading, setLoading] = useState(false);
//   const { policyId } = useContext(PolicyContext);

//   const handleSend = async () => {
//     if (!question.trim()) return;

//     const userMessage = {
//       sender: "user",
//       text: question,
//     };

//     setMessages((prev) => [...prev, userMessage]);

//     try {
//       setLoading(true);
//       const result = await askPolicy(policyId, question);

//       const botMessage = {
//         sender: "bot",
//         text: result.answer || JSON.stringify(result),
//       };

//       setMessages((prev) => [...prev, botMessage]);
//       setLoading(false);
//     } catch (error) {
//       setMessages((prev) => [
//         ...prev,
//         {
//           sender: "bot",
//           text: "Unable to connect to backend.",
//         },
//       ]);
//       setLoading(false);
//       console.error(error);
//     }

//     setQuestion("");
//   };

//   return (
//     <div
//         style={{
//         maxWidth: "1100px",
//         margin: "0 auto",
//         }}
//     >
//       {/* Header */}
//       <div
//         style={{
//           display: "flex",
//           justifyContent: "space-between",
//           alignItems: "center",
//           marginBottom: "20px",
//         }}
//       >
//         <div>
//           <h2>Policy Assistant</h2>
//           <p style={{ color: "gray", marginTop: "5px" }}>
//             Ask questions about your insurance policy
//           </p>
//         </div>

//         <div
//           style={{
//             background: "#e5e7eb",
//             padding: "8px 12px",
//             borderRadius: "8px",
//             fontSize: "14px",
//           }}
//         >
//           Session: user_01
//         </div>
//       </div>

//       {/* Policy Selection */}
//       <div
//         style={{
//             background: "#f3f4f6",
//             padding: "12px",
//             borderRadius: "10px",
//             marginBottom: "15px",
//         }}
//         >
//         Current Policy:

//         <strong>
//             {policyId === "1"
//               ? "CAR-101"
//               : policyId === "2"
//               ? "BIKE-101"
//               : policyId === "3"
//               ? "CAR-102"
//               : ""}
//         </strong>
//       </div>

//       {/* Chat Area */}
//       <ChatWindow
//         messages={messages}
//         loading={loading}
//       />

//       {/* Input Area */}
//       <ChatInput
//         question={question}
//         setQuestion={setQuestion}
//         handleSend={handleSend}
//       />
//     </div>
//   );
// }

// export default ChatPage;