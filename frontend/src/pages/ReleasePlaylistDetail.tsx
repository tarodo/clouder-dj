import { useEffect, useState } from "react"
import { useParams, Link } from "react-router-dom"
import { getReleasePlaylist, type ReleasePlaylist } from "@/lib/clouderApi"
import { Button } from "@/components/ui/button"
import { ArrowLeft, ExternalLink } from "lucide-react"
import { formatMsToTime } from "@/lib/utils"

export default function ReleasePlaylistDetailPage() {
  const { id } = useParams<{ id: string }>()
  const [playlist, setPlaylist] = useState<ReleasePlaylist | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const fetchPlaylist = async () => {
      if (!id) return
      try {
        const data = await getReleasePlaylist(parseInt(id, 10))
        setPlaylist(data)
      } catch (err) {
        setError("Failed to load playlist details")
        console.error(err)
      } finally {
        setLoading(false)
      }
    }
    fetchPlaylist()
  }, [id])

  if (loading) return <div className="p-8 text-center">Loading details...</div>
  if (error || !playlist) return <div className="p-8 text-center text-red-500">{error || "Playlist not found"}</div>

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-4">
        <Button variant="ghost" size="icon" asChild>
          <Link to="/release-playlists">
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
        <div className="grid grid-cols-[auto_1fr_auto_auto_auto] gap-4 p-4 font-medium border-b bg-muted/50">
          <div className="w-8 text-center">#</div>
          <div>Title</div>
          <div className="text-right w-16">BPM</div>
          <div className="text-center w-16">Key</div>
          <div className="text-right w-16">Time</div>
        </div>
        <div className="divide-y">
          {playlist.tracks.map((item) => (
            <div key={item.track.id} className="grid grid-cols-[auto_1fr_auto_auto_auto] gap-4 p-4 items-center hover:bg-muted/30 transition-colors">
              <div className="w-8 text-center text-muted-foreground">{item.position + 1}</div>
              <div className="min-w-0">
                <div className="font-medium truncate">{item.track.name}</div>
                <div className="text-sm text-muted-foreground truncate">{item.track.artists?.map((a) => a.name).join(", ") || ""}</div>
              </div>
              <div className="text-right w-16 tabular-nums">{item.track.bpm ? Math.round(item.track.bpm) : "-"}</div>
              <div className="text-center w-16">{item.track.key || "-"}</div>
              <div className="text-right w-16 tabular-nums text-muted-foreground">{formatMsToTime(item.track.duration_ms || 0)}</div>
            </div>
          ))}
          {playlist.tracks.length === 0 && <div className="p-8 text-center text-muted-foreground">No tracks in this playlist.</div>}
        </div>
      </div>
    </div>
  )
}
