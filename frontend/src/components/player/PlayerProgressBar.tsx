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
      <div className="relative flex-1 group">
        <Progress value={progress} className="w-full" />
        {/* Markers for shortcuts 1-5 (0%, 20%, 40%, 60%, 80%) */}
        {[0, 20, 40, 60, 80].map((percent, index) => (
          <>
            <div
              key={`bottom-${percent}`}
              className="absolute top-2.5 h-1.5 w-0.5 bg-foreground/30 z-10 pointer-events-none group-hover:bg-foreground/50 transition-colors"
              style={{ left: `${percent}%` }}
              title={`Shortcut: ${index + 1}`}
            />
            <div
              key={`top-${percent}`}
              className="absolute -top-2 h-1.5 w-0.5 bg-foreground/30 z-10 pointer-events-none group-hover:bg-foreground/50 transition-colors"
              style={{ left: `${percent}%` }}
              title={`Shortcut: ${index + 1}`}
            />
          </>
        ))}
      </div>
      <span className="text-xs tabular-nums min-w-[36px] text-left">
        {formatMsToTime(track.item.duration_ms)}
      </span>
    </div>
  )
}
