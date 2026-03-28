const BASE = import.meta.env.VITE_API_URL || "http://localhost:8000";

async function req(method, path, body = null, isForm = false) {
  const opts = {
    method,
    headers: isForm ? {} : { "Content-Type": "application/json" },
    body: body ? (isForm ? body : JSON.stringify(body)) : null,
  };
  const res = await fetch(`${BASE}${path}`, opts);
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || "Request failed");
  }
  return res.json();
}

export const api = {
  health: () => req("GET", "/health"),
  sendMessage: (sid, msg, mode, iomt) =>
    req("POST", "/chat", {
      session_id: sid,
      message: msg,
      user_mode: mode,
      iomt_data: iomt || null,
    }),
  uploadPDF: (sid, file) => {
    const f = new FormData();
    f.append("file", file);
    return req("POST", `/upload-pdf?session_id=${sid}`, f, true);
  },
  deletePDF: (sid) => req("DELETE", `/pdf?session_id=${sid}`),
  getSession: (sid) => req("GET", `/session?session_id=${sid}`),
  updateProfile: (sid, profile) =>
    req("POST", `/session/profile?session_id=${sid}`, profile),
  setMode: (sid, mode) =>
    req("POST", "/session/mode", { session_id: sid, user_mode: mode }),
  getVitals: (sid) => req("GET", `/vitals?session_id=${sid}`),
  pushVitals: (sid, vitals) =>
    req("POST", "/vitals", { session_id: sid, ...vitals }),
  getHistory: (sid) => req("GET", `/history?session_id=${sid}&limit=50`),
  clearHistory: (sid) => req("DELETE", `/history?session_id=${sid}`),
};

export async function streamMessage(sid, message, mode, onToken, onDone) {
  const res = await fetch(`${BASE}/chat/stream`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ session_id: sid, message, user_mode: mode }),
  });
  if (!res.ok) throw new Error("Stream failed");
  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    const lines = decoder.decode(value).split("\n");
    for (const line of lines) {
      if (!line.startsWith("data: ")) continue;
      const token = line.slice(6);
      if (token === "[DONE]") {
        onDone();
        return;
      }
      if (!token.startsWith("\n\n<!-- model_used:")) onToken(token);
    }
  }
  onDone();
}
