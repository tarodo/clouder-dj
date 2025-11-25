import { config } from "@/config"
import { clouderTokenizedFetch } from "./api"

export interface ClouderWeekResponse {
  clouder_week: string
}

export interface SpPlaylist {
  playlist_id: string
  clouder_pl_name: string
  clouder_pl_type: "base" | "category"
  clouder_week: string
  playlist_name: string
}

export async function getClouderWeekForPlaylist(playlistId: string): Promise<ClouderWeekResponse> {
  const response = await fetch(`${config.api.baseUrl}/clouder_playlists/${playlistId}/clouder_week`)
  if (!response.ok) {
    throw new Error("Failed to fetch clouder week")
  }
  return response.json()
}

export async function getSpPlaylistsForWeek(clouderWeek: string): Promise<SpPlaylist[]> {
  const response = await fetch(`${config.api.baseUrl}/clouder_weeks/${clouderWeek}/sp_playlists`)
  if (!response.ok) {
    throw new Error("Failed to fetch playlists for the week")
  }
  return response.json()
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
