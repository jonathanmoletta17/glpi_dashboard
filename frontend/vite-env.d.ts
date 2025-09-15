/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_API_BASE_URL: string
  readonly VITE_API_TIMEOUT: string
  readonly VITE_API_RETRY_ATTEMPTS: string
  readonly VITE_API_RETRY_DELAY: string
  // more env variables...
}

interface ImportMeta {
  readonly env: ImportMetaEnv
}