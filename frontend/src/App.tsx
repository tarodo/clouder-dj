import { BrowserRouter, Routes, Route } from "react-router-dom"
import LoginPage from "@/pages/Login"
import LogoutPage from "@/pages/Logout"
import SpotifyCallbackPage from "@/pages/SpotifyCallback"
import PlayerPage from "@/pages/Player"
import { AppLayout } from "@/components/AppLayout"
import PlaylistsPage from "@/pages/PlaylistsPage"
import ReleasePlaylistDetailPage from "@/pages/ReleasePlaylistDetail"
import { ProtectedRoute } from "@/components/auth/ProtectedRoute"

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<LoginPage />} />
        <Route path="/spotify-callback" element={<SpotifyCallbackPage />} />
        <Route path="/logout" element={<LogoutPage />} />
        <Route element={<ProtectedRoute><AppLayout /></ProtectedRoute>}>
          <Route path="/player" element={<PlayerPage />} />
          <Route path="/release-playlists" element={<PlaylistsPage />} />
          <Route path="/release-playlists/:id" element={<ReleasePlaylistDetailPage />} />
        </Route>
      </Routes>
    </BrowserRouter>
  )
}

export default App
