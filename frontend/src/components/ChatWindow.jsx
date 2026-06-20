import MessageBubble from "./MessageBubble";
import { useEffect, useRef } from "react";

function ChatWindow({
  messages,
  loading
}) {

  const bottomRef = useRef(null);

  useEffect(() => {

    bottomRef.current?.scrollIntoView({
      behavior: "smooth"
    });

  }, [messages, loading]);

  return (
    <div
      style={{
        border: "1px solid #ddd",
        borderRadius: "12px",
        height: "60vh",
        overflowY: "auto",
        padding: "20px",
        background: "#fafafa",
        marginBottom: "15px",
      }}
    >
      {messages.length === 0 ? (
        <div
          style={{
            textAlign: "center",
            color: "gray",
            marginTop: "100px",
          }}
        >
          Start a conversation with INSURIX
        </div>
      ) : (
        messages.map((msg, index) => (
          <MessageBubble
            key={index}
            sender={msg.sender}
            text={msg.text}
          />
        ))
      )}

      {loading && (
        <div
          style={{
            marginTop: "15px",
            padding: "10px",
            color: "#6b7280",
            fontStyle: "italic",
            background: "#f3f4f6",
            borderRadius: "8px",
            width: "fit-content",
          }}
        >
          INSURIX is analyzing your request...
        </div>
      )}

      <div ref={bottomRef}></div>

    </div>
  );
}

export default ChatWindow;