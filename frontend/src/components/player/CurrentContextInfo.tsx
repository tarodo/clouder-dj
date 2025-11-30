import { useRawBlockContext } from "@/hooks/useRawBlockContext"
import { usePlaylistContext } from "@/hooks/usePlaylistContext"
import { Skeleton } from "@/components/ui/skeleton"
import type { SpotifyCurrentlyPlaying } from "@/lib/spotify"

interface CurrentContextInfoProps {
  track: SpotifyCurrentlyPlaying | null
}

export function CurrentContextInfo({ track }: CurrentContextInfoProps) {
  const contextUri = track?.context?.uri
  const currentTrackUri = track?.item?.uri

  const playlistId = contextUri?.startsWith("spotify:playlist:")
    ? contextUri.split(":")[2]
    : undefined

  const { activeBlock, isLoading: isBlockLoading } = useRawBlockContext(contextUri)
  const { data: playlistInfo, isLoading: isPlaylistLoading } = usePlaylistContext(playlistId, currentTrackUri)

  if (!track || !contextUri) return null

  const isLoading = isBlockLoading || isPlaylistLoading

  if (isLoading) {
    return (
      <div className="flex flex-col items-center gap-1 mt-4">
        <Skeleton className="h-4 w-48" />
        <Skeleton className="h-3 w-32" />
      </div>
    )
  }

  return (
    <div className="flex flex-col items-center gap-1 mt-4 text-center">
      {playlistInfo && (
        <div className="text-sm font-medium">
          {playlistInfo.name}
          <span className="text-muted-foreground ml-2">
            {playlistInfo.currentIndex !== -1 ? `${playlistInfo.currentIndex + 1} / ` : ""}
            {playlistInfo.total}
          </span>
        </div>
      )}
      {activeBlock && (
        <div className="text-xs text-muted-foreground">
          {activeBlock.name} • {activeBlock.style_name} • {activeBlock.start_date} - {activeBlock.end_date}
        </div>
      )}
    </div>
  )
}
