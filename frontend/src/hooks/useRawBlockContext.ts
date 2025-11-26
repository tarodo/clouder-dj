import { useQuery } from "@tanstack/react-query"
import { getRawLayerBlocks, type RawLayerPlaylistResponse } from "@/lib/clouderApi"

export interface RawContextActions {
  targetPlaylists: RawLayerPlaylistResponse[]
  trashPlaylist: RawLayerPlaylistResponse | null
  isLoading: boolean
  error: string | null
}

export function useRawBlockContext(currentContextUri: string | null | undefined): RawContextActions {
  const { data, isLoading, error } = useQuery({
    queryKey: ["raw-block-context", currentContextUri],
    queryFn: async () => {
      if (!currentContextUri) {
        return { targets: [], trash: null }
      }

      const parts = currentContextUri.split(":")
      const contextId = parts[parts.length - 1]

      if (!contextId) {
        return { targets: [], trash: null }
      }

      const response = await getRawLayerBlocks()
      const activeBlock = response.items.find(block =>
        block.playlists.some(p => p.spotify_playlist_id === contextId)
      )

      if (activeBlock) {
        const targets = activeBlock.playlists.filter(p => p.type === "TARGET")
        const trash = activeBlock.playlists.find(p => p.type === "TRASH") || null
        targets.sort((a, b) => (a.category_name || "").localeCompare(b.category_name || ""))
        return { targets, trash }
      }

      return { targets: [], trash: null }
    },
    enabled: !!currentContextUri,
    staleTime: 1000 * 60 * 5,
  })

  return {
    targetPlaylists: data?.targets || [],
    trashPlaylist: data?.trash || null,
    isLoading,
    error: error ? "Failed to load curation context" : null,
  }
}
