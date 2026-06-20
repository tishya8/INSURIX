function MessageBubble({ sender, text }) {
  const isUser = sender === "user";

  return (
    <div
      style={{
        display: "flex",
        justifyContent: isUser
          ? "flex-end"
          : "flex-start",
        marginBottom: "15px",
      }}
    >
      <div
        style={{
          maxWidth: "70%",
          padding: "12px",
          borderRadius: "12px",
          backgroundColor: isUser
            ? "#dbeafe"
            : "#f3f4f6",
          color: "#111827",
        }}
      >
        {text}
      </div>
    </div>
  );
}

export default MessageBubble;