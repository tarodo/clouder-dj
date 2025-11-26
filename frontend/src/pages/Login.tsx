import { useEffect } from "react"
import { useNavigate } from "react-router-dom"
import { Button } from "@/components/ui/button"
import { isLoggedIn } from "@/lib/auth"
import { config } from "@/config"

export default function LoginPage() {
  const navigate = useNavigate()

  useEffect(() => {
    if (isLoggedIn()) {
      navigate("/player")
    }
  }, [navigate])

  return (
    <div className="flex min-h-svh flex-col items-center justify-center">
      <Button asChild size="lg">
        <a href={config.spotify.loginUrl}>Login with Spotify</a>
      </Button>
    </div>
  )
}
