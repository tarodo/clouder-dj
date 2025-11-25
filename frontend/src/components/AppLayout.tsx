import { useEffect } from "react"
import { Outlet, useNavigate } from "react-router-dom"
import { MainMenu } from "@/components/MainMenu"
import { isLoggedIn } from "@/lib/auth"

export function AppLayout() {
  const navigate = useNavigate()

  useEffect(() => {
    if (!isLoggedIn()) {
      navigate("/")
    }
  }, [navigate])

  if (!isLoggedIn()) {
    return null // or a loading spinner, but redirect will happen
  }

  return (
    <div className="container mx-auto p-4 sm:p-6 lg:p-8">
      <MainMenu />
      <Outlet />
    </div>
  )
}
