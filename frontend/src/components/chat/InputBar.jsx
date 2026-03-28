import React, { useState, useRef, useEffect, useCallback } from "react";
import { useChatStore } from "../../store/chatStore.js";
import { api, streamMessage } from "../../lib/api.js";

export default function InputBar() {
  const [text, setText] = useState("");
  const [recording, setRecording] = useState(false);
  const [uploading, setUploading] = useState(false);
  const taRef = useRef(null);
  const fileRef = useRef(null);
  const recRef = useRef(null);

  const {
    sessionId,
    userMode,
    isLoading,
    isStreaming,
    ensureSession,
    addMessage,
    appendToLastMessage,
    updateLastMeta,
    setLoading,
    setStreaming,
    setSuggestedQuestions,
    setPDF,
    setEmergency,
  } = useChatStore();

  // Auto resize textarea
  useEffect(() => {
    if (!taRef.current) return;
    taRef.current.style.height = "auto";
    taRef.current.style.height =
      Math.min(taRef.current.scrollHeight, 180) + "px";
  }, [text]);

  // Send function — wrapped in useCallback so event listener always has fresh ref
  const sendMessage = useCallback(
    async (msgOverride) => {
      const msg = (typeof msgOverride === "string" ? msgOverride : text).trim();
      if (!msg) return;
      if (useChatStore.getState().isLoading) return;

      setText("");

      const sid =
        useChatStore.getState().sessionId ||
        useChatStore.getState().ensureSession();
      const mode = useChatStore.getState().userMode || "general";

      useChatStore.getState().setLoading(true);
      useChatStore.getState().addMessage({ role: "user", content: msg });
      useChatStore
        .getState()
        .addMessage({ role: "assistant", content: "", streaming: true });
      useChatStore.getState().setStreaming(true);

      try {
        // Stream tokens in real time
        await streamMessage(
          sid,
          msg,
          mode,
          (token) => useChatStore.getState().appendToLastMessage(token),
          () => {},
        );

        // After streaming done, get full metadata
        const result = await api.sendMessage(sid, msg, mode);

        useChatStore.getState().updateLastMeta({
          streaming: false,
          severity: result.severity || "low",
          sources: result.sources || [],
          isEmergency: result.is_emergency || false,
          hasPrescription: result.has_prescription || false,
          modelUsed: result.model_used || "",
        });

        if (result.is_emergency) {
          useChatStore.getState().setEmergency(true, result.response);
        }

        useChatStore
          .getState()
          .setSuggestedQuestions(result.suggested_questions || []);
      } catch (err) {
        console.error("Send error:", err);
        useChatStore.getState().updateLastMeta({
          content: `❌ Connection error: ${err.message}\n\nPlease make sure the backend server is running on port 8000.`,
          streaming: false,
        });
      } finally {
        useChatStore.getState().setLoading(false);
        useChatStore.getState().setStreaming(false);
      }
    },
    [text],
  );

  // Listen for starter/suggestion clicks
  useEffect(() => {
    const handler = (e) => sendMessage(e.detail);
    window.addEventListener("hb-send", handler);
    return () => window.removeEventListener("hb-send", handler);
  }, [sendMessage]);

  const handleKey = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  // Voice input
  const handleVoice = () => {
    const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SR) {
      alert("Voice input not supported in this browser. Please use Chrome.");
      return;
    }

    if (recording) {
      recRef.current?.stop();
      setRecording(false);
      return;
    }

    const r = new SR();
    r.lang = "en-IN";
    r.interimResults = false;
    recRef.current = r;
    setRecording(true);
    r.start();
    r.onresult = (e) => {
      setText(e.results[0][0].transcript);
      setRecording(false);
    };
    r.onerror = () => setRecording(false);
    r.onend = () => setRecording(false);
  };

  // File upload
  const handleFile = async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;

    const sid = ensureSession();
    setUploading(true);

    try {
      const res = await api.uploadPDF(sid, file);
      setPDF({
        filename: res.filename,
        chunkCount: res.chunk_count,
        pageCount: res.page_count,
      });
      addMessage({
        role: "assistant",
        content: `✅ **${res.filename}** uploaded and indexed.\n\n📄 ${res.page_count} page(s), ${res.chunk_count} sections ready.\n\nYou can now ask any question about this document and I will answer from it.`,
      });
    } catch (err) {
      addMessage({
        role: "assistant",
        content: `❌ Upload failed: ${err.message}`,
      });
    } finally {
      setUploading(false);
      e.target.value = "";
    }
  };

  const busy = isLoading || isStreaming;

  return (
    <div
      style={{
        padding: "0.75rem 1.25rem 1rem",
        background: "var(--bg-primary)",
        borderTop: "1px solid var(--border)",
        flexShrink: 0,
      }}
    >
      <div style={{ maxWidth: "760px", margin: "0 auto" }}>
        <div
          style={{
            display: "flex",
            alignItems: "flex-end",
            gap: "0.4rem",
            background: "var(--bg-card)",
            border: `1px solid ${busy ? "var(--border)" : "var(--border-accent)"}`,
            borderRadius: "14px",
            padding: "0.5rem",
            transition: "border-color 0.2s",
          }}
        >
          {/* Attach file */}
          <button
            onClick={() => fileRef.current?.click()}
            disabled={busy || uploading}
            title="Upload PDF / DOCX health report"
            style={btnSt(busy || uploading)}
          >
            {uploading ? "⏳" : "📎"}
          </button>
          <input
            ref={fileRef}
            type="file"
            accept=".pdf,.docx,.doc,.txt"
            onChange={handleFile}
            style={{ display: "none" }}
          />

          {/* Text input */}
          <textarea
            ref={taRef}
            value={text}
            onChange={(e) => setText(e.target.value)}
            onKeyDown={handleKey}
            disabled={busy}
            rows={1}
            placeholder="Describe symptoms, ask a question, or upload a report..."
            style={{
              flex: 1,
              background: "transparent",
              border: "none",
              outline: "none",
              resize: "none",
              color: "var(--text-primary)",
              fontSize: "0.91rem",
              fontFamily: "var(--font-main)",
              lineHeight: 1.6,
              padding: "0.35rem 0.25rem",
              minHeight: "36px",
              maxHeight: "180px",
              overflowY: "auto",
            }}
          />

          {/* Voice */}
          <button
            onClick={handleVoice}
            disabled={busy}
            title="Voice input (Chrome only)"
            style={{
              ...btnSt(busy),
              color: recording ? "#ef4444" : "var(--text-muted)",
              animation: recording ? "pulse 1s infinite" : "none",
            }}
          >
            🎤
          </button>

          {/* Send */}
          <button
            onClick={() => sendMessage()}
            disabled={busy || !text.trim()}
            style={{
              width: "36px",
              height: "36px",
              borderRadius: "10px",
              border: "none",
              background:
                busy || !text.trim() ? "var(--bg-hover)" : "var(--accent)",
              color: "#fff",
              cursor: busy || !text.trim() ? "not-allowed" : "pointer",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              fontSize: "1rem",
              transition: "all 0.15s",
              flexShrink: 0,
            }}
          >
            {busy ? (
              <div
                style={{
                  width: "14px",
                  height: "14px",
                  border: "2px solid rgba(255,255,255,0.3)",
                  borderTopColor: "#fff",
                  borderRadius: "50%",
                  animation: "spin 0.7s linear infinite",
                }}
              />
            ) : (
              "↑"
            )}
          </button>
        </div>

        <p
          style={{
            textAlign: "center",
            fontSize: "0.7rem",
            color: "var(--text-muted)",
            marginTop: "0.4rem",
          }}
        >
          Enter to send · Shift+Enter for new line · 📎 upload health reports
        </p>
      </div>
    </div>
  );
}

const btnSt = (disabled) => ({
  width: "36px",
  height: "36px",
  background: "transparent",
  border: "none",
  color: "var(--text-muted)",
  cursor: disabled ? "not-allowed" : "pointer",
  borderRadius: "8px",
  fontSize: "1.05rem",
  display: "flex",
  alignItems: "center",
  justifyContent: "center",
  transition: "background 0.15s",
  flexShrink: 0,
});
