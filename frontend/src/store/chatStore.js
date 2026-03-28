import { create } from "zustand";

let _counter = 0;
const uid = () => `msg_${++_counter}_${Date.now()}`;

export const useChatStore = create((set, get) => ({
  sessionId: null,
  userMode: "general",
  messages: [],
  isLoading: false,
  isStreaming: false,
  activePDF: null,
  vitals: null,
  vitalsRisk: "normal",
  chatHistory: [], // [{id, preview, messages, ts}]
  emergencyActive: false,
  emergencyMessage: "",
  suggestedQuestions: [],

  ensureSession: () => {
    const { sessionId } = get();
    if (sessionId) return sessionId;
    const id = crypto.randomUUID();
    set({ sessionId: id });
    return id;
  },

  // Start a new chat — saves current chat to history
  newChat: () => {
    const { messages, sessionId, chatHistory } = get();
    let updatedHistory = chatHistory;

    // Save current chat if it has messages
    if (messages.length > 0 && sessionId) {
      const firstUserMsg = messages.find((m) => m.role === "user");
      const preview = firstUserMsg?.content?.slice(0, 55) || "Chat";
      const existingIdx = chatHistory.findIndex((h) => h.id === sessionId);

      if (existingIdx >= 0) {
        // Update existing entry
        updatedHistory = [...chatHistory];
        updatedHistory[existingIdx] = {
          ...updatedHistory[existingIdx],
          messages,
          preview,
        };
      } else {
        // Add new entry
        updatedHistory = [
          { id: sessionId, preview, messages: [...messages], ts: Date.now() },
          ...chatHistory.slice(0, 19),
        ];
      }
    }

    const newId = crypto.randomUUID();
    set({
      sessionId: newId,
      messages: [],
      activePDF: null,
      suggestedQuestions: [],
      isLoading: false,
      isStreaming: false,
      chatHistory: updatedHistory,
    });
    return newId;
  },

  // Load a previous chat from history
  loadChat: (historyId) => {
    const { messages, sessionId, chatHistory } = get();
    let updatedHistory = chatHistory;

    // Save current chat first
    if (messages.length > 0 && sessionId) {
      const firstUserMsg = messages.find((m) => m.role === "user");
      const preview = firstUserMsg?.content?.slice(0, 55) || "Chat";
      const existingIdx = chatHistory.findIndex((h) => h.id === sessionId);
      if (existingIdx >= 0) {
        updatedHistory = [...chatHistory];
        updatedHistory[existingIdx] = {
          ...updatedHistory[existingIdx],
          messages,
          preview,
        };
      } else {
        updatedHistory = [
          { id: sessionId, preview, messages: [...messages], ts: Date.now() },
          ...chatHistory.slice(0, 19),
        ];
      }
    }

    // Load the selected chat
    const targetChat = updatedHistory.find((h) => h.id === historyId);
    if (!targetChat) return;

    set({
      sessionId: targetChat.id,
      messages: targetChat.messages || [],
      activePDF: null,
      suggestedQuestions: [],
      isLoading: false,
      isStreaming: false,
      chatHistory: updatedHistory,
    });
  },

  setUserMode: (v) => set({ userMode: v }),
  setLoading: (v) => set({ isLoading: v }),
  setStreaming: (v) => set({ isStreaming: v }),
  setPDF: (v) => set({ activePDF: v }),
  clearPDF: () => set({ activePDF: null }),
  setVitals: (v, r = "normal") => set({ vitals: v, vitalsRisk: r }),
  setEmergency: (a, m = "") => set({ emergencyActive: a, emergencyMessage: m }),
  setSuggestedQuestions: (v) => set({ suggestedQuestions: v }),
  clearMessages: () => set({ messages: [], suggestedQuestions: [] }),

  addMessage: (msg) =>
    set((s) => ({
      messages: [
        ...s.messages,
        {
          id: uid(),
          timestamp: new Date().toISOString(),
          sources: [],
          ...msg,
        },
      ],
    })),

  appendToLastMessage: (token) =>
    set((s) => {
      if (!s.messages.length) return {};
      const msgs = [...s.messages];
      const last = msgs[msgs.length - 1];
      msgs[msgs.length - 1] = {
        ...last,
        content: (last.content || "") + token,
      };
      return { messages: msgs };
    }),

  updateLastMeta: (meta) =>
    set((s) => {
      if (!s.messages.length) return {};
      const msgs = [...s.messages];
      msgs[msgs.length - 1] = { ...msgs[msgs.length - 1], ...meta };
      return { messages: msgs };
    }),
}));
