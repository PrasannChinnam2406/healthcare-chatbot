import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import { auth } from "../lib/supabase.js";

export default function AuthPage() {
  const [mode, setMode] = useState("login"); // login | signup
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [name, setName] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setSuccess("");
    setLoading(true);

    try {
      if (mode === "signup") {
        const { error: err } = await auth.signUp(email, password);
        if (err) throw err;
        setSuccess(
          "Account created! Check your email to confirm, then log in.",
        );
        setMode("login");
      } else {
        const { error: err } = await auth.signIn(email, password);
        if (err) throw err;
        navigate("/chat");
      }
    } catch (err) {
      setError(err.message || "Something went wrong. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  // Guest access — skip auth
  const continueAsGuest = () => navigate("/chat");

  return (
    <div
      style={{
        minHeight: "100vh",
        background: "var(--bg-primary)",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        padding: "1.5rem",
        position: "relative",
        overflow: "hidden",
      }}
    >
      {/* Background glow */}
      <div
        style={{
          position: "absolute",
          top: "-15%",
          left: "50%",
          transform: "translateX(-50%)",
          width: "600px",
          height: "500px",
          background:
            "radial-gradient(circle, rgba(59,130,246,0.07) 0%, transparent 65%)",
          pointerEvents: "none",
        }}
      />

      <div
        style={{
          width: "100%",
          maxWidth: "420px",
          background: "var(--bg-card)",
          border: "1px solid var(--border)",
          borderRadius: "16px",
          padding: "2.5rem 2rem",
          animation: "fadeUp 0.4s ease",
        }}
      >
        {/* Logo */}
        <div style={{ textAlign: "center", marginBottom: "2rem" }}>
          <div
            style={{
              width: "56px",
              height: "56px",
              background: "linear-gradient(135deg,#1d4ed8,#3b82f6)",
              borderRadius: "14px",
              margin: "0 auto 1rem",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              fontSize: "1.6rem",
              boxShadow: "0 0 28px rgba(59,130,246,0.3)",
            }}
          >
            🏥
          </div>
          <h1
            style={{
              fontSize: "1.5rem",
              fontWeight: 600,
              marginBottom: "0.25rem",
            }}
          >
            {mode === "login" ? "Welcome back" : "Create account"}
          </h1>
          <p style={{ color: "var(--text-secondary)", fontSize: "0.875rem" }}>
            {mode === "login"
              ? "Sign in to HealthBot"
              : "Start your free HealthBot account"}
          </p>
        </div>

        {/* Form */}
        <form
          onSubmit={handleSubmit}
          style={{ display: "flex", flexDirection: "column", gap: "0.875rem" }}
        >
          {mode === "signup" && (
            <div>
              <label style={labelStyle}>Full Name</label>
              <input
                type="text"
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="Your name"
                required={mode === "signup"}
                style={inputStyle}
                onFocus={(e) => (e.target.style.borderColor = "var(--accent)")}
                onBlur={(e) => (e.target.style.borderColor = "var(--border)")}
              />
            </div>
          )}

          <div>
            <label style={labelStyle}>Email address</label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="you@example.com"
              required
              style={inputStyle}
              onFocus={(e) => (e.target.style.borderColor = "var(--accent)")}
              onBlur={(e) => (e.target.style.borderColor = "var(--border)")}
            />
          </div>

          <div>
            <label style={labelStyle}>Password</label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder={
                mode === "signup" ? "Min 6 characters" : "Your password"
              }
              required
              minLength={6}
              style={inputStyle}
              onFocus={(e) => (e.target.style.borderColor = "var(--accent)")}
              onBlur={(e) => (e.target.style.borderColor = "var(--border)")}
            />
          </div>

          {/* Error / Success messages */}
          {error && (
            <div
              style={{
                background: "rgba(239,68,68,0.1)",
                border: "1px solid rgba(239,68,68,0.25)",
                borderRadius: "var(--radius-sm)",
                padding: "0.625rem 0.875rem",
                color: "#ef4444",
                fontSize: "0.82rem",
              }}
            >
              ⚠️ {error}
            </div>
          )}
          {success && (
            <div
              style={{
                background: "rgba(16,185,129,0.1)",
                border: "1px solid rgba(16,185,129,0.25)",
                borderRadius: "var(--radius-sm)",
                padding: "0.625rem 0.875rem",
                color: "#10b981",
                fontSize: "0.82rem",
              }}
            >
              ✅ {success}
            </div>
          )}

          {/* Submit */}
          <button
            type="submit"
            disabled={loading}
            style={{
              width: "100%",
              padding: "0.8rem",
              background: loading ? "var(--bg-hover)" : "var(--accent)",
              color: "#fff",
              border: "none",
              borderRadius: "var(--radius-sm)",
              fontSize: "0.95rem",
              fontFamily: "var(--font-main)",
              fontWeight: 600,
              cursor: loading ? "not-allowed" : "pointer",
              transition: "opacity 0.2s",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              gap: "0.5rem",
            }}
          >
            {loading && (
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
            )}
            {loading
              ? "Please wait..."
              : mode === "login"
                ? "Sign in"
                : "Create account"}
          </button>
        </form>

        {/* Divider */}
        <div
          style={{
            display: "flex",
            alignItems: "center",
            gap: "0.75rem",
            margin: "1.25rem 0",
            color: "var(--text-muted)",
            fontSize: "0.8rem",
          }}
        >
          <div
            style={{ flex: 1, height: "1px", background: "var(--border)" }}
          />
          or
          <div
            style={{ flex: 1, height: "1px", background: "var(--border)" }}
          />
        </div>

        {/* Guest button */}
        <button
          onClick={continueAsGuest}
          style={{
            width: "100%",
            padding: "0.75rem",
            background: "transparent",
            border: "1px solid var(--border)",
            borderRadius: "var(--radius-sm)",
            color: "var(--text-secondary)",
            fontSize: "0.875rem",
            fontFamily: "var(--font-main)",
            cursor: "pointer",
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
          Continue as Guest →
        </button>

        {/* Toggle mode */}
        <p
          style={{
            textAlign: "center",
            marginTop: "1.25rem",
            fontSize: "0.85rem",
            color: "var(--text-secondary)",
          }}
        >
          {mode === "login"
            ? "Don't have an account? "
            : "Already have an account? "}
          <button
            onClick={() => {
              setMode(mode === "login" ? "signup" : "login");
              setError("");
              setSuccess("");
            }}
            style={{
              background: "none",
              border: "none",
              color: "var(--accent-light)",
              cursor: "pointer",
              fontFamily: "var(--font-main)",
              fontSize: "0.85rem",
              fontWeight: 600,
              padding: 0,
            }}
          >
            {mode === "login" ? "Sign up" : "Sign in"}
          </button>
        </p>

        {/* Terms */}
        <p
          style={{
            textAlign: "center",
            marginTop: "1rem",
            fontSize: "0.72rem",
            color: "var(--text-muted)",
            lineHeight: 1.5,
          }}
        >
          For informational purposes only. Not a substitute for professional
          medical advice.
        </p>
      </div>
    </div>
  );
}

const labelStyle = {
  display: "block",
  fontSize: "0.8rem",
  color: "var(--text-secondary)",
  marginBottom: "0.35rem",
  fontWeight: 500,
};

const inputStyle = {
  width: "100%",
  padding: "0.65rem 0.875rem",
  background: "var(--bg-secondary)",
  border: "1px solid var(--border)",
  borderRadius: "var(--radius-sm)",
  color: "var(--text-primary)",
  fontSize: "0.9rem",
  fontFamily: "var(--font-main)",
  outline: "none",
  transition: "border-color 0.15s",
};
