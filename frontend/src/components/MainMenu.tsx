import { NavLink } from "react-router-dom"
import { cn } from "@/lib/utils"

const links = [
  { label: "Player", to: "/player" },
  { label: "Playlists", to: "/playlists" },
  { label: "Curation", to: "/curation" },
]

export function MainMenu() {
  return (
    <nav className="flex items-center justify-center p-1 rounded-full border bg-muted/60 max-w-fit mx-auto overflow-x-auto no-scrollbar mb-6 mt-2 gap-1">
      {links.map(({ label, to }) => (
        <NavLink
          key={to}
          to={to}
          className={({ isActive }) =>
            cn(
              "px-4 py-1.5 rounded-full text-xs font-medium transition-all whitespace-nowrap",
              isActive
                ? "bg-background text-foreground shadow-sm"
                : "text-muted-foreground hover:text-foreground hover:bg-muted/50"
            )
          }
        >
          {label}
        </NavLink>
      ))}
      <NavLink
        to="/logout"
        className={({ isActive }) =>
          cn(
            "px-4 py-1.5 rounded-full text-xs font-medium transition-all whitespace-nowrap",
            isActive
              ? "bg-background text-foreground shadow-sm"
              : "text-muted-foreground hover:text-foreground hover:bg-muted/50"
          )
        }
      >
        Logout
      </NavLink>
    </nav>
  )
}
