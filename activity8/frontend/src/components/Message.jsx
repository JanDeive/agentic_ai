import ReactMarkdown from "react-markdown";
import "./Message.css";

export default function Message({ role, text, chunks_used }) {
  return (
    <div className={`message ${role}`}>
      <span className="message-label">{role === "user" ? "You" : "AI"}</span>
      <div className="bubble">
        {role === "assistant" ? (
          <ReactMarkdown>{text}</ReactMarkdown>
        ) : (
          text
        )}
      </div>
      {role === "assistant" && chunks_used != null && (
        <span className="chunk-badge">
          {chunks_used} chunk{chunks_used !== 1 ? "s" : ""} used
        </span>
      )}
    </div>
  );
}
