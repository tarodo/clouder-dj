import { useEffect, useState } from "react"
import { getRawLayerBlocks, type RawLayerBlockSummary, type RawLayerPlaylistResponse } from "@/lib/clouderApi"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { ExternalLink, Play } from "lucide-react"
import { playerPlayContext } from "@/lib/spotify"
import { toast } from "sonner"

export function RawLayerList() {
  const [blocks, setBlocks] = useState<RawLayerBlockSummary[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const fetchBlocks = async () => {
      try {
        const response = await getRawLayerBlocks()
        setBlocks(response.items)
      } catch (err) {
        setError("Failed to load raw layer blocks")
        console.error(err)
      } finally {
        setLoading(false)
      }
    }
    fetchBlocks()
  }, [])

  const handlePlay = async (spotifyPlaylistId: string) => {
    try {
      await playerPlayContext(`spotify:playlist:${spotifyPlaylistId}`)
      toast.success("Playback started")
    } catch (e) {
      console.error(e)
      toast.error("Failed to start playback")
    }
  }

  if (loading) return <div className="p-8 text-center">Loading blocks...</div>
  if (error) return <div className="p-8 text-center text-red-500">{error}</div>
  if (blocks.length === 0) return <div className="p-8 text-center text-muted-foreground">No raw layer blocks found.</div>

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
      {blocks.map((block) => (
        <Card key={block.id} className="flex flex-col">
          <CardHeader className="pb-3">
            <div className="flex justify-between items-start">
              <CardTitle className="truncate" title={block.name}>
                {block.name}
              </CardTitle>
              <Badge variant={block.status === "PROCESSED" ? "secondary" : "outline"}>
                {block.status}
              </Badge>
            </div>
            <CardDescription>
              {block.start_date} - {block.end_date}
            </CardDescription>
            <div className="flex gap-4 text-xs text-muted-foreground mt-1">
              <span>{block.track_count} Tracks</span>
              <span>{block.playlist_count} Playlists</span>
            </div>
          </CardHeader>
          <CardContent className="flex-1 flex flex-col gap-4">
            <PlaylistSection
              title="System"
              playlists={block.playlists.filter(p => p.type !== "TARGET")}
              onPlay={handlePlay}
            />
            <PlaylistSection
              title="Targets"
              playlists={block.playlists.filter(p => p.type === "TARGET")}
              onPlay={handlePlay}
            />
          </CardContent>
        </Card>
      ))}
    </div>
  )
}

function PlaylistSection({ title, playlists, onPlay }: { title: string, playlists: RawLayerPlaylistResponse[], onPlay: (id: string) => void }) {
  if (playlists.length === 0) return null
  return (
    <div>
      <h4 className="text-sm font-semibold mb-2 text-muted-foreground">{title}</h4>
      <div className="space-y-1">
        {playlists.map(p => (
          <div key={p.spotify_playlist_id} className="flex items-center justify-between group">
            <div className="flex items-center gap-2 overflow-hidden">
              <Button variant="ghost" size="icon" className="h-6 w-6" onClick={() => onPlay(p.spotify_playlist_id)}>
                <Play className="size-3" />
              </Button>
              <span className="text-sm truncate" title={getPlaylistName(p)}>
                {getPlaylistName(p)}
              </span>
            </div>
            <a href={p.spotify_playlist_url} target="_blank" rel="noopener noreferrer" className="text-muted-foreground hover:text-foreground p-1">
              <ExternalLink className="size-3" />
            </a>
          </div>
        ))}
      </div>
    </div>
  )
}

function getPlaylistName(p: RawLayerPlaylistResponse): string {
  if (p.type === "TARGET") return p.category_name || "Unknown Category"
  if (p.type === "INBOX_NEW") return "Inbox New"
  if (p.type === "INBOX_OLD") return "Inbox Old"
  if (p.type === "INBOX_NOT") return "Inbox Not"
  if (p.type === "TRASH") return "Trash"
  return p.type
}
