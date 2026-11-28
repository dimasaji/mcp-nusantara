/// <reference types="vite/client" />

interface ImportMetaEnv {
  VITE_NUSANTARA_BACKEND_URL?: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}
