import { Button } from "@/components/ui/button"
import { useClouderPlaylists } from "@/hooks/useClouderPlaylists"
import { moveTrackToPlaylist } from "@/lib/clouderApi"
import type { SpotifyCurrentlyPlaying } from "@/lib/spotify"
import { useState } from "react"
import { cn } from "@/lib/utils"

interface CategoryActionsProps {
  track: SpotifyCurrentlyPlaying | null
  onNext: () => void
}

export function CategoryActions({ track, onNext }: CategoryActionsProps) {
  const { playlists, isLoading, error } = useClouderPlaylists(track)
  const [isMoving, setIsMoving] = useState(false)
  const [highlightedPlaylistId, setHighlightedPlaylistId] = useState<string | null>(null)

  const handleMoveTrack = async (targetPlaylistId: string) => {
    if (!track?.item || !track.context) return

    const sourcePlaylistId = track.context.uri.split(":")[2]
    const trashPlaylist = playlists.find(p => p.name.toLowerCase() === "trash")

    if (!sourcePlaylistId || !trashPlaylist) {
      console.error("Could not determine source or trash playlist.")
      return
    }

    setIsMoving(true)
    try {
      await moveTrackToPlaylist(
        track.item.id,
        sourcePlaylistId,
        targetPlaylistId,
        trashPlaylist.playlist_id
      )
      setHighlightedPlaylistId(targetPlaylistId)
      onNext()
    } catch (e) {
      console.error("Failed to move track:", e)
      // TODO: Show a toast notification to the user
    } finally {
      setIsMoving(false)
    }
  }

  if (isLoading) {
    return <p className="text-center">Loading categories...</p>
  }

  if (error) {
    return <p className="text-center text-destructive">{error}</p>
  }

  if (playlists.length === 0) {
    return null
  }

  return (
    <div className="grid grid-cols-4 gap-2 rounded-md border p-4 mx-auto">
      <div className="col-span-4 flex flex-wrap justify-center gap-2">
        {[...playlists]
          .sort((a, b) => a.name.localeCompare(b.name))
          .slice(0, 8)
          .map(category => (
            <Button
              key={category.playlist_id}
              variant="secondary"
              className={cn("transition-all active:scale-95 hover:opacity-90 w-32 h-10 text-black", highlightedPlaylistId === category.playlist_id && "bg-gray-700 hover:bg-gray-800 text-white")}
              onClick={() => handleMoveTrack(category.playlist_id)}
              disabled={isMoving}
            >
              {category.name}
            </Button>
          ))}
      </div>
    </div>
  )
}
