import { Progress } from "@/components/ui/progress"
import { formatMsToTime } from "@/lib/utils"
import type { SpotifyCurrentlyPlaying } from "@/lib/spotify"

interface PlayerProgressBarProps {
  track: SpotifyCurrentlyPlaying | null
}

export function PlayerProgressBar({ track }: PlayerProgressBarProps) {
  if (!track?.item) {
    return null
  }

  const progress =
    track.item.duration_ms > 0 ? (track.progress_ms / track.item.duration_ms) * 100 : 0

  return (
    <div className="w-full flex items-center gap-2">
      <span className="text-xs tabular-nums min-w-[36px] text-right">
        {formatMsToTime(track.progress_ms)}
      </span>
      <Progress value={progress} className="flex-1" />
      <span className="text-xs tabular-nums min-w-[36px] text-left">
        {formatMsToTime(track.item.duration_ms)}
      </span>
    </div>
  )
}
