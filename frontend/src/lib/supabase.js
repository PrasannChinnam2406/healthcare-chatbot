import { createClient } from "@supabase/supabase-js";

const SUPABASE_URL = import.meta.env.VITE_SUPABASE_URL;
const SUPABASE_KEY = import.meta.env.VITE_SUPABASE_ANON_KEY;

if (!SUPABASE_URL || !SUPABASE_KEY) {
  console.warn("Supabase env vars not set — auth will not work");
}

export const supabase = createClient(
  SUPABASE_URL || "https://placeholder.supabase.co",
  SUPABASE_KEY || "placeholder",
);

// Auth helpers
export const auth = {
  signUp: (email, password) => supabase.auth.signUp({ email, password }),

  signIn: (email, password) =>
    supabase.auth.signInWithPassword({ email, password }),

  signOut: () => supabase.auth.signOut(),

  getUser: () => supabase.auth.getUser(),

  onAuthChange: (callback) => supabase.auth.onAuthStateChange(callback),
};
