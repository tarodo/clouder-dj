import { useEffect, useCallback } from "react"
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query"
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

const REFRESH_INTERVAL = 3000

export function useSpotifyPlayer() {
  const queryClient = useQueryClient()

  const { data: track, isLoading, error } = useQuery<SpotifyCurrentlyPlaying | null>({
    queryKey: ["spotify-player"],
    queryFn: getCurrentlyPlaying,
    refetchInterval: REFRESH_INTERVAL,
    enabled: isLoggedIn(),
    retry: false,
  })

  const mutation = useMutation({
    mutationFn: async (action: () => Promise<void>) => {
      await action()
    },
    onSuccess: () => {
      setTimeout(() => {
        queryClient.invalidateQueries({ queryKey: ["spotify-player"] })
      }, 500)
    },
  })

  const performPlayerAction = useCallback((action: () => Promise<void>) => {
    if (!isLoggedIn()) return
    mutation.mutate(action)
  }, [mutation])

  const handlePrevious = useCallback(() => performPlayerAction(playerPrevious), [performPlayerAction])
  const handleNext = useCallback(() => performPlayerAction(playerNext), [performPlayerAction])

  const handlePlayPause = useCallback(async () => {
    if (!track) return
    const action = track.is_playing ? playerPause : playerPlay
    performPlayerAction(action)
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

  return {
    track: track || null,
    loading: isLoading,
    error: error ? "Failed to fetch player state" : null,
    handlePrevious,
    handleNext,
    handlePlayPause,
    handleSeek,
    handleRewind,
    handleFastForward,
  }
}
