import type { ReactNode } from "react"
import { Navigate } from "react-router-dom"
import { isLoggedIn } from "@/lib/auth"

interface ProtectedRouteProps {
  children: ReactNode
}

export function ProtectedRoute({ children }: ProtectedRouteProps) {
  if (!isLoggedIn()) {
    return <Navigate to="/" replace />
  }

  return <>{children}</>
}
