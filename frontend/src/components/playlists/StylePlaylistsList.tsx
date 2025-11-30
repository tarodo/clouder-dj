import { useQuery } from "@tanstack/react-query"
import { getAllCategories, type CategoryWithStyle } from "@/lib/clouderApi"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Skeleton } from "@/components/ui/skeleton"
import { ExternalLink, Play } from "lucide-react"
import { playerPlayContext } from "@/lib/spotify"
import { toast } from "sonner"

export function StylePlaylistsList() {
  const { data: categories = [], isLoading, error } = useQuery({
    queryKey: ["all-categories"],
    queryFn: getAllCategories,
  })

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
      <div className="space-y-4">
        {[1, 2, 3].map(i => (
          <Skeleton key={i} className="h-20 w-full" />
        ))}
      </div>
    )
  }

  if (error) return <div className="p-8 text-center text-red-500">Failed to load categories</div>
  if (categories.length === 0) return <div className="p-8 text-center text-muted-foreground">No categorized playlists found.</div>

  // Group by style
  const grouped = categories.reduce((acc, cat) => {
    const style = cat.style_name || "Unknown"
    if (!acc[style]) acc[style] = []
    acc[style].push(cat)
    return acc
  }, {} as Record<string, CategoryWithStyle[]>)

  return (
    <div className="space-y-8">
      {Object.entries(grouped).map(([styleName, styleCategories]) => (
        <Card key={styleName}>
          <CardHeader className="pb-3">
            <CardTitle className="text-lg tracking-wide">
              {styleName.toUpperCase()}
            </CardTitle>
          </CardHeader>
          <CardContent className="pt-0">
            <div className="divide-y">
              {styleCategories.map((category) => (
                <div
                  key={category.id}
                  className="flex flex-col gap-3 py-3 first:pt-0 last:pb-0 sm:flex-row sm:items-center sm:justify-between"
                >
                  <div className="flex-1 truncate">
                    <p className="font-medium truncate" title={category.name}>
                      {category.name}
                    </p>
                  </div>
                  <div className="flex gap-1 sm:gap-2">
                    <Button
                      variant="ghost"
                      size="icon"
                      onClick={() => handlePlay(category.spotify_playlist_id)}
                      title="Play"
                    >
                      <Play className="size-4" />
                    </Button>
                    <Button variant="ghost" size="icon" asChild title="Open in Spotify">
                      <a href={category.spotify_playlist_url} target="_blank" rel="noopener noreferrer">
                        <ExternalLink className="size-4" />
                      </a>
                    </Button>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      ))}
    </div>
  )
}
