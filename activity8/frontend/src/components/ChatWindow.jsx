import { useState, useRef, useEffect } from "react";
import Message from "./Message";
import "./ChatWindow.css";

export default function ChatWindow({ messages, onSend, loading }) {
  const [input, setInput] = useState("");
  const bottomRef = useRef(null);
  const textareaRef = useRef(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  // Auto-resize textarea
  useEffect(() => {
    const el = textareaRef.current;
    if (!el) return;
    el.style.height = "auto";
    el.style.height = Math.min(el.scrollHeight, 120) + "px";
  }, [input]);

  function submit() {
    const text = input.trim();
    if (!text || loading) return;
    setInput("");
    onSend(text);
  }

  function handleKeyDown(e) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      submit();
    }
  }

  return (
    <div className="chat-window">
      <div className="messages">
        {messages.map((msg, i) => (
          <Message key={i} role={msg.role} text={msg.text} chunks_used={msg.chunks_used} />
        ))}
        {loading && (
          <div className="typing-bubble">
            <span /><span /><span />
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      <div className="input-area">
        <div className="input-wrapper">
          <textarea
            ref={textareaRef}
            className="chat-input"
            rows={1}
            placeholder="Ask something about your document…"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            disabled={loading}
          />
          <button
            className="send-btn"
            onClick={submit}
            disabled={loading || !input.trim()}
            title="Send (Enter)"
          >
            ↑
          </button>
        </div>
        <p className="input-hint">Press Enter to send · Shift+Enter for new line</p>
      </div>
    </div>
  );
}
