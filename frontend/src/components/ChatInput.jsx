function ChatInput({
  question,
  setQuestion,
  handleSend
}) {
  return (
    <div>
      <textarea
        rows="4"
        style={{
          width: "100%",
          padding: "10px",
          borderRadius: "8px",
          border: "1px solid #ccc",
        }}
        placeholder="Ask a policy question..."
        value={question}
        onChange={(e) =>
          setQuestion(e.target.value)
        }
      />

      <br />
      <br />

      <button
        onClick={handleSend}
        style={{
          background: "#2563eb",
          color: "white",
          border: "none",
          padding: "10px 20px",
          borderRadius: "8px",
          cursor: "pointer",
        }}
      >
        Send
      </button>
    </div>
  );
}

export default ChatInput;