import { useQuery } from "@tanstack/react-query"
import { getCollectionStats } from "@/lib/clouderApi"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Skeleton } from "@/components/ui/skeleton"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"

export function CollectionStats() {
  const { data, isLoading, error } = useQuery({
    queryKey: ["collection-stats"],
    queryFn: getCollectionStats,
  })

  if (isLoading) return <Skeleton className="h-64 w-full" />
  if (error) return <div className="text-red-500">Failed to load statistics</div>
  if (!data) return null

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-2 gap-4">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">Total Artists</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{data.total_artists.toLocaleString()}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">Total Releases</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{data.total_releases.toLocaleString()}</div>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Tracks per Style</CardTitle>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Style</TableHead>
                <TableHead className="text-right">Tracks</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {data.styles.map((style) => (
                <TableRow key={style.id}>
                  <TableCell className="font-medium">{style.name}</TableCell>
                  <TableCell className="text-right">{style.track_count.toLocaleString()}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardContent>
      </Card>
    </div>
  )
}
