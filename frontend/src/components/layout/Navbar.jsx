import React, { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useChatStore } from "../../store/chatStore.js";
import { api } from "../../lib/api.js";
import { auth } from "../../lib/supabase.js";
import UserModeToggle from "./UserModeToggle.jsx";

export default function Navbar() {
  const { activePDF, clearPDF, sessionId, vitalsRisk } = useChatStore();
  const navigate = useNavigate();
  const [user, setUser] = useState(null);
  const [showMenu, setShowMenu] = useState(false);

  useEffect(() => {
    auth.getUser().then(({ data }) => setUser(data?.user || null));
    const { data: sub } = auth.onAuthChange((_e, session) => {
      setUser(session?.user || null);
    });
    return () => sub?.subscription?.unsubscribe();
  }, []);

  const handleClearPDF = async () => {
    if (sessionId) {
      try {
        await api.deletePDF(sessionId);
      } catch {}
    }
    clearPDF();
  };

  const handleSignOut = async () => {
    await auth.signOut();
    setShowMenu(false);
    navigate("/");
  };

  const riskClr =
    {
      normal: "#10b981",
      warning: "#f59e0b",
      critical: "#ef4444",
    }[vitalsRisk] || "#10b981";

  return (
    <div
      style={{
        height: "56px",
        display: "flex",
        alignItems: "center",
        justifyContent: "space-between",
        padding: "0 1.25rem",
        borderBottom: "1px solid var(--border)",
        background: "var(--bg-secondary)",
        gap: "1rem",
        flexShrink: 0,
        position: "relative",
      }}
    >
      {/* Left: model badge */}
      <div
        style={{
          fontSize: "0.78rem",
          color: "var(--text-muted)",
          display: "flex",
          alignItems: "center",
          gap: "0.4rem",
          whiteSpace: "nowrap",
          minWidth: "100px",
        }}
      >
        <span
          style={{
            width: "6px",
            height: "6px",
            borderRadius: "50%",
            background: "#10b981",
            display: "inline-block",
            flexShrink: 0,
          }}
        />
        LLaMA 3.3 · 70B
      </div>

      {/* Centre: mode toggle */}
      <UserModeToggle />

      {/* Right: badges + user */}
      <div
        style={{
          display: "flex",
          alignItems: "center",
          gap: "0.625rem",
          minWidth: "100px",
          justifyContent: "flex-end",
        }}
      >
        {/* Active PDF badge */}
        {activePDF && (
          <div
            style={{
              display: "flex",
              alignItems: "center",
              gap: "0.35rem",
              background: "rgba(16,185,129,0.1)",
              border: "1px solid rgba(16,185,129,0.25)",
              borderRadius: "20px",
              padding: "0.2rem 0.625rem",
              fontSize: "0.73rem",
              color: "#10b981",
              maxWidth: "150px",
            }}
          >
            <span>📄</span>
            <span
              style={{
                overflow: "hidden",
                textOverflow: "ellipsis",
                whiteSpace: "nowrap",
              }}
            >
              {activePDF.filename}
            </span>
            <button
              onClick={handleClearPDF}
              style={{
                background: "none",
                border: "none",
                color: "#10b981",
                cursor: "pointer",
                padding: 0,
                fontSize: "0.82rem",
                lineHeight: 1,
                flexShrink: 0,
              }}
            >
              ✕
            </button>
          </div>
        )}

        {/* Vitals risk badge */}
        {vitalsRisk !== "normal" && (
          <div
            style={{
              display: "flex",
              alignItems: "center",
              gap: "0.35rem",
              background: `${riskClr}15`,
              border: `1px solid ${riskClr}40`,
              borderRadius: "20px",
              padding: "0.2rem 0.625rem",
              fontSize: "0.73rem",
              color: riskClr,
              whiteSpace: "nowrap",
            }}
          >
            <span>📡</span>
            {vitalsRisk === "critical" ? "🚨 Critical" : "⚠️ Warning"}
          </div>
        )}

        {/* User menu */}
        {user ? (
          <div style={{ position: "relative" }}>
            <button
              onClick={() => setShowMenu(!showMenu)}
              style={{
                width: "32px",
                height: "32px",
                borderRadius: "50%",
                background: "var(--accent)",
                border: "none",
                cursor: "pointer",
                color: "#fff",
                fontWeight: 700,
                fontSize: "0.82rem",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                flexShrink: 0,
              }}
            >
              {user.email?.[0]?.toUpperCase() || "U"}
            </button>

            {showMenu && (
              <>
                {/* Backdrop */}
                <div
                  style={{ position: "fixed", inset: 0, zIndex: 99 }}
                  onClick={() => setShowMenu(false)}
                />
                {/* Dropdown */}
                <div
                  style={{
                    position: "absolute",
                    right: 0,
                    top: "40px",
                    zIndex: 100,
                    background: "var(--bg-card)",
                    border: "1px solid var(--border)",
                    borderRadius: "10px",
                    minWidth: "200px",
                    boxShadow: "0 8px 32px rgba(0,0,0,0.5)",
                    overflow: "hidden",
                  }}
                >
                  <div
                    style={{
                      padding: "0.75rem 1rem",
                      borderBottom: "1px solid var(--border)",
                    }}
                  >
                    <div
                      style={{
                        fontSize: "0.72rem",
                        color: "var(--text-muted)",
                        marginBottom: "0.2rem",
                      }}
                    >
                      Signed in as
                    </div>
                    <div
                      style={{
                        fontSize: "0.82rem",
                        color: "var(--text-primary)",
                        overflow: "hidden",
                        textOverflow: "ellipsis",
                        whiteSpace: "nowrap",
                      }}
                    >
                      {user.email}
                    </div>
                  </div>
                  <button
                    onClick={handleSignOut}
                    style={{
                      width: "100%",
                      padding: "0.625rem 1rem",
                      background: "transparent",
                      border: "none",
                      color: "#ef4444",
                      cursor: "pointer",
                      fontFamily: "var(--font-main)",
                      fontSize: "0.82rem",
                      textAlign: "left",
                      transition: "background 0.12s",
                    }}
                    onMouseEnter={(e) =>
                      (e.currentTarget.style.background = "rgba(239,68,68,0.1)")
                    }
                    onMouseLeave={(e) =>
                      (e.currentTarget.style.background = "transparent")
                    }
                  >
                    Sign out
                  </button>
                </div>
              </>
            )}
          </div>
        ) : (
          <button
            onClick={() => navigate("/auth")}
            style={{
              background: "transparent",
              border: "1px solid var(--border-accent)",
              borderRadius: "20px",
              padding: "0.25rem 0.875rem",
              color: "var(--accent-light)",
              fontSize: "0.78rem",
              fontFamily: "var(--font-main)",
              cursor: "pointer",
              transition: "all 0.15s",
              whiteSpace: "nowrap",
            }}
            onMouseEnter={(e) =>
              (e.currentTarget.style.background = "var(--accent-glow)")
            }
            onMouseLeave={(e) =>
              (e.currentTarget.style.background = "transparent")
            }
          >
            Sign in
          </button>
        )}
      </div>
    </div>
  );
}
