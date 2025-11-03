/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_API_URL: string;
  readonly VITE_API_TIMEOUT: string;
  readonly VITE_ROBLOX_API_URL: string;
  readonly VITE_WEBSOCKET_URL: string;
  readonly VITE_COPPA_COMPLIANCE: string;
  readonly VITE_FERPA_COMPLIANCE: string;
  readonly VITE_GDPR_COMPLIANCE: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}