import { createClient } from '@supabase/supabase-js';

const url = import.meta.env.VITE_SUPABASE_URL as string | undefined;
const key = import.meta.env.VITE_SUPABASE_PUBLISHABLE_KEY as string | undefined;

/** False when the env vars are missing; the UI then shows a setup notice instead of crashing. */
export const authConfigured = Boolean(url && key);

// The publishable key is designed to be public; access is enforced by RLS and the API's JWT checks.
export const supabase = createClient(url ?? 'http://localhost', key ?? 'missing', {
  auth: { persistSession: true, autoRefreshToken: true, detectSessionInUrl: true },
});
