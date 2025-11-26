import { Link } from "react-router-dom"
import { useQuery } from "@tanstack/react-query"
import { getReleasePlaylists } from "@/lib/clouderApi"
import { Button } from "@/components/ui/button"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import { Skeleton } from "@/components/ui/skeleton"
import { ExternalLink, Play, ListMusic } from "lucide-react"
import { playerPlayContext } from "@/lib/spotify"
import { toast } from "sonner"

export function ReleasePlaylistsTable() {
  const { data: playlists = [], isLoading, error } = useQuery({
    queryKey: ["release-playlists"],
    queryFn: getReleasePlaylists,
  })

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

  if (isLoading) {
    return (
      <div className="space-y-2">
        {[1, 2, 3].map(i => (
          <Skeleton key={i} className="h-10 w-full" />
        ))}
      </div>
    )
  }

  if (error) return <div className="p-8 text-center text-red-500">Failed to load playlists</div>
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
