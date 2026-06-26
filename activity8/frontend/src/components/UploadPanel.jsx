import { useRef, useState } from "react";
import "./UploadPanel.css";

export default function UploadPanel({ onUpload, uploadedFile }) {
  const inputRef = useRef(null);
  const [status, setStatus] = useState(null); // null | "loading" | "success" | "error"
  const [errorMsg, setErrorMsg] = useState("");

  async function handleChange(e) {
    const file = e.target.files[0];
    if (!file) return;
    setStatus("loading");
    setErrorMsg("");
    try {
      await onUpload(file);
      setStatus("success");
    } catch (err) {
      setStatus("error");
      setErrorMsg(err.message);
    }
    e.target.value = "";
  }

  const isLoading = status === "loading";

  return (
    <div className="upload-panel">
      <div
        className={`upload-drop-zone ${isLoading ? "disabled" : ""}`}
        onClick={() => !isLoading && inputRef.current.click()}
      >
        <span className="upload-icon">
          {isLoading ? "⏳" : status === "success" ? "📄" : "📁"}
        </span>
        <span className="upload-label">
          {isLoading ? "Indexing…" : "Choose .txt file"}
        </span>
        <span className="upload-sub">Click to browse</span>
      </div>

      <input
        ref={inputRef}
        type="file"
        accept=".txt"
        style={{ display: "none" }}
        onChange={handleChange}
      />

      {status === "success" && (
        <div className="upload-status success">
          ✓ {uploadedFile}
        </div>
      )}
      {status === "loading" && (
        <div className="upload-status loading">
          Processing file…
        </div>
      )}
      {status === "error" && (
        <div className="upload-status error">
          ✕ {errorMsg}
        </div>
      )}
    </div>
  );
}
