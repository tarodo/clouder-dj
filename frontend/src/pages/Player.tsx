import { useSpotifyPlayer } from "@/hooks/useSpotifyPlayer"
import { TrackInfo } from "@/components/player/TrackInfo"
import { PlayerProgressBar } from "@/components/player/PlayerProgressBar"
import { PlayerControls } from "@/components/player/PlayerControls"
import { CategoryActions } from "@/components/player/CategoryActions"
import { Card, CardContent } from "@/components/ui/card"
import { CurrentContextInfo } from "@/components/player/CurrentContextInfo"
import { useRawBlockContext } from "@/hooks/useRawBlockContext"
import { TrackLikeButton } from "@/components/player/TrackLikeButton"

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

  const { targetPlaylists } = useRawBlockContext(track?.context?.uri)

  const contextUri = track?.context?.uri
  const playlistId = contextUri?.startsWith("spotify:playlist:") ? contextUri.split(":")[2] : null
  const currentTargetPlaylist = playlistId ? targetPlaylists.find(p => p.spotify_playlist_id === playlistId) : null

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
      <Card className="relative">
        {currentTargetPlaylist?.category_id && track?.item?.uri && (
          <div className="absolute top-4 right-4 z-10">
            <TrackLikeButton trackUri={track.item.uri} categoryId={currentTargetPlaylist.category_id} />
          </div>
        )}
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
