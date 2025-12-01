import { useParams, Link } from "react-router-dom"
import { useQuery } from "@tanstack/react-query"
import { getReleasePlaylist } from "@/lib/clouderApi"
import { Button } from "@/components/ui/button"
import { Skeleton } from "@/components/ui/skeleton"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import { ArrowLeft, ExternalLink } from "lucide-react"
import { formatMsToTime } from "@/lib/utils"

export default function ReleasePlaylistDetailPage() {
  const { id } = useParams<{ id: string }>()
  const { data: playlist, isLoading, error } = useQuery({
    queryKey: ["release-playlist", id],
    queryFn: () => getReleasePlaylist(parseInt(id!, 10)),
    enabled: !!id,
  })

  if (isLoading) {
    return (
      <div className="space-y-4">
        <Skeleton className="h-12 w-1/3" />
        <Skeleton className="h-96 w-full" />
      </div>
    )
  }

  if (error || !playlist) return <div className="p-8 text-center text-red-500">Playlist not found</div>

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-4">
        <Button variant="ghost" size="icon" asChild>
          <Link to="/playlists">
            <ArrowLeft className="size-6" />
          </Link>
        </Button>
        <div>
          <h1 className="text-3xl font-bold">{playlist.name}</h1>
          {playlist.description && <p className="text-muted-foreground">{playlist.description}</p>}
        </div>
        {playlist.spotify_playlist_url && (
          <Button variant="outline" size="icon" asChild className="ml-auto">
            <a href={playlist.spotify_playlist_url} target="_blank" rel="noopener noreferrer">
              <ExternalLink className="size-5" />
            </a>
          </Button>
        )}
      </div>

      <div className="border rounded-md">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead className="w-12 text-center">#</TableHead>
              <TableHead>Title</TableHead>
              <TableHead className="text-right w-20">BPM</TableHead>
              <TableHead className="text-center w-20">Key</TableHead>
              <TableHead className="text-right w-20">Time</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {playlist.tracks.map((item) => (
              <TableRow key={item.track.id}>
                <TableCell className="text-center text-muted-foreground">{item.position + 1}</TableCell>
                <TableCell>
                  <div className="font-medium">{item.track.name}</div>
                  <div className="text-sm text-muted-foreground">{item.track.artists?.map((a) => a.name).join(", ") || ""}</div>
                </TableCell>
                <TableCell className="text-right tabular-nums">{item.track.bpm ? Math.round(item.track.bpm) : "-"}</TableCell>
                <TableCell className="text-center">{item.track.key || "-"}</TableCell>
                <TableCell className="text-right tabular-nums text-muted-foreground">{formatMsToTime(item.track.duration_ms || 0)}</TableCell>
              </TableRow>
            ))}
            {playlist.tracks.length === 0 && (
              <TableRow>
                <TableCell colSpan={5} className="h-24 text-center text-muted-foreground">
                  No tracks in this playlist.
                </TableCell>
              </TableRow>
            )}
          </TableBody>
        </Table>
      </div>
    </div>
  )
}
