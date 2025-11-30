import { useState, useEffect } from "react"
import { Heart } from "lucide-react"
import { Button } from "@/components/ui/button"
import { useMutation } from "@tanstack/react-query"
import { addTrackToCategory } from "@/lib/clouderApi"
import { toast } from "sonner"
import { cn } from "@/lib/utils"

interface TrackLikeButtonProps {
  trackUri: string
  categoryId: number
  className?: string
}

export function TrackLikeButton({ trackUri, categoryId, className }: TrackLikeButtonProps) {
  const [isLiked, setIsLiked] = useState(false)

  useEffect(() => {
    setIsLiked(false)
  }, [trackUri])

  const mutation = useMutation({
    mutationFn: () => addTrackToCategory(categoryId, trackUri),
    onSuccess: () => {
      setIsLiked(true)
      toast.success("Track added to category playlist")
    },
    onError: () => {
      toast.error("Failed to add track")
    },
  })

  return (
    <Button
      variant="ghost"
      size="icon"
      className={cn("rounded-full hover:bg-transparent hover:text-primary", className)}
      onClick={() => mutation.mutate()}
      disabled={mutation.isPending || isLiked}
    >
      <Heart
        className={cn("size-6 transition-all", isLiked ? "fill-primary text-primary" : "text-muted-foreground")}
      />
    </Button>
  )
}
