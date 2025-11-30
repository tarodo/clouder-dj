import { useSpotifyPlayer } from "@/hooks/useSpotifyPlayer"
import { TrackInfo } from "@/components/player/TrackInfo"
import { PlayerProgressBar } from "@/components/player/PlayerProgressBar"
import { PlayerControls } from "@/components/player/PlayerControls"
import { CategoryActions } from "@/components/player/CategoryActions"
import { Card, CardContent } from "@/components/ui/card"
import { CurrentContextInfo } from "@/components/player/CurrentContextInfo"

export default function PlayerPage() {
  const {
    track,
    loading,
    error,
    handlePrevious,
    handleNext,
    handlePlayPause,
    handleSeek,
    handleRewind,
    handleFastForward,
  } = useSpotifyPlayer()

  if (loading) {
    return <div className="flex flex-col items-center justify-center pt-10">Loading player...</div>
  }
  if (error) {
    return <div className="flex flex-col items-center justify-center pt-10 text-red-500">{error}</div>
  }
  if (!track) {
    return (
      <div className="flex flex-col items-center justify-center pt-10">
        No track currently playing on Spotify.
      </div>
    )
  }

  return (
    <div className="mt-4 max-w-[36rem] mx-auto">
      <Card>
        <CardContent className="flex flex-col items-center justify-center gap-4">
          <TrackInfo track={track} />
          <PlayerProgressBar track={track} />
          <PlayerControls
            isPlaying={track.is_playing}
            onPlayPause={handlePlayPause}
            onNext={handleNext}
            onPrevious={handlePrevious}
            onRewind={handleRewind}
            onFastForward={handleFastForward}
            onSeek={handleSeek}
            isPlayerActive={!!track.item}
          />
        </CardContent>
      </Card>
      <CurrentContextInfo track={track} />
      <div className="mt-4">
        <CategoryActions track={track} onNext={handleNext} />
      </div>
    </div>
  )
}
