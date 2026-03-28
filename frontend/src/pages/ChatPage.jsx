import React, { useEffect } from "react";
import { useChatStore } from "../store/chatStore.js";
import Sidebar from "../components/layout/Sidebar.jsx";
import Navbar from "../components/layout/Navbar.jsx";
import ChatWindow from "../components/chat/ChatWindow.jsx";
import InputBar from "../components/chat/InputBar.jsx";
import EmergencyAlert from "../components/chat/EmergencyAlert.jsx";

export default function ChatPage() {
  const { sessionId, ensureSession, emergencyActive } = useChatStore();

  useEffect(() => {
    ensureSession();
  }, []);

  return (
    <div
      style={{
        display: "flex",
        height: "100vh",
        background: "var(--bg-primary)",
        overflow: "hidden",
      }}
    >
      {emergencyActive && <EmergencyAlert />}
      <Sidebar />
      <div
        style={{
          flex: 1,
          display: "flex",
          flexDirection: "column",
          overflow: "hidden",
        }}
      >
        <Navbar />
        <ChatWindow />
        <InputBar />
      </div>
    </div>
  );
}
