import { useEffect, useState } from "react"
import { getRawLayerBlocks, type RawLayerBlockSummary } from "@/lib/clouderApi"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"

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

  if (loading) return <div className="p-8 text-center">Loading blocks...</div>
  if (error) return <div className="p-8 text-center text-red-500">{error}</div>
  if (blocks.length === 0) return <div className="p-8 text-center text-muted-foreground">No raw layer blocks found.</div>

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
      {blocks.map((block) => (
        <Card key={block.id}>
          <CardHeader>
            <div className="flex justify-between items-start">
              <CardTitle className="truncate" title={block.name}>
                {block.name}
              </CardTitle>
              <Badge variant={block.status === "PROCESSED" ? "secondary" : "default"}>
                {block.status}
              </Badge>
            </div>
            <CardDescription>
              {block.start_date} - {block.end_date}
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="flex justify-between text-sm">
              <span className="text-muted-foreground">Tracks</span>
              <span className="font-medium">{block.track_count}</span>
            </div>
            <div className="flex justify-between text-sm mt-1">
              <span className="text-muted-foreground">Playlists</span>
              <span className="font-medium">{block.playlist_count}</span>
            </div>
          </CardContent>
        </Card>
      ))}
    </div>
  )
}
