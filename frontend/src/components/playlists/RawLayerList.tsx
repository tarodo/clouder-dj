import { useState } from "react"
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { getRawLayerBlocks, processRawLayerBlock, type RawLayerPlaylistResponse, type RawLayerBlockSummary } from "@/lib/clouderApi"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Skeleton } from "@/components/ui/skeleton"
import { ChevronDown, ChevronLeft, ChevronRight, ExternalLink, Loader2, Play } from "lucide-react"
import { playerPlayContext } from "@/lib/spotify"
import { cn } from "@/lib/utils"
import { toast } from "sonner"
import { CreateRawBlockForm } from "./CreateRawBlockForm"

const BLOCKS_PER_PAGE = 3

export function RawLayerList() {
  const { data, isLoading, error } = useQuery({
    queryKey: ["raw-layer-blocks"],
    queryFn: getRawLayerBlocks,
  })
  const queryClient = useQueryClient()
  const [processingBlockId, setProcessingBlockId] = useState<number | null>(null)
  const [pageByStyle, setPageByStyle] = useState<Record<string, number>>({})

  const processMutation = useMutation({
    mutationFn: (blockId: number) => processRawLayerBlock(blockId),
    onMutate: (blockId: number) => {
      setProcessingBlockId(blockId)
    },
    onSuccess: () => {
      toast.success("Raw layer block processed")
      queryClient.invalidateQueries({ queryKey: ["raw-layer-blocks"] })
    },
    onError: (err: any) => {
      toast.error(err?.message || "Failed to process block")
    },
    onSettled: () => {
      setProcessingBlockId(null)
    },
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

  const handleProcess = (blockId: number) => {
    processMutation.mutate(blockId)
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

      {Object.entries(groupedBlocks).map(([styleName, styleBlocks]) => {
        const pages = chunkArray(styleBlocks, BLOCKS_PER_PAGE)
        const totalPages = Math.max(pages.length, 1)
        const currentPage = Math.min(pageByStyle[styleName] ?? 0, totalPages - 1)
        const canPrev = currentPage > 0
        const canNext = currentPage < totalPages - 1

        const setPage = (nextPage: number) => {
          setPageByStyle(prev => ({ ...prev, [styleName]: nextPage }))
        }

        return (
          <div key={styleName} className="space-y-4">
            <div className="flex items-center justify-between gap-4">
              <h2 className="text-2xl font-bold capitalize">{styleName}</h2>
              {totalPages > 1 && (
                <span className="text-xs uppercase tracking-wide text-muted-foreground">
                  Page {currentPage + 1} / {totalPages}
                </span>
              )}
            </div>

            <div className="relative group">
              <div className="overflow-hidden rounded-xl border border-border/60 bg-background/40">
                <div
                  className="flex transition-transform duration-300 ease-out touch-pan-x"
                  style={{ transform: `translateX(-${currentPage * 100}%)` }}
                >
                  {pages.map((pageBlocks, pageIndex) => (
                    <div key={`${styleName}-page-${pageIndex}`} className="w-full shrink-0 px-1 py-4">
                      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                        {pageBlocks.map((block) => (
                          <Card key={block.id} className="flex flex-col border border-border/60 shadow-none bg-background/80">
                            <CardHeader className="pb-4 space-y-4">
                              <div className="flex items-start justify-between gap-3">
                                <div className="space-y-1">
                                  <CardTitle className="truncate text-base font-semibold" title={block.name}>
                                    {block.name}
                                  </CardTitle>
                                  <CardDescription className="text-xs">
                                    {block.start_date} — {block.end_date}
                                  </CardDescription>
                                </div>
                                <div className="flex items-center gap-2">
                                  {block.status === "NEW" && (
                                    <Button
                                      size="sm"
                                      variant="ghost"
                                      disabled={processMutation.isPending}
                                      onClick={() => handleProcess(block.id)}
                                      className="gap-2"
                                    >
                                      {processMutation.isPending && processingBlockId === block.id ? (
                                        <>
                                          <Loader2 className="size-3 animate-spin" />
                                          Processing
                                        </>
                                      ) : (
                                        "Process"
                                      )}
                                    </Button>
                                  )}
                                  <Badge variant={block.status === "PROCESSED" ? "secondary" : "outline"} className="uppercase tracking-wide">
                                    {block.status}
                                  </Badge>
                                </div>
                              </div>
                              <div className="flex flex-wrap gap-2 text-xs text-muted-foreground">
                                <StatChip label="Tracks" value={block.track_count} />
                                <StatChip label="Playlists" value={block.playlist_count} />
                                <StatChip label="Block ID" value={`#${block.id}`} />
                              </div>
                            </CardHeader>
                            <CardContent className="flex-1 pt-0">
                              <PlaylistAccordion
                                sections={[
                                  { key: `system-${block.id}`, title: "System", playlists: block.playlists.filter(p => p.type !== "TARGET") },
                                  { key: `targets-${block.id}`, title: "Targets", playlists: block.playlists.filter(p => p.type === "TARGET") },
                                ]}
                                onPlay={handlePlay}
                              />
                            </CardContent>
                          </Card>
                        ))}
                        {pageBlocks.length < BLOCKS_PER_PAGE &&
                          Array.from({ length: BLOCKS_PER_PAGE - pageBlocks.length }).map((_, fillerIndex) => (
                            <div key={`filler-${fillerIndex}`} className="hidden md:block" />
                          ))}
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {totalPages > 1 && (
                <>
                  <Button
                    size="icon"
                    variant="secondary"
                    disabled={!canPrev}
                    onClick={() => setPage(currentPage - 1)}
                    className="absolute left-3 top-1/2 -translate-y-1/2 z-10 opacity-0 group-hover:opacity-100 transition-opacity"
                  >
                    <ChevronLeft className="size-4" />
                  </Button>
                  <Button
                    size="icon"
                    variant="secondary"
                    disabled={!canNext}
                    onClick={() => setPage(currentPage + 1)}
                    className="absolute right-3 top-1/2 -translate-y-1/2 z-10 opacity-0 group-hover:opacity-100 transition-opacity"
                  >
                    <ChevronRight className="size-4" />
                  </Button>
                </>
              )}
            </div>
          </div>
        )
      })}
    </div>
  )
}

type PlaylistSectionConfig = {
  key: string
  title: string
  playlists: RawLayerPlaylistResponse[]
}

function PlaylistAccordion({ sections, onPlay }: { sections: PlaylistSectionConfig[], onPlay: (id: string) => void }) {
  const visibleSections = sections.filter(section => section.playlists.length > 0)
  const [openKey, setOpenKey] = useState<string | null>(visibleSections[0]?.key ?? null)

  if (visibleSections.length === 0) {
    return <div className="text-sm text-muted-foreground">Нет связанных плейлистов</div>
  }

  return (
    <div className="space-y-2">
      {visibleSections.map(section => {
        const isOpen = openKey === section.key
        return (
          <div key={section.key} className="rounded-lg border border-border/60 bg-muted/20">
            <button
              type="button"
              onClick={() => setOpenKey(isOpen ? null : section.key)}
              className="flex w-full items-center justify-between px-3 py-2 text-sm font-medium text-foreground"
            >
              <span>{section.title}</span>
              <div className="flex items-center gap-2 text-xs text-muted-foreground">
                {section.playlists.length} pcs
                <ChevronDown className={cn("size-4 transition-transform", isOpen ? "rotate-180" : "rotate-0")} />
              </div>
            </button>
            <div className={cn("grid transition-[grid-template-rows] duration-200 ease-out", isOpen ? "grid-rows-[1fr]" : "grid-rows-[0fr]")}>
              <div className="overflow-hidden border-t border-border/60">
                <div className="max-h-60 overflow-y-auto px-3 py-2 space-y-1">
                  {section.playlists.map(playlist => (
                    <MinimalPlaylistRow key={playlist.spotify_playlist_id} playlist={playlist} onPlay={onPlay} />
                  ))}
                </div>
              </div>
            </div>
          </div>
        )
      })}
    </div>
  )
}

function MinimalPlaylistRow({ playlist, onPlay }: { playlist: RawLayerPlaylistResponse, onPlay: (id: string) => void }) {
  return (
    <div className="flex items-center justify-between gap-3 rounded-md px-2 py-1.5 transition-colors hover:bg-background/70">
      <div className="flex items-center gap-2 overflow-hidden">
        <Button variant="ghost" size="icon" className="h-7 w-7 shrink-0" onClick={() => onPlay(playlist.spotify_playlist_id)}>
          <Play className="size-3" />
        </Button>
        <div className="flex flex-col overflow-hidden">
          <span className="text-sm font-medium truncate" title={getPlaylistName(playlist)}>
            {getPlaylistName(playlist)}
          </span>
          <span className="text-[11px] uppercase tracking-wide text-muted-foreground">
            {playlist.type.replace(/_/g, " ").toLowerCase()}
          </span>
        </div>
      </div>
      <a href={playlist.spotify_playlist_url} target="_blank" rel="noopener noreferrer" className="text-muted-foreground hover:text-foreground p-1">
        <ExternalLink className="size-3" />
      </a>
    </div>
  )
}

function StatChip({ label, value }: { label: string, value: string | number }) {
  return (
    <span className="inline-flex items-center gap-1 rounded-full border border-dashed border-border/60 px-2.5 py-1 text-[11px] uppercase tracking-wide text-muted-foreground">
      <span className="text-muted-foreground/70">{label}</span>
      <span className="font-semibold text-foreground">{value}</span>
    </span>
  )
}

function chunkArray<T>(items: T[], size: number): T[][] {
  if (size <= 0) return [items]
  const chunks: T[][] = []
  for (let i = 0; i < items.length; i += size) {
    chunks.push(items.slice(i, i + size))
  }
  return chunks
}

function getPlaylistName(p: RawLayerPlaylistResponse): string {
  if (p.type === "TARGET") return p.category_name || "Unknown Category"
  if (p.type === "INBOX_NEW") return "Inbox New"
  if (p.type === "INBOX_OLD") return "Inbox Old"
  if (p.type === "INBOX_NOT") return "Inbox Not"
  if (p.type === "TRASH") return "Trash"
  return p.type
}
