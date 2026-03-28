import React from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { useChatStore } from "../../store/chatStore.js";

export default function EmergencyAlert() {
  const { emergencyMessage, setEmergency } = useChatStore();

  return (
    <div
      style={{
        position: "fixed",
        inset: 0,
        zIndex: 9999,
        background: "rgba(0,0,0,0.88)",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        padding: "1rem",
        animation: "fadeUp 0.2s ease",
      }}
    >
      <div
        style={{
          background: "#160808",
          border: "2px solid #ef4444",
          borderRadius: "12px",
          padding: "2rem",
          maxWidth: "480px",
          width: "100%",
          boxShadow: "0 0 60px rgba(239,68,68,0.25)",
        }}
      >
        <div
          style={{
            fontSize: "2.5rem",
            textAlign: "center",
            marginBottom: "1rem",
          }}
        >
          🚨
        </div>
        <div className="md" style={{ marginBottom: "1.5rem" }}>
          <ReactMarkdown remarkPlugins={[remarkGfm]}>
            {emergencyMessage || ""}
          </ReactMarkdown>
        </div>
        <div
          style={{
            display: "flex",
            gap: "0.75rem",
            justifyContent: "center",
            flexWrap: "wrap",
          }}
        >
          <a
            href="tel:108"
            style={{
              background: "#ef4444",
              color: "#fff",
              padding: "0.75rem 2rem",
              borderRadius: "8px",
              fontWeight: 700,
              fontSize: "1.05rem",
              textDecoration: "none",
              display: "inline-block",
            }}
          >
            📞 Call 108
          </a>
          <button
            onClick={() => setEmergency(false)}
            style={{
              background: "transparent",
              border: "1px solid rgba(255,255,255,0.15)",
              color: "#94a3b8",
              padding: "0.75rem 1.5rem",
              borderRadius: "8px",
              cursor: "pointer",
              fontFamily: "var(--font-main)",
            }}
          >
            Dismiss
          </button>
        </div>
      </div>
    </div>
  );
}
