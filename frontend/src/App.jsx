import React, { useEffect, useState } from "react";
import {
  BrowserRouter,
  Routes,
  Route,
  Navigate,
  useNavigate,
} from "react-router-dom";
import { auth } from "./lib/supabase.js";
import LandingPage from "./pages/LandingPage.jsx";
import AuthPage from "./pages/AuthPage.jsx";
import ChatPage from "./pages/ChatPage.jsx";
// import DashboardPage from "./pages/DashboardPage.jsx";

// Loading screen
function Loading() {
  return (
    <div
      style={{
        minHeight: "100vh",
        background: "var(--bg-primary)",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
      }}
    >
      <div
        style={{
          width: "20px",
          height: "20px",
          border: "2px solid var(--border)",
          borderTopColor: "var(--accent)",
          borderRadius: "50%",
          animation: "spin 0.7s linear infinite",
        }}
      />
    </div>
  );
}

// Main app — manages auth state
function AppInner() {
  const [user, setUser] = useState(undefined); // undefined = loading
  const [checked, setChecked] = useState(false);

  useEffect(() => {
    // Check current session
    auth.getUser().then(({ data }) => {
      setUser(data?.user || null);
      setChecked(true);
    });
    // Listen for auth changes
    const { data: listener } = auth.onAuthChange((_event, session) => {
      setUser(session?.user || null);
    });
    return () => listener?.subscription?.unsubscribe();
  }, []);

  if (!checked) return <Loading />;

  return (
    <Routes>
      {/* Public routes */}
      <Route path="/" element={<LandingPage />} />
      <Route
        path="/auth"
        element={user ? <Navigate to="/chat" /> : <AuthPage />}
      />

      {/* Protected routes — guests still allowed, auth just saves history */}
      <Route path="/chat" element={<ChatPage />} />
      {/* <Route path="/dashboard" element={<DashboardPage />} /> */}

      <Route path="*" element={<Navigate to="/" />} />
    </Routes>
  );
}

export default function App() {
  return (
    <BrowserRouter>
      <AppInner />
    </BrowserRouter>
  );
}
