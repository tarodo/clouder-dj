import { config } from "@/config"
import { clouderTokenizedFetch } from "./api"

export interface Artist {
  id: number
  name: string
}

export interface Style {
  id: number
  name: string
  beatport_style_id: number | null
}

export interface Category {
  id: number
  name: string
  user_id: number
  style_id: number
  spotify_playlist_id: string
  spotify_playlist_url: string
}

export interface CategoryCreate {
  name: string
  is_public?: boolean
}

export interface CategoryUpdate {
  name: string
}

export interface Track {
  id: number
  name: string
  duration_ms: number | null
  bpm: number | null
  key: string | null
  isrc: string | null
  release_id: number
  artists?: Artist[]
}

export interface ReleasePlaylistTrack {
  position: number
  track: Track
}

export interface ReleasePlaylistSimple {
  id: number
  name: string
  description: string | null
  user_id: number
  spotify_playlist_id: string | null
  spotify_playlist_url: string | null
  track_count: number
}

export interface ReleasePlaylist extends ReleasePlaylistSimple {
  tracks: ReleasePlaylistTrack[]
}

export interface RawLayerPlaylistResponse {
  type: "INBOX_NEW" | "INBOX_OLD" | "INBOX_NOT" | "TRASH" | "TARGET"
  spotify_playlist_id: string
  spotify_playlist_url: string
  category_id: number | null
  category_name: string | null
}

export interface RawLayerBlockSummary {
  id: number
  name: string
  style_id: number
  style_name: string
  status: "NEW" | "PROCESSED"
  start_date: string
  end_date: string
  track_count: number
  playlist_count: number
  playlists: RawLayerPlaylistResponse[]
}

export interface RawLayerBlockResponse {
  id: number
  name: string
  status: "NEW" | "PROCESSED"
  start_date: string
  end_date: string
  playlists: RawLayerPlaylistResponse[]
  track_count: number
}

export interface PaginatedResponse<T> {
  items: T[]
  total: number
}

export interface CollectionStatsStyle {
  id: number
  name: string
  track_count: number
}

export interface CollectionStats {
  total_artists: number
  total_releases: number
  styles: CollectionStatsStyle[]
}

export interface BeatportCollectionRequest {
  bp_token: string
  style_id: number
  date_from: string
  date_to: string
}

export interface RawLayerBlockCreate {
  block_name: string
  start_date: string
  end_date: string
}

export async function moveTrackToPlaylist(trackId: string, sourcePlaylistId: string, targetPlaylistId: string, trashPlaylistId: string): Promise<void> {
  const response = await clouderTokenizedFetch(`${config.api.baseUrl}/clouder_playlists/move_track`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      track_id: trackId,
      source_playlist_id: sourcePlaylistId,
      target_playlist_id: targetPlaylistId,
      trash_playlist_id: trashPlaylistId,
    }),
  })

  if (!response.ok) {
    const errorData = await response
      .json()
      .catch(() => ({}))
    throw new Error(`Failed to move track: ${errorData.detail || response.statusText}`)
  }
}

export async function getReleasePlaylists(): Promise<ReleasePlaylistSimple[]> {
  const response = await clouderTokenizedFetch(`${config.api.baseUrl}/release-playlists`)
  if (!response.ok) {
    throw new Error("Failed to fetch release playlists")
  }
  return response.json()
}

export async function getReleasePlaylist(id: number): Promise<ReleasePlaylist> {
  const response = await clouderTokenizedFetch(`${config.api.baseUrl}/release-playlists/${id}`)
  if (!response.ok) {
    throw new Error("Failed to fetch release playlist")
  }
  return response.json()
}

export async function getRawLayerBlocks(): Promise<PaginatedResponse<RawLayerBlockSummary>> {
  const response = await clouderTokenizedFetch(`${config.api.baseUrl}/curation/raw-blocks`)
  if (!response.ok) {
    throw new Error("Failed to fetch raw layer blocks")
  }
  return response.json()
}

export async function createRawLayerBlock(styleId: number, data: RawLayerBlockCreate): Promise<RawLayerBlockResponse> {
  const response = await clouderTokenizedFetch(`${config.api.baseUrl}/curation/styles/${styleId}/raw-blocks`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  })
  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}))
    throw new Error((errorData as any).detail || "Failed to create raw layer block")
  }
  return response.json()
}

export async function processRawLayerBlock(blockId: number): Promise<RawLayerBlockResponse> {
  const response = await clouderTokenizedFetch(`${config.api.baseUrl}/curation/raw-blocks/${blockId}/process`, {
    method: "POST",
  })
  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}))
    throw new Error((errorData as any).detail || "Failed to process raw layer block")
  }
  return response.json()
}

export async function getStyles(): Promise<PaginatedResponse<Style>> {
  const response = await clouderTokenizedFetch(`${config.api.baseUrl}/styles`)
  if (!response.ok) {
    throw new Error("Failed to fetch styles")
  }
  return response.json()
}

export async function getCategories(styleId: number): Promise<Category[]> {
  const response = await clouderTokenizedFetch(`${config.api.baseUrl}/curation/styles/${styleId}/categories`)
  if (!response.ok) {
    throw new Error("Failed to fetch categories")
  }
  return response.json()
}

export async function createCategory(styleId: number, data: CategoryCreate): Promise<Category[]> {
  const response = await clouderTokenizedFetch(`${config.api.baseUrl}/curation/styles/${styleId}/categories`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify([data]),
  })

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}))
    throw new Error((errorData as any).detail || "Failed to create category")
  }
  return response.json()
}

export async function updateCategory(categoryId: number, data: CategoryUpdate): Promise<Category> {
  const response = await clouderTokenizedFetch(`${config.api.baseUrl}/curation/categories/${categoryId}`, {
    method: "PATCH",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(data),
  })

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}))
    throw new Error((errorData as any).detail || "Failed to update category")
  }
  return response.json()
}

export async function deleteCategory(categoryId: number, deleteOnSpotify: boolean): Promise<void> {
  const response = await clouderTokenizedFetch(`${config.api.baseUrl}/curation/categories/${categoryId}?delete_on_spotify=${deleteOnSpotify}`, {
    method: "DELETE",
  })

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}))
    throw new Error((errorData as any).detail || "Failed to delete category")
  }
}

export async function getCollectionStats(): Promise<CollectionStats> {
  const response = await clouderTokenizedFetch(`${config.api.baseUrl}/collect/stats`)
  if (!response.ok) {
    throw new Error("Failed to fetch collection stats")
  }
  return response.json()
}

export async function triggerBeatportCollection(data: BeatportCollectionRequest): Promise<{ task_id: string }> {
  const response = await clouderTokenizedFetch(`${config.api.baseUrl}/collect/beatport/collect`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(data),
  })

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}))
    throw new Error((errorData as any).detail || "Failed to trigger collection")
  }
  return response.json()
}

export async function triggerSpotifyEnrichment(similarityThreshold: number = 80): Promise<{ task_id: string }> {
  const response = await clouderTokenizedFetch(`${config.api.baseUrl}/collect/spotify/enrich?similarity_threshold=${similarityThreshold}`, {
    method: "POST",
  })
  if (!response.ok) throw new Error("Failed to trigger spotify enrichment")
  return response.json()
}

export async function triggerSpotifyArtistEnrichment(): Promise<{ task_id: string }> {
  const response = await clouderTokenizedFetch(`${config.api.baseUrl}/collect/spotify/enrich-artists`, {
    method: "POST",
  })
  if (!response.ok) throw new Error("Failed to trigger spotify artist enrichment")
  return response.json()
}
