import { useState } from "react";
import { askPolicy } from "../api/insurix";
import MessageBubble from "../components/MessageBubble";
import ChatInput from "../components/ChatInput";
import ChatWindow from "../components/ChatWindow";
import { useContext } from "react";
import { PolicyContext } from "../components/PolicyContext";

function ChatPage() {
  //const [policyId, setPolicyId] = useState("1");
  const [question, setQuestion] = useState("");
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(false);
  const { policyId } = useContext(PolicyContext);

  const handleSend = async () => {
    if (!question.trim()) return;

    const userMessage = {
      sender: "user",
      text: question,
    };

    setMessages((prev) => [...prev, userMessage]);

    try {
      setLoading(true);
      const result = await askPolicy(policyId, question);

      const botMessage = {
        sender: "bot",
        text: result.answer || JSON.stringify(result),
      };

      setMessages((prev) => [...prev, botMessage]);
      setLoading(false);
    } catch (error) {
      setMessages((prev) => [
        ...prev,
        {
          sender: "bot",
          text: "Unable to connect to backend.",
        },
      ]);
      setLoading(false);
      console.error(error);
    }

    setQuestion("");
  };

  return (
    <div
        style={{
        maxWidth: "1100px",
        margin: "0 auto",
        }}
    >
      {/* Header */}
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          marginBottom: "20px",
        }}
      >
        <div>
          <h2>Policy Assistant</h2>
          <p style={{ color: "gray", marginTop: "5px" }}>
            Ask questions about your insurance policy
          </p>
        </div>

        <div
          style={{
            background: "#e5e7eb",
            padding: "8px 12px",
            borderRadius: "8px",
            fontSize: "14px",
          }}
        >
          Session: user_01
        </div>
      </div>

      {/* Policy Selection */}
      <div
        style={{
            background: "#f3f4f6",
            padding: "12px",
            borderRadius: "10px",
            marginBottom: "15px",
        }}
        >
        Current Policy:

        <strong>
            {policyId === "1"
            ? " CAR-101"
            : " BIKE-101"}
        </strong>
      </div>

      {/* Chat Area */}
      <ChatWindow
        messages={messages}
        loading={loading}
      />

      {/* Input Area */}
      <ChatInput
        question={question}
        setQuestion={setQuestion}
        handleSend={handleSend}
      />
    </div>
  );
}

export default ChatPage;