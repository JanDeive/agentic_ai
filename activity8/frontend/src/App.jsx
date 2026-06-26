import { useState } from "react";
import UploadPanel from "./components/UploadPanel";
import ChatWindow from "./components/ChatWindow";
import "./App.css";

export default function App() {
  const [messages, setMessages] = useState([
    {
      role: "assistant",
      text: "Hello! Upload a .txt file using the panel on the left, then ask me anything about its contents.",
    },
  ]);
  const [uploadedFile, setUploadedFile] = useState(null);
  const [loading, setLoading] = useState(false);

  async function handleUpload(file) {
    const formData = new FormData();
    formData.append("file", file);

    const res = await fetch("/upload", { method: "POST", body: formData });
    const data = await res.json();

    if (!res.ok) throw new Error(data.detail || "Upload failed");

    setUploadedFile(file.name);
    setMessages([
      {
        role: "assistant",
        text: `✓ "${file.name}" has been indexed into ${data.chunks} chunks. Ask me anything about it.`,
      },
    ]);
  }

  async function handleSend(text) {
    const userMsg = { role: "user", text };
    setMessages((prev) => [...prev, userMsg]);
    setLoading(true);

    try {
      const res = await fetch("/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: text }),
      });
      const data = await res.json();
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          text: data.answer || data.detail || "Something went wrong.",
          chunks_used: data.chunks_used ?? null,
        },
      ]);
    } catch {
      setMessages((prev) => [
        ...prev,
        { role: "assistant", text: "Network error — is the backend running?" },
      ]);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="sidebar-header">
          <div className="logo">
            <div className="logo-icon">⚡</div>
            RAG Chat
          </div>
        </div>

        <div className="sidebar-body">
          <div>
            <p className="sidebar-section-label">Document</p>
            <UploadPanel onUpload={handleUpload} uploadedFile={uploadedFile} />
          </div>

          <div>
            <p className="sidebar-section-label">How it works</p>
            <p className="sidebar-hint">
              Your file is split into chunks, embedded as vectors, and stored locally.
              Each question retrieves the most relevant chunks before generating an answer.
            </p>
          </div>
        </div>

        <div className="sidebar-footer">
          Powered by Gemini · Qdrant
        </div>
      </aside>

      <main className="main">
        <div className="chat-header">
          <div className="chat-header-dot" />
          <span className="chat-header-title">
            {uploadedFile ? uploadedFile : "No document loaded"}
          </span>
          <span className="chat-header-sub">
            {uploadedFile ? "Ready" : "Upload a file to begin"}
          </span>
        </div>

        <ChatWindow messages={messages} onSend={handleSend} loading={loading} />
      </main>
    </div>
  );
}
