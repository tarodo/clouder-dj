import { useEffect, useState } from "react"
import { Link } from "react-router-dom"
import { getReleasePlaylists, type ReleasePlaylistSimple } from "@/lib/clouderApi"
import { Button } from "@/components/ui/button"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import { ExternalLink, Play, ListMusic } from "lucide-react"
import { playerPlayContext } from "@/lib/spotify"
import { toast } from "sonner"

export function ReleasePlaylistsTable() {
  const [playlists, setPlaylists] = useState<ReleasePlaylistSimple[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const fetchPlaylists = async () => {
      try {
        const data = await getReleasePlaylists()
        setPlaylists(data)
      } catch (err) {
        setError("Failed to load playlists")
        console.error(err)
      } finally {
        setLoading(false)
      }
    }
    fetchPlaylists()
  }, [])

  const handlePlay = async (spotifyPlaylistId: string | null) => {
    if (!spotifyPlaylistId) return
    try {
      await playerPlayContext(`spotify:playlist:${spotifyPlaylistId}`)
      toast.success("Playback started")
    } catch (e) {
      console.error(e)
      toast.error("Failed to start playback. Ensure Spotify is active.")
    }
  }

  if (loading) return <div className="p-8 text-center">Loading playlists...</div>
  if (error) return <div className="p-8 text-center text-red-500">{error}</div>
  if (playlists.length === 0) return <div className="p-8 text-center text-muted-foreground">No release playlists found.</div>

  return (
    <div className="rounded-md border">
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>Name</TableHead>
            <TableHead className="w-[100px] text-right">Tracks</TableHead>
            <TableHead className="w-[150px] text-right">Actions</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {playlists.map((playlist) => (
            <TableRow key={playlist.id}>
              <TableCell>
                <div className="font-medium">{playlist.name}</div>
                {playlist.description && <div className="text-sm text-muted-foreground line-clamp-1">{playlist.description}</div>}
              </TableCell>
              <TableCell className="text-right">{playlist.track_count}</TableCell>
              <TableCell className="text-right">
                <div className="flex justify-end gap-2">
                  <Button variant="ghost" size="icon" onClick={() => handlePlay(playlist.spotify_playlist_id)} disabled={!playlist.spotify_playlist_id} title="Play on Spotify">
                    <Play className="size-4" />
                  </Button>
                  <Button variant="ghost" size="icon" asChild title="View Details">
                    <Link to={`/release-playlists/${playlist.id}`}>
                      <ListMusic className="size-4" />
                    </Link>
                  </Button>
                  {playlist.spotify_playlist_url && (
                    <Button variant="ghost" size="icon" asChild title="Open in Spotify">
                      <a href={playlist.spotify_playlist_url} target="_blank" rel="noopener noreferrer">
                        <ExternalLink className="size-4" />
                      </a>
                    </Button>
                  )}
                </div>
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </div>
  )
}
