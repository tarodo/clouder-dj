import { BrowserRouter, Routes, Route } from "react-router-dom"
import LoginPage from "@/pages/Login"
import LogoutPage from "@/pages/Logout"
import SpotifyCallbackPage from "@/pages/SpotifyCallback"
import PlayerPage from "@/pages/Player"
import { AppLayout } from "@/components/AppLayout"

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<LoginPage />} />
        <Route path="/spotify-callback" element={<SpotifyCallbackPage />} />
        <Route path="/logout" element={<LogoutPage />} />
        <Route element={<AppLayout />}>
          <Route path="/player" element={<PlayerPage />} />
        </Route>
      </Routes>
    </BrowserRouter>
  )
}

export default App
