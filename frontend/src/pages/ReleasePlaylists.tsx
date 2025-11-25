import { useEffect, useState } from "react"
import { Link } from "react-router-dom"
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/card"
import { getReleasePlaylists, type ReleasePlaylistSimple } from "@/lib/clouderApi"
import { Button } from "@/components/ui/button"

export default function ReleasePlaylistsPage() {
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

  if (loading) return <div className="p-8 text-center">Loading playlists...</div>
  if (error) return <div className="p-8 text-center text-red-500">{error}</div>

  return (
    <div className="space-y-6">
      <h1 className="text-3xl font-bold">Release Playlists</h1>
      {playlists.length === 0 ? (
        <p className="text-muted-foreground">No playlists found.</p>
      ) : (
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
                <Button asChild className="w-full">
                  <Link to={`/release-playlists/${playlist.id}`}>View Details</Link>
                </Button>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  )
}
