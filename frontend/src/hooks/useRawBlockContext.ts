import { useState, useEffect } from "react"
import { getRawLayerBlocks, type RawLayerPlaylistResponse } from "@/lib/clouderApi"

export interface RawContextActions {
  targetPlaylists: RawLayerPlaylistResponse[]
  trashPlaylist: RawLayerPlaylistResponse | null
  isLoading: boolean
  error: string | null
}

export function useRawBlockContext(currentContextUri: string | null | undefined): RawContextActions {
  const [targetPlaylists, setTargetPlaylists] = useState<RawLayerPlaylistResponse[]>([])
  const [trashPlaylist, setTrashPlaylist] = useState<RawLayerPlaylistResponse | null>(null)
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!currentContextUri) {
      setTargetPlaylists([])
      setTrashPlaylist(null)
      return
    }

    const fetchContext = async () => {
      setIsLoading(true)
      setError(null)
      try {
        // Extract playlist ID from URI (spotify:playlist:ID or spotify:user:USER:playlist:ID)
        const parts = currentContextUri.split(":")
        const contextId = parts[parts.length - 1]

        if (!contextId) {
          setTargetPlaylists([])
          setTrashPlaylist(null)
          return
        }

        // Fetch blocks (assuming page 1 is sufficient for active curation)
        const response = await getRawLayerBlocks()

        // Find the block containing the current playlist
        const activeBlock = response.items.find(block =>
          block.playlists.some(p => p.spotify_playlist_id === contextId)
        )

        if (activeBlock) {
          const targets = activeBlock.playlists.filter(p => p.type === "TARGET")
          const trash = activeBlock.playlists.find(p => p.type === "TRASH") || null

          // Sort targets by category name
          targets.sort((a, b) => (a.category_name || "").localeCompare(b.category_name || ""))

          setTargetPlaylists(targets)
          setTrashPlaylist(trash)
        } else {
          setTargetPlaylists([])
          setTrashPlaylist(null)
        }

      } catch (err) {
        console.error("Failed to resolve raw block context:", err)
        setError("Failed to load curation context")
      } finally {
        setIsLoading(false)
      }
    }

    fetchContext()
  }, [currentContextUri])

  return { targetPlaylists, trashPlaylist, isLoading, error }
}
