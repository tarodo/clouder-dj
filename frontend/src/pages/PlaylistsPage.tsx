import { useState } from "react"
import { PillTabs, PillTabsContent, PillTabsList, PillTabsTrigger } from "@/components/ui/pill-tabs"
import { ReleasePlaylistsTable } from "@/components/playlists/ReleasePlaylistsTable"
import { RawLayerList } from "@/components/playlists/RawLayerList"
import { UserPlaylistsList } from "@/components/playlists/UserPlaylistsList"
import { StylePlaylistsList } from "@/components/playlists/StylePlaylistsList"

export default function PlaylistsPage() {
  const [activeTab, setActiveTab] = useState("raw")

  return (
    <div className="mx-auto max-w-6xl space-y-6">
      <PillTabs value={activeTab} onValueChange={setActiveTab} className="w-full">
        <PillTabsList>
          <PillTabsTrigger value="raw">
            Raw Layer
          </PillTabsTrigger>
          <PillTabsTrigger value="categorized">
            Categorized
          </PillTabsTrigger>
          <PillTabsTrigger value="release">
            Release
          </PillTabsTrigger>
          <PillTabsTrigger value="user">
            User
          </PillTabsTrigger>
        </PillTabsList>
        <PillTabsContent value="raw" className="mt-6">
          <RawLayerList />
        </PillTabsContent>
        <PillTabsContent value="categorized" className="mt-6">
          <StylePlaylistsList />
        </PillTabsContent>
        <PillTabsContent value="release" className="mt-6">
          <ReleasePlaylistsTable />
        </PillTabsContent>
        <PillTabsContent value="user" className="mt-6">
          <UserPlaylistsList />
        </PillTabsContent>
      </PillTabs>
    </div>
  )
}
