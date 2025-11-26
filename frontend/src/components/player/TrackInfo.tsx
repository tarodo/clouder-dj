import type { SpotifyCurrentlyPlaying } from "@/lib/spotify"

interface TrackInfoProps {
  track: SpotifyCurrentlyPlaying | null
}

export function TrackInfo({ track }: TrackInfoProps) {
  return (
    <div className="text-center">
      <p className="text-lg font-semibold">{track?.item?.name ?? "No track playing"}</p>
      <p className="text-muted-foreground">{track?.item?.artists.map(a => a.name).join(", ") ?? "-"}</p>
    </div>
  )
}
