import {
  Menubar,
  MenubarMenu,
  MenubarTrigger,
} from "@/components/ui/menubar"
import { NavLink } from "react-router-dom"
import { cn } from "@/lib/utils"

export function MainMenu() {
  return (
    <Menubar className="mb-4 max-w-[36rem] mx-auto">
      <MenubarMenu>
        <MenubarTrigger asChild className="cursor-pointer">
          <NavLink to="/player" className={({ isActive }) => cn(isActive && "text-primary font-semibold")}>
            Player
          </NavLink>
        </MenubarTrigger>
      </MenubarMenu>
      <MenubarMenu>
        <MenubarTrigger asChild className="cursor-pointer">
          <NavLink to="/logout">Logout</NavLink>
        </MenubarTrigger>
      </MenubarMenu>
    </Menubar>
  )
}
