import React, { useState } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

// ── FORMATTER (🔥 MAIN FIX) ───────────────────────────────────────────────
function formatMedicalResponse(text) {
  if (!text) return "";

  // 1. Clean unwanted ###
  text = text.replace(/###/g, "");

  // 2. Fix spacing
  text = text.replace(/\n+/g, " ");

  // 3. Force line breaks BEFORE bullets
  text = text.replace(/-\s+/g, "\n- ");

  // 4. Force line breaks AFTER full stops
  text = text.replace(/\.\s+/g, ".\n");

  // 5. Fix section titles (VERY IMPORTANT)
  text = text.replace(/Summary\s*-/i, "### 🩺 Summary\n");
  text = text.replace(/What to do\s*-/i, "\n### 🏠 What to do\n");
  text = text.replace(/Medicines\s*-/i, "\n### 💊 Medicines\n");
  text = text.replace(
    /See a doctor if\s*-/i,
    "\n### ⚠️ When to see a doctor\n",
  );

  // 6. Split lines
  const lines = text.split("\n");

  const formatted = lines.map((line) => {
    const clean = line.trim();

    if (!clean) return "";

    // Keep headings
    if (clean.startsWith("###")) return clean;

    // Remove unwanted symbols
    const fixed = clean.replace(/^[-*]\s*/, "");

    return "- " + fixed;
  });

  return formatted.join("\n");
}
// ── Severity badge ────────────────────────────────────────────────────────
function SeverityBadge({ severity }) {
  const cfg = {
    moderate: {
      c: "#f59e0b",
      bg: "rgba(245,158,11,0.08)",
      b: "rgba(245,158,11,0.2)",
      label: "⚠️ Moderate",
    },
    high: {
      c: "#f97316",
      bg: "rgba(249,115,22,0.08)",
      b: "rgba(249,115,22,0.2)",
      label: "🔶 High severity — see a doctor today",
    },
    critical: {
      c: "#ef4444",
      bg: "rgba(239,68,68,0.08)",
      b: "rgba(239,68,68,0.2)",
      label: "🚨 Critical — seek emergency care now",
    },
  }[severity];

  if (!cfg) return null;

  return (
    <div
      style={{
        background: cfg.bg,
        border: `1px solid ${cfg.b}`,
        borderRadius: "8px",
        padding: "0.35rem 0.75rem",
        marginBottom: "0.875rem",
        fontSize: "0.8rem",
        color: cfg.c,
        fontWeight: 600,
      }}
    >
      {cfg.label}
    </div>
  );
}

// ── Copy button ───────────────────────────────────────────────────────────
function CopyBtn({ text }) {
  const [done, setDone] = useState(false);

  const copy = () => {
    navigator.clipboard.writeText(text).then(() => {
      setDone(true);
      setTimeout(() => setDone(false), 2000);
    });
  };

  return (
    <button
      onClick={copy}
      style={{
        background: "transparent",
        border: "none",
        color: done ? "#10b981" : "var(--text-muted)",
        cursor: "pointer",
        fontSize: "0.72rem",
      }}
    >
      {done ? "✓ Copied" : "⎘ Copy"}
    </button>
  );
}

// ── Markdown UI components ────────────────────────────────────────────────
const MD_COMPONENTS = {
  h3: ({ children }) => (
    <div
      style={{
        fontSize: "0.78rem",
        fontWeight: 700,
        color: "var(--accent-light)",
        textTransform: "uppercase",
        margin: "1rem 0 0.4rem",
      }}
    >
      {children}
    </div>
  ),

  p: ({ children }) => (
    <p
      style={{
        margin: "0 0 0.55rem",
        color: "var(--text-secondary)",
        lineHeight: 1.7,
      }}
    >
      {children}
    </p>
  ),

  ul: ({ children }) => (
    <ul
      style={{
        paddingLeft: "1.2rem",
        margin: "0.2rem 0 0.6rem",
      }}
    >
      {children}
    </ul>
  ),

  li: ({ children }) => (
    <li
      style={{
        marginBottom: "4px",
        color: "var(--text-secondary)",
        lineHeight: 1.6,
      }}
    >
      {children}
    </li>
  ),
};

// ── MAIN COMPONENT ────────────────────────────────────────────────────────
export default function MessageBubble({ message }) {
  const isUser = message.role === "user";
  const content = message.content || "";

  if (isUser) {
    return (
      <div style={{ display: "flex", justifyContent: "flex-end" }}>
        <div
          style={{
            background: "var(--accent)",
            color: "#fff",
            borderRadius: "18px",
            padding: "0.7rem 1rem",
            maxWidth: "70%",
          }}
        >
          {content}
        </div>
      </div>
    );
  }

  return (
    <div style={{ display: "flex", gap: "0.6rem" }}>
      {/* Avatar */}
      <div
        style={{
          width: "34px",
          height: "34px",
          borderRadius: "10px",
          background: "#2563eb",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
        }}
      >
        🏥
      </div>

      {/* Message */}
      <div
        style={{
          flex: 1,
          background: "var(--bg-card)",
          border: "1px solid var(--border)",
          borderRadius: "12px",
          padding: "1rem",
        }}
      >
        {/* Severity */}
        {message.severity && <SeverityBadge severity={message.severity} />}

        {/* Clean Markdown Output */}
        <ReactMarkdown remarkPlugins={[remarkGfm]} components={MD_COMPONENTS}>
          {formatMedicalResponse(content)}
        </ReactMarkdown>

        {/* Footer */}
        <div
          style={{
            marginTop: "0.6rem",
            display: "flex",
            justifyContent: "space-between",
            fontSize: "0.7rem",
            color: "gray",
          }}
        >
          <CopyBtn text={content} />
          <span>{new Date(message.timestamp).toLocaleTimeString()}</span>
        </div>
      </div>
    </div>
  );
}
