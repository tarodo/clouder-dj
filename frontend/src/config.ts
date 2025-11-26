const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000"

export const config = {
  api: {
    baseUrl: API_BASE_URL,
  },
  spotify: {
    loginUrl: `${API_BASE_URL}/auth/login`,
  },
}
