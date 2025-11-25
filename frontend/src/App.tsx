import { BrowserRouter, Routes, Route } from "react-router-dom"
import LoginPage from "@/pages/Login"
import LogoutPage from "@/pages/Logout"
import SpotifyCallbackPage from "@/pages/SpotifyCallback"
import PlayerPage from "@/pages/Player"
import { AppLayout } from "@/components/AppLayout"
import ReleasePlaylistsPage from "@/pages/ReleasePlaylists"
import ReleasePlaylistDetailPage from "@/pages/ReleasePlaylistDetail"

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<LoginPage />} />
        <Route path="/spotify-callback" element={<SpotifyCallbackPage />} />
        <Route path="/logout" element={<LogoutPage />} />
        <Route element={<AppLayout />}>
          <Route path="/player" element={<PlayerPage />} />
          <Route path="/release-playlists" element={<ReleasePlaylistsPage />} />
          <Route path="/release-playlists/:id" element={<ReleasePlaylistDetailPage />} />
        </Route>
      </Routes>
    </BrowserRouter>
  )
}

export default App
