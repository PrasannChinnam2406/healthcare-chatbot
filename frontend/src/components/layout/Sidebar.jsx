import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useChatStore } from "../../store/chatStore.js";

export default function Sidebar() {
  const { chatHistory, newChat, activePDF, sessionId, loadChat } =
    useChatStore();
  const navigate = useNavigate();
  const [collapsed, setCollapsed] = useState(false);

  const handleNewChat = () => {
    newChat();
    navigate("/chat");
  };

  const handleLoadChat = (historyId) => {
    loadChat(historyId);
    navigate("/chat");
  };

  const W = collapsed ? "52px" : "256px";

  return (
    <div
      style={{
        width: W,
        minWidth: W,
        background: "var(--bg-secondary)",
        borderRight: "1px solid var(--border)",
        display: "flex",
        flexDirection: "column",
        transition: "width 0.2s",
        overflow: "hidden",
        flexShrink: 0,
      }}
    >
      {/* Header */}
      <div
        style={{
          height: "56px",
          display: "flex",
          alignItems: "center",
          justifyContent: collapsed ? "center" : "space-between",
          padding: collapsed ? "0" : "0 0.875rem",
          borderBottom: "1px solid var(--border)",
          flexShrink: 0,
        }}
      >
        {!collapsed && (
          <div
            style={{
              display: "flex",
              alignItems: "center",
              gap: "0.5rem",
              overflow: "hidden",
            }}
          >
            <span style={{ fontSize: "1.1rem", flexShrink: 0 }}>🏥</span>
            <span
              style={{
                fontWeight: 600,
                fontSize: "0.9rem",
                whiteSpace: "nowrap",
              }}
            >
              HealthBot
            </span>
          </div>
        )}
        <button onClick={() => setCollapsed(!collapsed)} style={iconBtn}>
          {collapsed ? "▶" : "◀"}
        </button>
      </div>

      {/* New chat button */}
      <div
        style={{
          padding: collapsed ? "0.5rem 0.375rem" : "0.625rem 0.75rem",
          flexShrink: 0,
        }}
      >
        <button
          onClick={handleNewChat}
          style={{
            width: "100%",
            padding: collapsed ? "0.5rem" : "0.5rem 0.75rem",
            background: "var(--accent-glow)",
            border: "1px solid var(--border-accent)",
            borderRadius: "var(--radius-sm)",
            color: "var(--accent-light)",
            cursor: "pointer",
            fontFamily: "var(--font-main)",
            fontWeight: 500,
            fontSize: "0.82rem",
            display: "flex",
            alignItems: "center",
            justifyContent: collapsed ? "center" : "flex-start",
            gap: "0.4rem",
            transition: "background 0.15s",
            whiteSpace: "nowrap",
          }}
          onMouseEnter={(e) =>
            (e.currentTarget.style.background = "rgba(59,130,246,0.22)")
          }
          onMouseLeave={(e) =>
            (e.currentTarget.style.background = "var(--accent-glow)")
          }
        >
          <span>✏️</span>
          {!collapsed && "New chat"}
        </button>
      </div>

      {/* Active PDF indicator */}
      {!collapsed && activePDF && (
        <div
          style={{
            margin: "0 0.75rem 0.5rem",
            padding: "0.5rem 0.625rem",
            background: "rgba(16,185,129,0.1)",
            border: "1px solid rgba(16,185,129,0.2)",
            borderRadius: "var(--radius-sm)",
            fontSize: "0.75rem",
            color: "#10b981",
            display: "flex",
            alignItems: "center",
            gap: "0.35rem",
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
        </div>
      )}

      {/* Chat history list */}
      {!collapsed && (
        <div style={{ flex: 1, overflowY: "auto", padding: "0.25rem 0.5rem" }}>
          {chatHistory.length > 0 ? (
            <>
              <div
                style={{
                  fontSize: "0.68rem",
                  color: "var(--text-muted)",
                  padding: "0.4rem 0.25rem 0.25rem",
                  textTransform: "uppercase",
                  letterSpacing: "0.07em",
                }}
              >
                Recent chats
              </div>
              {chatHistory.map((item) => (
                <button
                  key={item.id}
                  onClick={() => handleLoadChat(item.id)}
                  style={{
                    width: "100%",
                    padding: "0.5rem 0.5rem",
                    borderRadius: "var(--radius-sm)",
                    cursor: "pointer",
                    fontSize: "0.82rem",
                    color:
                      item.id === sessionId
                        ? "var(--accent-light)"
                        : "var(--text-secondary)",
                    background:
                      item.id === sessionId
                        ? "var(--accent-glow)"
                        : "transparent",
                    border:
                      item.id === sessionId
                        ? "1px solid var(--border-accent)"
                        : "1px solid transparent",
                    overflow: "hidden",
                    textOverflow: "ellipsis",
                    whiteSpace: "nowrap",
                    textAlign: "left",
                    transition: "all 0.12s",
                    fontFamily: "var(--font-main)",
                  }}
                  onMouseEnter={(e) => {
                    if (item.id !== sessionId)
                      e.currentTarget.style.background = "var(--bg-hover)";
                  }}
                  onMouseLeave={(e) => {
                    if (item.id !== sessionId)
                      e.currentTarget.style.background = "transparent";
                  }}
                >
                  💬 {item.preview}
                </button>
              ))}
            </>
          ) : (
            <div
              style={{
                padding: "1rem 0.5rem",
                color: "var(--text-muted)",
                fontSize: "0.8rem",
                textAlign: "center",
                lineHeight: 1.5,
              }}
            >
              Your chat history will appear here
            </div>
          )}
        </div>
      )}

      {/* Bottom nav */}
      <div
        style={{
          borderTop: "1px solid var(--border)",
          padding: collapsed ? "0.5rem 0.375rem" : "0.5rem 0.75rem",
          flexShrink: 0,
        }}
      >
        <button
          onClick={() => navigate("/dashboard")}
          style={{
            width: "100%",
            padding: collapsed ? "0.5rem" : "0.45rem 0.5rem",
            background: "transparent",
            border: "none",
            color: "var(--text-secondary)",
            cursor: "pointer",
            fontFamily: "var(--font-main)",
            fontSize: "0.82rem",
            display: "flex",
            alignItems: "center",
            justifyContent: collapsed ? "center" : "flex-start",
            gap: "0.4rem",
            borderRadius: "var(--radius-sm)",
            transition: "background 0.12s",
            whiteSpace: "nowrap",
          }}
          onMouseEnter={(e) =>
            (e.currentTarget.style.background = "var(--bg-hover)")
          }
          onMouseLeave={(e) =>
            (e.currentTarget.style.background = "transparent")
          }
        >
          <span>📡</span>
          {!collapsed && "Vitals Dashboard"}
        </button>
      </div>
    </div>
  );
}

const iconBtn = {
  background: "transparent",
  border: "none",
  color: "var(--text-muted)",
  cursor: "pointer",
  width: "28px",
  height: "28px",
  borderRadius: "6px",
  display: "flex",
  alignItems: "center",
  justifyContent: "center",
  fontSize: "0.75rem",
  flexShrink: 0,
};
