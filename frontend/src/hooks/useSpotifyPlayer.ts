import { useState, useEffect, useCallback } from "react"
import {
  getCurrentlyPlaying,
  playerNext,
  playerPause,
  playerPlay,
  playerPrevious,
  playerSeek,
  type SpotifyCurrentlyPlaying,
} from "@/lib/spotify"
import { isLoggedIn } from "@/lib/auth"

const REFRESH_INTERVAL = 2000
const ACTION_DELAY = 500 // Delay to allow Spotify API to update state

export function useSpotifyPlayer() {
  const [track, setTrack] = useState<SpotifyCurrentlyPlaying | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const fetchCurrentTrack = useCallback(async () => {
    if (!isLoggedIn()) {
      setError("Authentication token not found.")
      setLoading(false)
      return
    }
    try {
      const currentTrack = await getCurrentlyPlaying()
      setTrack(currentTrack)
    } catch (e) {
      console.error(e)
      setError("Failed to fetch current track.")
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    setLoading(true)
    fetchCurrentTrack()
    const intervalId = setInterval(fetchCurrentTrack, REFRESH_INTERVAL)
    return () => clearInterval(intervalId)
  }, [fetchCurrentTrack])

  const performPlayerAction = useCallback(
    async (action: () => Promise<void>) => {
      if (!isLoggedIn()) return
      try {
        await action()
        setTimeout(fetchCurrentTrack, ACTION_DELAY)
      } catch (e) {
        console.error(e)
        setError("Player command failed.")
      }
    },
    [fetchCurrentTrack]
  )

  const handlePrevious = useCallback(() => performPlayerAction(playerPrevious), [performPlayerAction])
  const handleNext = useCallback(() => performPlayerAction(playerNext), [performPlayerAction])

  const handlePlayPause = useCallback(async () => {
    if (!track) return
    const action = track.is_playing ? playerPause : playerPlay
    await performPlayerAction(action)
  }, [track, performPlayerAction])

  const handleSeek = useCallback((percentage: number) => {
    if (!track?.item) return
    const positionMs = track.item.duration_ms * percentage
    performPlayerAction(() => playerSeek(positionMs))
  }, [track, performPlayerAction])

  const handleRewind = useCallback(() => {
    if (!track) return
    const newPositionMs = Math.max(0, track.progress_ms - 10000)
    performPlayerAction(() => playerSeek(newPositionMs))
  }, [track, performPlayerAction])

  const handleFastForward = useCallback(() => {
    if (!track?.item) return
    const newPositionMs = Math.min(track.item.duration_ms, track.progress_ms + 10000)
    performPlayerAction(() => playerSeek(newPositionMs))
  }, [track, performPlayerAction])

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.target instanceof HTMLInputElement || e.target instanceof HTMLTextAreaElement) return

      const keyMap: Record<string, (() => void) | undefined> = {
        " ": handlePlayPause,
        ">": handleNext,
        "<": handlePrevious,
        ".": handleFastForward,
        ",": handleRewind,
        "1": () => handleSeek(0),
        "2": () => handleSeek(0.2),
        "3": () => handleSeek(0.4),
        "4": () => handleSeek(0.6),
        "5": () => handleSeek(0.8),
      }

      const action = keyMap[e.key]
      if (action) {
        e.preventDefault()
        action()
      }
    }

    window.addEventListener("keydown", handleKeyDown)
    return () => window.removeEventListener("keydown", handleKeyDown)
  }, [handlePlayPause, handleNext, handlePrevious, handleFastForward, handleRewind, handleSeek])

  return { track, loading, error, handlePrevious, handleNext, handlePlayPause, handleSeek, handleRewind, handleFastForward }
}
