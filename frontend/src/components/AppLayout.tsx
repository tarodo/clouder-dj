import { Outlet } from "react-router-dom"
import { MainMenu } from "@/components/MainMenu"

export function AppLayout() {
  return (
    <div className="container mx-auto p-4 sm:p-6 lg:p-8">
      <MainMenu />
      <Outlet />
    </div>
  )
}
