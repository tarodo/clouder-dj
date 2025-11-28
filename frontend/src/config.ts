const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL ??
  (import.meta.env.DEV ? "http://127.0.0.1:8000" : "/api")

export const config = {
  api: {
    baseUrl: API_BASE_URL,
  },
  spotify: {
    loginUrl: `${API_BASE_URL}/auth/login`,
  },
}
