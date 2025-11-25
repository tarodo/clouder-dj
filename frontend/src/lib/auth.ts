const ACCESS_TOKEN_KEY = "spotify_access_token"
const REFRESH_TOKEN_KEY = "spotify_refresh_token"
const SPOTIFY_ACCESS_TOKEN_KEY = "spotify_raw_access_token"

export function getAccessToken(): string | null {
  return localStorage.getItem(ACCESS_TOKEN_KEY)
}

export function getSpotifyToken(): string | null {
  return localStorage.getItem(SPOTIFY_ACCESS_TOKEN_KEY)
}

export function getRefreshToken(): string | null {
  return localStorage.getItem(REFRESH_TOKEN_KEY)
}

export function setTokens(accessToken: string, refreshToken?: string | null, spotifyToken?: string | null): void {
  localStorage.setItem(ACCESS_TOKEN_KEY, accessToken)
  if (refreshToken) {
    localStorage.setItem(REFRESH_TOKEN_KEY, refreshToken)
  }
  if (spotifyToken) {
    localStorage.setItem(SPOTIFY_ACCESS_TOKEN_KEY, spotifyToken)
  }
}

export function clearTokens(): void {
  localStorage.removeItem(ACCESS_TOKEN_KEY)
  localStorage.removeItem(REFRESH_TOKEN_KEY)
  localStorage.removeItem(SPOTIFY_ACCESS_TOKEN_KEY)
}

export function isLoggedIn(): boolean {
  return getAccessToken() !== null
}
