import { useQuery } from "@tanstack/react-query"
import { getAllUserPlaylists } from "@/lib/spotify"
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Skeleton } from "@/components/ui/skeleton"
import { ExternalLink } from "lucide-react"

export function UserPlaylistsList() {
  const { data: playlists = [], isLoading, error } = useQuery({
    queryKey: ["user-playlists"],
    queryFn: getAllUserPlaylists,
  })

  if (isLoading) {
    return (
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {[1, 2, 3].map(i => (
          <Skeleton key={i} className="h-48 w-full" />
        ))}
      </div>
    )
  }

  if (error) return <div className="p-8 text-center text-red-500">Failed to load Spotify playlists</div>
  if (playlists.length === 0) return <div className="p-8 text-center text-muted-foreground">No Spotify playlists found.</div>

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
      {playlists.map((playlist) => (
        <Card key={playlist.id} className="flex flex-col">
          <CardHeader>
            <CardTitle className="truncate" title={playlist.name}>
              {playlist.name}
            </CardTitle>
            <CardDescription className="line-clamp-2 h-10">
              {playlist.description || "No description"}
            </CardDescription>
          </CardHeader>
          <CardContent className="mt-auto pt-0">
            <Button variant="outline" asChild className="w-full">
              <a href={playlist.external_urls.spotify} target="_blank" rel="noopener noreferrer">
                Open in Spotify <ExternalLink className="ml-2 size-4" />
              </a>
            </Button>
          </CardContent>
        </Card>
      ))}
    </div>
  )
}
