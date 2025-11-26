import { useQuery } from "@tanstack/react-query"
import { getStyles } from "@/lib/clouderApi"
import { Button } from "@/components/ui/button"
import { Skeleton } from "@/components/ui/skeleton"
import { cn } from "@/lib/utils"

interface StyleSelectorProps {
  selectedStyleId: number | null
  onSelect: (styleId: number) => void
  useBeatportId?: boolean
}

export function StyleSelector({ selectedStyleId, onSelect, useBeatportId = false }: StyleSelectorProps) {
  const { data, isLoading, error } = useQuery({
    queryKey: ["styles"],
    queryFn: getStyles,
  })

  if (isLoading) return <Skeleton className="h-10 w-full" />
  if (error) return <div className="text-red-500">Failed to load styles</div>

  const styles = data?.items || []

  return (
    <div className="flex flex-wrap gap-2">
      {styles.map((style: any) => {
        const styleId = useBeatportId ? style.beatport_style_id : style.id
        if (styleId === null || styleId === undefined) return null

        return (
          <Button
            key={styleId}
            variant={selectedStyleId === styleId ? "default" : "outline"}
            onClick={() => onSelect(styleId)}
            className={cn("capitalize")}
          >
            {style.name}
          </Button>
        )
      })}
    </div>
  )
}
