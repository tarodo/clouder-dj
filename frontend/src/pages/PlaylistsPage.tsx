import { useState } from "react"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { ReleasePlaylistsTable } from "@/components/playlists/ReleasePlaylistsTable"
import { RawLayerList } from "@/components/playlists/RawLayerList"
import { UserPlaylistsList } from "@/components/playlists/UserPlaylistsList"

export default function PlaylistsPage() {
  const [activeTab, setActiveTab] = useState("raw")

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold">Playlists</h1>
      </div>

      <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
        <TabsList className="flex h-auto w-auto max-w-full items-center justify-start sm:justify-center rounded-full bg-muted/60 p-1 overflow-x-auto no-scrollbar mx-auto">
          <TabsTrigger value="raw" className="rounded-full text-xs px-4 py-1.5">
            Raw Layer
          </TabsTrigger>
          <TabsTrigger value="release" className="rounded-full text-xs px-4 py-1.5">
            Release
          </TabsTrigger>
          <TabsTrigger value="user" className="rounded-full text-xs px-4 py-1.5">
            User
          </TabsTrigger>
        </TabsList>
        <TabsContent value="raw" className="mt-6">
          <RawLayerList />
        </TabsContent>
        <TabsContent value="release" className="mt-6">
          <ReleasePlaylistsTable />
        </TabsContent>
        <TabsContent value="user" className="mt-6">
          <UserPlaylistsList />
        </TabsContent>
      </Tabs>
    </div>
  )
}
