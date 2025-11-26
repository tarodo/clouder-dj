import { useEffect } from "react"
import { useNavigate } from "react-router-dom"
import { clearTokens } from "@/lib/auth"

export default function LogoutPage() {
  const navigate = useNavigate()
  useEffect(() => {
    clearTokens()
    navigate("/")
  }, [navigate])
  return <div>Logging out...</div>
}
