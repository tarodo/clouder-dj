import { useEffect, useCallback, useState, useRef } from "react"
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

const REFRESH_INTERVAL = 6000
const LOCAL_UPDATE_INTERVAL = 1000

export function useSpotifyPlayer() {
  const queryClient = useQueryClient()
  const [localProgress, setLocalProgress] = useState<number>(0)
  const isInteracting = useRef(false)

  const { data: track, isLoading, error } = useQuery<SpotifyCurrentlyPlaying | null>({
    queryKey: ["spotify-player"],
    queryFn: getCurrentlyPlaying,
    refetchInterval: REFRESH_INTERVAL,
    enabled: isLoggedIn(),
    retry: false,
  })

  // Sync local progress when new track data arrives
  useEffect(() => {
    if (track) {
      setLocalProgress(track.progress_ms)
    }
  }, [track])

  // Local timer for smooth progress
  useEffect(() => {
    if (!track?.is_playing || !track.item) return

    const interval = setInterval(() => {
      // If we successfully synced barely ago, don't jump
      // Just increment normally

      // Check if we are interacting (seek/pause pending) - unimplemented here but good for future
      if (isInteracting.current) return

      setLocalProgress((prev) => {
        const next = prev + LOCAL_UPDATE_INTERVAL
        return next > track.item!.duration_ms ? track.item!.duration_ms : next
      })
    }, LOCAL_UPDATE_INTERVAL)

    return () => clearInterval(interval)
  }, [track?.is_playing, track?.item])


  const mutation = useMutation({
    mutationFn: async (action: () => Promise<void>) => {
      isInteracting.current = true
      await action()
    },
    onSuccess: () => {
      // Force immediate refresh to feel responsive
      queryClient.invalidateQueries({ queryKey: ["spotify-player"] })
      setTimeout(() => {
        isInteracting.current = false
      }, 1000)
    },
    onError: () => {
      isInteracting.current = false
    }
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
    // Optimistic update could go here
    performPlayerAction(action)
  }, [track, performPlayerAction])

  const handleSeek = useCallback((percentage: number) => {
    if (!track?.item) return
    const positionMs = track.item.duration_ms * percentage
    setLocalProgress(positionMs) // Immediate local update
    performPlayerAction(() => playerSeek(positionMs))
  }, [track, performPlayerAction])

  const handleRewind = useCallback(() => {
    if (!track) return
    const newPositionMs = Math.max(0, localProgress - 10000)
    setLocalProgress(newPositionMs)
    performPlayerAction(() => playerSeek(newPositionMs))
  }, [track, localProgress, performPlayerAction])

  const handleFastForward = useCallback(() => {
    if (!track?.item) return
    const newPositionMs = Math.min(track.item.duration_ms, localProgress + 10000)
    setLocalProgress(newPositionMs)
    performPlayerAction(() => playerSeek(newPositionMs))
  }, [track, localProgress, performPlayerAction])

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

  // Construct the return object with the LOCAL progress
  const displayTrack = track ? {
    ...track,
    progress_ms: localProgress
  } : null

  return {
    track: displayTrack,
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
