import { useQuery } from "@tanstack/react-query"
import { getStyles } from "@/lib/clouderApi"
import { Button } from "@/components/ui/button"
import { Skeleton } from "@/components/ui/skeleton"
import { cn } from "@/lib/utils"

interface StyleSelectorProps {
  selectedStyleId: number | null
  onSelect: (styleId: number) => void
}

export function StyleSelector({ selectedStyleId, onSelect }: StyleSelectorProps) {
  const { data, isLoading, error } = useQuery({
    queryKey: ["styles"],
    queryFn: getStyles,
  })

  if (isLoading) return <Skeleton className="h-10 w-full" />
  if (error) return <div className="text-red-500">Failed to load styles</div>

  const styles = data?.items || []

  return (
    <div className="flex flex-wrap gap-2">
      {styles.map((style: any) => (
        <Button
          key={style.id}
          variant={selectedStyleId === style.id ? "default" : "outline"}
          onClick={() => onSelect(style.id)}
          className={cn("capitalize")}
        >
          {style.name}
        </Button>
      ))}
    </div>
  )
}
