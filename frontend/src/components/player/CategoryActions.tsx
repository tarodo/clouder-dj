import { Button } from "@/components/ui/button"
import { useRawBlockContext } from "@/hooks/useRawBlockContext"
import { addTrackToPlaylist, removeTrackFromPlaylist, type SpotifyCurrentlyPlaying } from "@/lib/spotify"
import { cn } from "@/lib/utils"
import { toast } from "sonner"

interface CategoryActionsProps {
  track: SpotifyCurrentlyPlaying | null
  onNext: () => void
}

export function CategoryActions({ track, onNext }: CategoryActionsProps) {
  const { targetPlaylists, trashPlaylist, isLoading, error } = useRawBlockContext(track?.context?.uri)

  const handleMoveTrack = async (targetPlaylistId: string) => {
    if (!track?.item || !track.context) return

    // Extract playlist ID from URI (spotify:playlist:ID or spotify:user:USER:playlist:ID)
    const parts = track.context.uri.split(":")
    const sourcePlaylistId = parts[parts.length - 1]
    const trackUri = track.item.uri

    if (!sourcePlaylistId) {
      toast.error("Could not determine source playlist.")
      return
    }

    try {
      // 1. Add to target
      await addTrackToPlaylist(targetPlaylistId, trackUri)
      // 2. Remove from source
      await removeTrackFromPlaylist(sourcePlaylistId, trackUri)

      toast.success("Track moved")
      onNext()
    } catch (e) {
      console.error("Failed to move track:", e)
      toast.error("Failed to move track")
    } finally {
      // nothing
    }
  }

  if (isLoading) {
    return <p className="text-center text-sm text-muted-foreground mt-4">Loading actions...</p>
  }

  if (error) {
    return null
  }

  if (targetPlaylists.length === 0 && !trashPlaylist) {
    return null
  }

  return (
    <div className="grid grid-cols-4 gap-2 rounded-md border p-4 mx-auto mt-4">
      <div className="col-span-4 flex flex-wrap justify-center gap-2">
        {targetPlaylists.map(playlist => (
          <Button
            key={playlist.spotify_playlist_id}
            variant="secondary"
            className={cn(
              "transition-all active:scale-95 hover:opacity-90 w-32 h-10 text-black active:bg-neutral-800 active:text-white"
            )}
            onClick={() => handleMoveTrack(playlist.spotify_playlist_id)}
          >
            {playlist.category_name || "Unknown"}
          </Button>
        ))}

        {trashPlaylist && (
          <Button
            key={trashPlaylist.spotify_playlist_id}
            variant="secondary"
            className={cn(
              "transition-all active:scale-95 hover:opacity-90 w-32 h-10 text-red-900 bg-red-100 hover:bg-red-200 active:bg-red-300"
            )}
            onClick={() => handleMoveTrack(trashPlaylist.spotify_playlist_id)}
          >
            Skip
          </Button>
        )}
      </div>
    </div>
  )
}
