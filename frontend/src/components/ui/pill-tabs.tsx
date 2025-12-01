import * as React from "react"

import { cn } from "@/lib/utils"

const PillTabsContext = React.createContext<{
  value: string
  onValueChange: (value: string) => void
} | null>(null)

const PillTabs = React.forwardRef<
  HTMLDivElement,
  React.HTMLAttributes<HTMLDivElement> & { value: string; onValueChange: (value: string) => void }
>(({ className, value, onValueChange, ...props }, ref) => (
  <PillTabsContext.Provider value={{ value, onValueChange }}>
    <div ref={ref} className={cn("w-full", className)} {...props} />
  </PillTabsContext.Provider>
))
PillTabs.displayName = "PillTabs"

const PillTabsList = React.forwardRef<
  HTMLDivElement,
  React.HTMLAttributes<HTMLDivElement>
>(({ className, ...props }, ref) => (
  <div
    ref={ref}
    className={cn(
      "flex h-auto w-auto max-w-full items-center justify-start sm:justify-center rounded-full bg-muted/60 p-1 overflow-x-auto no-scrollbar mx-auto",
      className
    )}
    {...props}
  />
))
PillTabsList.displayName = "PillTabsList"

const PillTabsTrigger = React.forwardRef<
  HTMLButtonElement,
  React.ButtonHTMLAttributes<HTMLButtonElement> & { value: string }
>(({ className, value, ...props }, ref) => {
  const context = React.useContext(PillTabsContext)
  const isActive = context?.value === value
  return (
    <button
      ref={ref}
      className={cn(
        "inline-flex items-center justify-center whitespace-nowrap rounded-full px-4 py-1.5 text-sm font-medium ring-offset-background transition-all focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50",
        isActive
          ? "bg-background text-foreground shadow-sm"
          : "text-muted-foreground hover:bg-muted/50 hover:text-foreground",
        className
      )}
      onClick={() => context?.onValueChange(value)}
      {...props}
    />
  )
})
PillTabsTrigger.displayName = "PillTabsTrigger"

const PillTabsContent = React.forwardRef<
  HTMLDivElement,
  React.HTMLAttributes<HTMLDivElement> & { value: string }
>(({ className, value, ...props }, ref) => {
  const context = React.useContext(PillTabsContext)
  if (context?.value !== value) return null
  return (
    <div
      ref={ref}
      className={cn(
        "mt-2 ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2",
        className
      )}
      {...props}
    />
  )
})
PillTabsContent.displayName = "PillTabsContent"

export { PillTabs, PillTabsList, PillTabsTrigger, PillTabsContent }
