import { useLocation, useNavigate } from "react-router-dom"
import { Menubar, MenubarMenu, MenubarTrigger } from "@/components/ui/menubar"
import { cn } from "@/lib/utils"

const links = [
  { label: "Player", to: "/player" },
  { label: "Playlists", to: "/release-playlists" },
  { label: "Curation", to: "/curation" },
]

export function MainMenu() {
  const location = useLocation()
  const navigate = useNavigate()

  const isActive = (to: string) => location.pathname.startsWith(to)

  const baseItemStyles =
    "w-full min-w-[120px] sm:w-auto flex items-center justify-center rounded-full px-4 py-2 text-xs font-semibold uppercase tracking-[0.35em] transition-colors"
  const activeStyles =
    "bg-[#1f242d] text-white shadow-sm dark:bg-slate-200 dark:text-slate-900"
  const inactiveStyles =
    "bg-transparent text-slate-900 dark:text-slate-100 hover:bg-[#e9ebef] hover:text-slate-900 dark:hover:bg-slate-700/60"
  const activeLogoutStyles = activeStyles
  const inactiveLogoutStyles = inactiveStyles

  return (
    <Menubar className="mb-6 mt-2 h-auto w-full flex-wrap items-center gap-2 rounded-2xl border border-dashed bg-card/50 p-3 text-xs shadow-none text-slate-800 dark:text-slate-100">
      {links.map(({ label, to }) => (
        <MenubarMenu key={to}>
          <MenubarTrigger
            type="button"
            onClick={() => navigate(to)}
            className={cn(baseItemStyles, isActive(to) ? activeStyles : inactiveStyles)}
            aria-current={isActive(to) ? "page" : undefined}
          >
            {label}
          </MenubarTrigger>
        </MenubarMenu>
      ))}
      <div className="hidden flex-1 sm:block" aria-hidden />
      <MenubarMenu>
        <MenubarTrigger
          type="button"
          onClick={() => navigate("/logout")}
          className={cn(baseItemStyles, isActive("/logout") ? activeLogoutStyles : inactiveLogoutStyles)}
          aria-current={isActive("/logout") ? "page" : undefined}
        >
          Logout
        </MenubarTrigger>
      </MenubarMenu>
    </Menubar>
  )
}
