/**
 * Supabase Client Initialization
 *
 * Provides a singleton Supabase client instance for the React dashboard.
 * Uses environment variables for configuration (VITE_SUPABASE_URL, VITE_SUPABASE_ANON_KEY).
 *
 * @module services/supabase/client
 * @version 1.0.0
 */

import { createClient, SupabaseClient } from '@supabase/supabase-js';

// Environment variables
const supabaseUrl = import.meta.env.VITE_SUPABASE_URL;
const supabaseAnonKey = import.meta.env.VITE_SUPABASE_ANON_KEY;

if (!supabaseUrl || !supabaseAnonKey) {
  throw new Error(
    'Missing Supabase environment variables. Please set VITE_SUPABASE_URL and VITE_SUPABASE_ANON_KEY'
  );
}

/**
 * Singleton Supabase client instance
 *
 * Features:
 * - Browser client with anonymous key (public operations)
 * - Auto-refresh for authentication tokens
 * - Real-time subscriptions enabled
 * - Persistent session in localStorage
 */
export const supabase: SupabaseClient = createClient(supabaseUrl, supabaseAnonKey, {
  auth: {
    autoRefreshToken: true,
    persistSession: true,
    detectSessionInUrl: true,
  },
  realtime: {
    params: {
      eventsPerSecond: 10,
    },
  },
  global: {
    headers: {
      'x-application-name': 'toolboxai-dashboard',
      'x-client-info': 'toolboxai-dashboard/1.0.0',
    },
  },
});

/**
 * Get the current Supabase client instance
 * @returns {SupabaseClient} The Supabase client
 */
export const getSupabaseClient = (): SupabaseClient => {
  return supabase;
};

/**
 * Check if Supabase is properly configured
 * @returns {boolean} True if configured
 */
export const isSupabaseConfigured = (): boolean => {
  return Boolean(supabaseUrl && supabaseAnonKey);
};

/**
 * Get Supabase configuration details (for debugging)
 * @returns {object} Configuration object
 */
export const getSupabaseConfig = (): { url: string; hasAnonKey: boolean } => {
  return {
    url: supabaseUrl || 'Not configured',
    hasAnonKey: Boolean(supabaseAnonKey),
  };
};

export default supabase;
