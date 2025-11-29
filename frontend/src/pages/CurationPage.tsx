import { useEffect, useState } from "react"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { StyleSelector } from "@/components/categories/StyleSelector"
import { CategoryList } from "@/components/categories/CategoryList"
import { CreateCategoryForm } from "@/components/categories/CreateCategoryForm"
import { CollectionStats } from "@/components/collection/CollectionStats"
import { BeatportImportForm } from "@/components/collection/BeatportImportForm"
import { SpotifyEnrichmentControl } from "@/components/collection/SpotifyEnrichmentControl"

type CurationTab = "categories" | "collection"

interface CurationPageProps {
  initialTab?: CurationTab
}

export default function CurationPage({ initialTab = "categories" }: CurationPageProps) {
  const [activeTab, setActiveTab] = useState<CurationTab>(initialTab)
  const [selectedStyleId, setSelectedStyleId] = useState<number | null>(null)

  useEffect(() => {
    setActiveTab(initialTab)
  }, [initialTab])

  return (
    <div className="mx-auto max-w-6xl space-y-6">

      <Tabs value={activeTab} onValueChange={(value) => setActiveTab(value as CurationTab)} className="w-full">
        <TabsList className="flex h-auto w-full flex-wrap justify-center gap-2 rounded-full bg-muted/60 p-1 text-xs font-semibold uppercase tracking-[0.35em] text-muted-foreground">
          <TabsTrigger
            value="categories"
            className="w-full rounded-full px-4 py-2 text-xs tracking-[0.25em] sm:w-auto"
          >
            Categories
          </TabsTrigger>
          <TabsTrigger
            value="collection"
            className="w-full rounded-full px-4 py-2 text-xs tracking-[0.25em] sm:w-auto"
          >
            Collection
          </TabsTrigger>
        </TabsList>

        <TabsContent value="categories" className="mt-6 space-y-6">
          <div className="grid gap-6 lg:grid-cols-[minmax(0,280px),1fr]">
            <Card className="border border-dashed bg-card/40 shadow-none">
              <CardHeader className="space-y-1">
                <CardTitle className="text-base font-semibold">Focus style</CardTitle>
                <CardDescription>Pick a style to keep the editing context tight.</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <StyleSelector selectedStyleId={selectedStyleId} onSelect={setSelectedStyleId} useBeatportId={false} />
              </CardContent>
            </Card>

            <Card className="border border-dashed bg-card/40 shadow-none">
              <CardHeader className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
                <div>
                  <CardTitle className="text-base font-semibold">Categories</CardTitle>
                  <CardDescription>Inline edits, no navigation.</CardDescription>
                </div>
                {selectedStyleId && <CreateCategoryForm styleId={selectedStyleId} />}
              </CardHeader>
              <CardContent>
                {selectedStyleId ? (
                  <CategoryList styleId={selectedStyleId} />
                ) : (
                  <p className="rounded-2xl border border-dashed px-4 py-8 text-center text-sm text-muted-foreground">
                    Choose a style on the left to unlock its categories.
                  </p>
                )}
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        <TabsContent value="collection" className="mt-6 space-y-6">
          <div className="grid gap-6 lg:grid-cols-[2fr,1fr]">
            <Card className="border border-dashed bg-card/40 shadow-none">
              <CardHeader className="space-y-1">
                <CardTitle className="text-base font-semibold">Snapshot</CardTitle>
                <CardDescription>React Query keeps the metrics live.</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <CollectionStats />
              </CardContent>
            </Card>

            <div className="space-y-6">
              <Card className="border border-dashed bg-card/40 shadow-none">
                <CardHeader>
                  <CardTitle className="text-base font-semibold">Beatport Import</CardTitle>
                  <CardDescription>Targeted pulls with style + date range.</CardDescription>
                </CardHeader>
                <CardContent>
                  <BeatportImportForm />
                </CardContent>
              </Card>

              <Card className="border border-dashed bg-card/40 shadow-none">
                <CardHeader>
                  <CardTitle className="text-base font-semibold">Spotify Enrichment</CardTitle>
                  <CardDescription>Fire-and-forget enrichment tasks.</CardDescription>
                </CardHeader>
                <CardContent>
                  <SpotifyEnrichmentControl />
                </CardContent>
              </Card>
            </div>
          </div>
        </TabsContent>
      </Tabs>
    </div>
  )
}
