import { useQuery } from "@tanstack/react-query"
import { getRawLayerBlocks, type RawLayerPlaylistResponse, type RawLayerBlockSummary } from "@/lib/clouderApi"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Skeleton } from "@/components/ui/skeleton"
import { ExternalLink, Play } from "lucide-react"
import { playerPlayContext } from "@/lib/spotify"
import { toast } from "sonner"
import { CreateRawBlockForm } from "./CreateRawBlockForm"

export function RawLayerList() {
  const { data, isLoading, error } = useQuery({
    queryKey: ["raw-layer-blocks"],
    queryFn: getRawLayerBlocks,
  })

  const blocks = data?.items || []

  // Group blocks by style_name
  const groupedBlocks = blocks.reduce((acc, block) => {
    const style = block.style_name || "Unknown Style"
    if (!acc[style]) {
      acc[style] = []
    }
    acc[style].push(block)
    return acc
  }, {} as Record<string, RawLayerBlockSummary[]>)

  const handlePlay = async (spotifyPlaylistId: string) => {
    try {
      await playerPlayContext(`spotify:playlist:${spotifyPlaylistId}`)
      toast.success("Playback started")
    } catch (e) {
      console.error(e)
      toast.error("Failed to start playback")
    }
  }

  if (isLoading) {
    return (
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {[1, 2, 3].map(i => (
          <Skeleton key={i} className="h-64 w-full" />
        ))}
      </div>
    )
  }

  if (error) return <div className="p-8 text-center text-red-500">Failed to load raw layer blocks</div>

  return (
    <div className="space-y-8">
      <CreateRawBlockForm />

      {blocks.length === 0 && <div className="p-8 text-center text-muted-foreground">No raw layer blocks found.</div>}

      {Object.entries(groupedBlocks).map(([styleName, styleBlocks]) => (
        <div key={styleName} className="space-y-4">
          <h2 className="text-2xl font-bold capitalize">{styleName}</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {styleBlocks.map((block) => (
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
        </div>
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
