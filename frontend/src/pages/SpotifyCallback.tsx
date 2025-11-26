import { useEffect } from "react"
import { useNavigate } from "react-router-dom"
import { setTokens } from "@/lib/auth"

export default function SpotifyCallbackPage() {
  const navigate = useNavigate()
  useEffect(() => {
    const params = new URLSearchParams(window.location.search)
    const accessToken = params.get("access_token")
    const refreshToken = params.get("refresh_token")
    const spotifyAccessToken = params.get("spotify_access_token")
    const error = params.get("error")

    if (error) {
      console.error("Spotify login error:", error)
      navigate("/")
      return
    }

    if (accessToken && spotifyAccessToken) {
      setTokens(accessToken, refreshToken, spotifyAccessToken)
      navigate("/player") // Redirect to player after login
    } else {
      navigate("/") // Or back to login on failure
    }
  }, [navigate])
  return (
    <div className="flex min-h-svh flex-col items-center justify-center">
      <p>Completing login...</p>
    </div>
  )
}
