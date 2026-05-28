const DEFAULT_API_BASE_URL = "";

export const REGUTHINK_API_BASE_URL =
  typeof import.meta.env.VITE_REGUTHINK_API_BASE_URL === "string"
    ? import.meta.env.VITE_REGUTHINK_API_BASE_URL.trim()
    : DEFAULT_API_BASE_URL;