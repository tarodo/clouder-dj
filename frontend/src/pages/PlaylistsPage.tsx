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
        <TabsList className="grid w-full grid-cols-3 max-w-[400px]">
          <TabsTrigger value="raw">Raw Layer</TabsTrigger>
          <TabsTrigger value="release">Release</TabsTrigger>
          <TabsTrigger value="user">User</TabsTrigger>
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
