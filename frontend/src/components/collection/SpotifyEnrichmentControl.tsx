import { useMutation } from "@tanstack/react-query"
import { triggerSpotifyEnrichment, triggerSpotifyArtistEnrichment } from "@/lib/clouderApi"
import { Button } from "@/components/ui/button"
import { toast } from "sonner"
import { RefreshCw, Users } from "lucide-react"

export function SpotifyEnrichmentControl() {
  const tracksMutation = useMutation({
    mutationFn: () => triggerSpotifyEnrichment(80),
    onSuccess: () => toast.success("Track enrichment task started"),
    onError: () => toast.error("Failed to start track enrichment"),
  })

  const artistsMutation = useMutation({
    mutationFn: () => triggerSpotifyArtistEnrichment(),
    onSuccess: () => toast.success("Artist enrichment task started"),
    onError: () => toast.error("Failed to start artist enrichment"),
  })

  return (
    <div className="space-y-4">
      <Button
        variant="outline"
        className="w-full justify-start"
        onClick={() => tracksMutation.mutate()}
        disabled={tracksMutation.isPending}
      >
        <RefreshCw className={`mr-2 size-4 ${tracksMutation.isPending ? "animate-spin" : ""}`} />
        Enrich Tracks (Spotify)
      </Button>

      <Button
        variant="outline"
        className="w-full justify-start"
        onClick={() => artistsMutation.mutate()}
        disabled={artistsMutation.isPending}
      >
        <Users className={`mr-2 size-4 ${artistsMutation.isPending ? "animate-spin" : ""}`} />
        Enrich Artists (Spotify)
      </Button>
    </div>
  )
}
