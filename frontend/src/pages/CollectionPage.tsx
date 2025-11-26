import { CollectionStats } from "@/components/collection/CollectionStats"
import { BeatportImportForm } from "@/components/collection/BeatportImportForm"
import { SpotifyEnrichmentControl } from "@/components/collection/SpotifyEnrichmentControl"
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"

export default function CollectionPage() {
  return (
    <div className="space-y-6 max-w-6xl mx-auto">
      <div className="flex flex-col gap-2">
        <h1 className="text-3xl font-bold">Collection Management</h1>
        <p className="text-muted-foreground">Ingest data and view database statistics.</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 space-y-6">
          <CollectionStats />
        </div>

        <div className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Beatport Import</CardTitle>
              <CardDescription>Fetch tracks from Beatport API.</CardDescription>
            </CardHeader>
            <CardContent>
              <BeatportImportForm />
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Spotify Enrichment</CardTitle>
              <CardDescription>Match local data with Spotify.</CardDescription>
            </CardHeader>
            <CardContent>
              <SpotifyEnrichmentControl />
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  )
}
