import React from "react";
import { useChatStore } from "../../store/chatStore.js";
import { api } from "../../lib/api.js";

const MODES = [
  { value: "general", label: "General", icon: "👤" },
  { value: "patient", label: "Patient", icon: "🩺" },
  { value: "medical", label: "Medical", icon: "⚕️" },
];

export default function UserModeToggle() {
  const { userMode, setUserMode, sessionId } = useChatStore();

  const change = async (mode) => {
    setUserMode(mode);
    if (sessionId) {
      try {
        await api.setMode(sessionId, mode);
      } catch {}
    }
  };

  return (
    <div
      style={{
        display: "flex",
        background: "var(--bg-card)",
        border: "1px solid var(--border)",
        borderRadius: "8px",
        padding: "3px",
        gap: "2px",
      }}
    >
      {MODES.map((m) => (
        <button
          key={m.value}
          onClick={() => change(m.value)}
          style={{
            padding: "0.28rem 0.7rem",
            borderRadius: "6px",
            border: "none",
            cursor: "pointer",
            fontSize: "0.78rem",
            fontFamily: "var(--font-main)",
            fontWeight: 500,
            transition: "all 0.15s",
            display: "flex",
            alignItems: "center",
            gap: "0.3rem",
            background: userMode === m.value ? "var(--accent)" : "transparent",
            color: userMode === m.value ? "#fff" : "var(--text-muted)",
          }}
        >
          <span style={{ fontSize: "0.8rem" }}>{m.icon}</span>
          {m.label}
        </button>
      ))}
    </div>
  );
}
