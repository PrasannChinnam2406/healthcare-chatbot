import React from "react";
import { useNavigate } from "react-router-dom";
import { useChatStore } from "../store/chatStore.js";

const MODES = [
  {
    value: "general",
    icon: "👤",
    title: "General User",
    desc: "Simple health guidance in plain language",
    color: "#3b82f6",
  },
  {
    value: "patient",
    icon: "🩺",
    title: "Patient Mode",
    desc: "Detailed medicine & care recommendations",
    color: "#10b981",
  },
  {
    value: "medical",
    icon: "⚕️",
    title: "Medical Pro",
    desc: "Clinical terms & differential diagnosis",
    color: "#8b5cf6",
  },
];

const FEATURES = [
  "📄 Upload medical reports",
  "📡 Live IoMT vitals",
  "💊 Medicine prescriptions",
  "🚨 Emergency detection",
  "🎤 Voice input",
  "🌐 Hindi support",
];

export default function LandingPage() {
  const navigate = useNavigate();
  const setUserMode = useChatStore((s) => s.setUserMode);
  const ensureSession = useChatStore((s) => s.ensureSession);

  const goToChat = (mode) => {
    ensureSession();
    setUserMode(mode);
    navigate("/chat");
  };

  const goToAuth = () => navigate("/auth");

  return (
    <div
      style={{
        minHeight: "100vh",
        background: "var(--bg-primary)",
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
        padding: "2rem",
        position: "relative",
        overflow: "hidden",
      }}
    >
      {/* Background glow */}
      <div
        style={{
          position: "absolute",
          top: "-10%",
          left: "50%",
          transform: "translateX(-50%)",
          width: "700px",
          height: "500px",
          background:
            "radial-gradient(circle, rgba(59,130,246,0.07) 0%, transparent 65%)",
          pointerEvents: "none",
        }}
      />

      {/* Logo + title */}
      <div
        style={{
          textAlign: "center",
          marginBottom: "2.5rem",
          animation: "fadeUp 0.4s ease",
        }}
      >
        <div
          style={{
            width: "76px",
            height: "76px",
            background: "linear-gradient(135deg, #1d4ed8 0%, #3b82f6 100%)",
            borderRadius: "22px",
            margin: "0 auto 1.25rem",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            fontSize: "2.2rem",
            boxShadow: "0 0 48px rgba(59,130,246,0.35)",
          }}
        >
          🏥
        </div>

        <h1
          style={{
            fontSize: "clamp(2.2rem, 5vw, 3.2rem)",
            fontWeight: 600,
            color: "var(--text-primary)",
            letterSpacing: "-0.03em",
            marginBottom: "0.75rem",
          }}
        >
          Health<span style={{ color: "var(--accent)" }}>Bot</span>
        </h1>

        <p
          style={{
            color: "var(--text-secondary)",
            fontSize: "1.05rem",
            maxWidth: "480px",
            lineHeight: 1.65,
            margin: "0 auto",
          }}
        >
          AI-powered healthcare assistant with IoMT integration. Symptoms,
          prescriptions, reports — all in one place.
        </p>
      </div>

      {/* Mode cards */}
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(3, 1fr)",
          gap: "0.875rem",
          width: "100%",
          maxWidth: "700px",
          marginBottom: "2rem",
          animation: "fadeUp 0.5s ease 0.1s both",
        }}
      >
        {MODES.map((m) => (
          <ModeCard key={m.value} mode={m} onClick={() => goToChat(m.value)} />
        ))}
      </div>

      {/* CTA buttons */}
      <div
        style={{
          display: "flex",
          gap: "0.875rem",
          flexWrap: "wrap",
          justifyContent: "center",
          animation: "fadeUp 0.5s ease 0.2s both",
        }}
      >
        <button
          onClick={goToAuth}
          style={{
            background: "var(--accent)",
            color: "#fff",
            border: "none",
            borderRadius: "var(--radius)",
            padding: "0.9rem 2rem",
            fontSize: "1rem",
            fontFamily: "var(--font-main)",
            fontWeight: 600,
            cursor: "pointer",
            transition: "all 0.2s",
            boxShadow: "0 0 32px rgba(59,130,246,0.3)",
          }}
          onMouseEnter={(e) => {
            e.currentTarget.style.opacity = "0.88";
            e.currentTarget.style.transform = "translateY(-2px)";
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.opacity = "1";
            e.currentTarget.style.transform = "translateY(0)";
          }}
        >
          Sign up — it's free
        </button>

        <button
          onClick={() => goToChat("general")}
          style={{
            background: "transparent",
            color: "var(--text-secondary)",
            border: "1px solid var(--border)",
            borderRadius: "var(--radius)",
            padding: "0.9rem 2rem",
            fontSize: "1rem",
            fontFamily: "var(--font-main)",
            fontWeight: 500,
            cursor: "pointer",
            transition: "all 0.2s",
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
          Try as guest →
        </button>
      </div>

      {/* Features */}
      <div
        style={{
          display: "flex",
          flexWrap: "wrap",
          gap: "1.25rem",
          justifyContent: "center",
          marginTop: "2.5rem",
          animation: "fadeUp 0.5s ease 0.3s both",
        }}
      >
        {FEATURES.map((f) => (
          <span
            key={f}
            style={{ color: "var(--text-muted)", fontSize: "0.82rem" }}
          >
            {f}
          </span>
        ))}
      </div>
    </div>
  );
}

function ModeCard({ mode, onClick }) {
  const [hovered, setHovered] = React.useState(false);
  return (
    <button
      onClick={onClick}
      onMouseEnter={() => setHovered(true)}
      onMouseLeave={() => setHovered(false)}
      style={{
        background: hovered ? mode.color + "12" : "var(--bg-card)",
        border: `1px solid ${hovered ? mode.color : "var(--border)"}`,
        borderRadius: "var(--radius)",
        padding: "1.5rem 1.25rem",
        cursor: "pointer",
        textAlign: "left",
        color: "var(--text-primary)",
        fontFamily: "var(--font-main)",
        transform: hovered ? "translateY(-3px)" : "translateY(0)",
        transition: "all 0.2s",
      }}
    >
      <div style={{ fontSize: "1.75rem", marginBottom: "0.625rem" }}>
        {mode.icon}
      </div>
      <div
        style={{ fontWeight: 600, marginBottom: "0.3rem", fontSize: "0.95rem" }}
      >
        {mode.title}
      </div>
      <div
        style={{
          color: "var(--text-secondary)",
          fontSize: "0.8rem",
          lineHeight: 1.5,
        }}
      >
        {mode.desc}
      </div>
    </button>
  );
}
