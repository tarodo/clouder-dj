import { useQuery } from "@tanstack/react-query"
import { getPlaylist, getPlaylistTracks } from "@/lib/spotify"

export function usePlaylistContext(playlistId: string | undefined, currentTrackUri: string | undefined) {
  return useQuery({
    queryKey: ["playlist-context", playlistId, currentTrackUri],
    queryFn: async () => {
      if (!playlistId || !currentTrackUri) return null

      const [playlist, tracks] = await Promise.all([
        getPlaylist(playlistId),
        getPlaylistTracks(playlistId),
      ])

      const index = tracks.findIndex(item => item.track?.uri === currentTrackUri)

      return {
        name: playlist.name,
        total: playlist.tracks?.total ?? tracks.length,
        currentIndex: index,
      }
    },
    enabled: !!playlistId && !!currentTrackUri,
    staleTime: 1000 * 60 * 5,
  })
}
