import { useState, useEffect, useRef } from "react"
import { getClouderWeekForPlaylist, getSpPlaylistsForWeek, type SpPlaylist } from "@/lib/clouderApi"
import type { SpotifyCurrentlyPlaying } from "@/lib/spotify"

export interface CategoryPlaylist {
  name: string
  playlist_id: string
}

export function useClouderPlaylists(track: SpotifyCurrentlyPlaying | null) {
  const [playlists, setPlaylists] = useState<CategoryPlaylist[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const cache = useRef<{ [playlistId: string]: { week: string; categories: CategoryPlaylist[] } }>({})

  useEffect(() => {
    const fetchCategoryPlaylists = async () => {
      if (!track?.context || track.context.type !== "playlist") {
        setPlaylists([])
        return
      }

      const playlistId = track.context.uri.split(":")[2]
      if (!playlistId) {
        setPlaylists([])
        return
      }

      if (cache.current[playlistId]) {
        setPlaylists(cache.current[playlistId].categories)
        return
      }

      setIsLoading(true)
      setError(null)
      setPlaylists([])

      try {
        const weekData = await getClouderWeekForPlaylist(playlistId)
        const clouderWeek = weekData.clouder_week

        if (!clouderWeek) {
          setIsLoading(false)
          return
        }

        const playlistsData: SpPlaylist[] = await getSpPlaylistsForWeek(clouderWeek)

        const categoryObjects = playlistsData.filter(p => p.clouder_pl_type === "category" || p.clouder_pl_name === "trash").map(p => ({ name: p.clouder_pl_name[0].toUpperCase() + p.clouder_pl_name.slice(1), playlist_id: p.playlist_id }))

        cache.current[playlistId] = { week: clouderWeek, categories: categoryObjects }
        setPlaylists(categoryObjects)
      } catch (error) {
        console.error("Failed to fetch category playlists:", error)
        setError("Could not load category playlists.")
      } finally {
        setIsLoading(false)
      }
    }

    fetchCategoryPlaylists()
  }, [track?.context?.uri])

  return { playlists, isLoading, error }
}
