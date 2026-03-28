import React, { useEffect, useRef } from "react";
import { useChatStore } from "../../store/chatStore.js";
import MessageBubble from "./MessageBubble.jsx";
import SuggestedQuestions from "./SuggestedQuestions.jsx";

const STARTERS = [
  "I have fever, headache and body ache since 2 days",
  "What medicines can I take for cold and cough?",
  "Explain my blood test report",
  "My blood pressure reading is 150/95 mmHg",
];

function StarterCard({ text }) {
  const send = () => {
    window.dispatchEvent(new CustomEvent("hb-send", { detail: text }));
  };
  return (
    <button
      onClick={send}
      style={{
        background: "var(--bg-card)",
        border: "1px solid var(--border)",
        borderRadius: "12px",
        padding: "0.875rem 1rem",
        cursor: "pointer",
        textAlign: "left",
        color: "var(--text-secondary)",
        fontSize: "0.875rem",
        fontFamily: "var(--font-main)",
        lineHeight: 1.5,
        transition: "all 0.15s",
      }}
      onMouseEnter={(e) => {
        e.currentTarget.style.borderColor = "var(--border-accent)";
        e.currentTarget.style.color = "var(--text-primary)";
      }}
      onMouseLeave={(e) => {
        e.currentTarget.style.borderColor = "var(--border)";
        e.currentTarget.style.color = "var(--text-secondary)";
      }}
    >
      {text}
    </button>
  );
}

export default function ChatWindow() {
  const { messages, isLoading, isStreaming, suggestedQuestions } =
    useChatStore();
  const bottomRef = useRef(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isLoading]);

  // Empty state — welcome screen
  if (messages.length === 0) {
    return (
      <div
        style={{
          flex: 1,
          overflowY: "auto",
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          justifyContent: "center",
          padding: "2rem",
          gap: "1.5rem",
        }}
      >
        <div style={{ textAlign: "center", animation: "fadeUp 0.4s ease" }}>
          <div style={{ fontSize: "2.8rem", marginBottom: "0.75rem" }}>🏥</div>
          <h2
            style={{
              fontSize: "1.4rem",
              fontWeight: 600,
              color: "var(--text-primary)",
              marginBottom: "0.4rem",
            }}
          >
            How can I help you today?
          </h2>
          <p style={{ color: "var(--text-secondary)", fontSize: "0.9rem" }}>
            Describe symptoms, upload a report, or ask any health question.
          </p>
        </div>

        <div
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(2,1fr)",
            gap: "0.75rem",
            width: "100%",
            maxWidth: "560px",
            animation: "fadeUp 0.5s ease 0.1s both",
          }}
        >
          {STARTERS.map((s) => (
            <StarterCard key={s} text={s} />
          ))}
        </div>
      </div>
    );
  }

  // Chat messages
  return (
    <div style={{ flex: 1, overflowY: "auto", padding: "1.25rem 1.5rem" }}>
      <div
        style={{
          maxWidth: "760px",
          width: "100%",
          margin: "0 auto",
          display: "flex",
          flexDirection: "column",
          gap: "0.25rem",
        }}
      >
        {messages.map((m) => (
          <MessageBubble key={m.id} message={m} />
        ))}

        {/* Typing indicator */}
        {isLoading && !isStreaming && (
          <div
            style={{
              display: "flex",
              alignItems: "center",
              gap: "0.7rem",
              padding: "0.6rem 0",
              animation: "fadeUp 0.3s ease",
            }}
          >
            <div
              style={{
                width: "32px",
                height: "32px",
                borderRadius: "8px",
                background: "linear-gradient(135deg,#1d4ed8,#3b82f6)",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                flexShrink: 0,
              }}
            >
              🏥
            </div>
            <div style={{ display: "flex", gap: "4px", alignItems: "center" }}>
              {[0, 1, 2].map((i) => (
                <div
                  key={i}
                  style={{
                    width: "7px",
                    height: "7px",
                    borderRadius: "50%",
                    background: "var(--accent)",
                    animation: `pulse 1.4s ease-in-out ${i * 0.2}s infinite`,
                  }}
                />
              ))}
            </div>
          </div>
        )}

        {/* Suggested questions */}
        {!isLoading && !isStreaming && suggestedQuestions.length > 0 && (
          <SuggestedQuestions questions={suggestedQuestions} />
        )}

        <div ref={bottomRef} />
      </div>
    </div>
  );
}
