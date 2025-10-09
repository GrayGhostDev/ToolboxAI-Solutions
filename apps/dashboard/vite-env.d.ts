/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly DEV: boolean;
  readonly PROD: boolean;
  readonly VITE_API_BASE_URL?: string;
  readonly VITE_API_TIMEOUT?: string;
  readonly VITE_ROBLOX_API_URL?: string;
  readonly VITE_WS_URL?: string;
  readonly VITE_WEBSOCKET_URL?: string;
  readonly VITE_PUSHER_KEY?: string;
  readonly VITE_PUSHER_CLUSTER?: string;
  readonly VITE_PUSHER_ENABLED?: string;
  readonly VITE_PUSHER_FORCE_TLS?: string;
  readonly VITE_PUSHER_DEBUG?: string;
  readonly VITE_PUSHER_AUTH_ENDPOINT?: string;
  readonly VITE_AUTH_TOKEN_KEY?: string;
  readonly VITE_AUTH_REFRESH_TOKEN_KEY?: string;
  readonly VITE_ROBLOX_UNIVERSE_ID?: string;
  readonly VITE_GOOGLE_CLASSROOM_CLIENT_ID?: string;
  readonly VITE_CANVAS_API_TOKEN?: string;
  readonly VITE_ENABLE_WEBSOCKET?: string;
  readonly VITE_ENABLE_GAMIFICATION?: string;
  readonly VITE_ENABLE_ANALYTICS?: string;
  readonly VITE_COPPA_COMPLIANCE?: string;
  readonly VITE_FERPA_COMPLIANCE?: string;
  readonly VITE_GDPR_COMPLIANCE?: string;
  readonly VITE_DEBUG_MODE?: string;
  readonly VITE_MOCK_API?: string;
  readonly VITE_ENABLE_CLERK_AUTH?: string;
  readonly VITE_CLERK_PUBLISHABLE_KEY?: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}