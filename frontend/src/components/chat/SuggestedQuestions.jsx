import React from "react";

export default function SuggestedQuestions({ questions }) {
  const send = (q) => {
    window.dispatchEvent(new CustomEvent("hb-send", { detail: q }));
  };

  return (
    <div
      style={{
        display: "flex",
        flexWrap: "wrap",
        gap: "0.45rem",
        paddingLeft: "44px",
        marginTop: "0.5rem",
        animation: "fadeUp 0.3s ease",
      }}
    >
      {questions.slice(0, 4).map((q) => (
        <button
          key={q}
          onClick={() => send(q)}
          style={{
            background: "transparent",
            border: "1px solid var(--border-accent)",
            borderRadius: "20px",
            padding: "0.3rem 0.8rem",
            color: "var(--accent-light)",
            fontSize: "0.8rem",
            cursor: "pointer",
            fontFamily: "var(--font-main)",
            transition: "all 0.15s",
          }}
          onMouseEnter={(e) => {
            e.currentTarget.style.background = "var(--accent-glow)";
            e.currentTarget.style.borderColor = "var(--accent)";
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.background = "transparent";
            e.currentTarget.style.borderColor = "var(--border-accent)";
          }}
        >
          {q}
        </button>
      ))}
    </div>
  );
}
