import {
  Menubar,
  MenubarMenu,
  MenubarTrigger,
} from "@/components/ui/menubar"
import { NavLink } from "react-router-dom"
import { cn } from "@/lib/utils"

export function MainMenu() {
  return (
    <Menubar className="mb-4 max-w-[36rem] mx-auto w-full items-center gap-2">
      <MenubarMenu>
        <MenubarTrigger asChild className="cursor-pointer">
          <NavLink to="/player" className={({ isActive }) => cn(isActive && "text-primary font-semibold")}>
            Player
          </NavLink>
        </MenubarTrigger>
      </MenubarMenu>
      <MenubarMenu>
        <MenubarTrigger asChild className="cursor-pointer">
          <NavLink to="/release-playlists" className={({ isActive }) => cn(isActive && "text-primary font-semibold")}>
            Playlists
          </NavLink>
        </MenubarTrigger>
      </MenubarMenu>
      <MenubarMenu>
        <MenubarTrigger asChild className="cursor-pointer">
          <NavLink to="/categories" className={({ isActive }) => cn(isActive && "text-primary font-semibold")}>
            Categories
          </NavLink>
        </MenubarTrigger>
      </MenubarMenu>
      <MenubarMenu>
        <MenubarTrigger asChild className="cursor-pointer">
          <NavLink to="/collection" className={({ isActive }) => cn(isActive && "text-primary font-semibold")}>
            Collection
          </NavLink>
        </MenubarTrigger>
      </MenubarMenu>
      <div className="flex-1" />
      <MenubarMenu>
        <MenubarTrigger asChild className="cursor-pointer">
          <NavLink to="/logout" className={({ isActive }) => cn(isActive && "text-primary font-semibold")}>
            Logout
          </NavLink>
        </MenubarTrigger>
      </MenubarMenu>
    </Menubar>
  )
}
