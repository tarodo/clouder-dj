import { Button } from "@/components/ui/button"
import {
  ArrowLeftCircle,
  ArrowRightCircle,
  ChevronsLeft,
  ChevronsRight,
  PauseCircle,
  PlayCircle,
} from "lucide-react"

interface PlayerControlsProps {
  isPlaying: boolean
  onPlayPause: () => void
  onNext: () => void
  onPrevious: () => void
  onRewind: () => void
  onFastForward: () => void
  onSeek: (percentage: number) => void
  isPlayerActive: boolean
}

export function PlayerControls({
  isPlaying,
  onPlayPause,
  onNext,
  onPrevious,
  onRewind,
  onFastForward,
  onSeek,
  isPlayerActive,
}: PlayerControlsProps) {
  return (
    <>
      <div className="flex items-center gap-4">
        <Button variant="ghost" size="icon" onClick={onRewind} disabled={!isPlayerActive}>
          <ChevronsLeft className="size-10" />
        </Button>
        <Button variant="ghost" size="icon" onClick={onPrevious} disabled={!isPlayerActive}>
          <ArrowLeftCircle className="size-10" />
        </Button>
        <Button variant="ghost" size="icon" onClick={onPlayPause} disabled={!isPlayerActive}>
          {isPlaying ? <PauseCircle className="size-12" /> : <PlayCircle className="size-12" />}
        </Button>
        <Button variant="ghost" size="icon" onClick={onNext} disabled={!isPlayerActive}>
          <ArrowRightCircle className="size-10" />
        </Button>
        <Button variant="ghost" size="icon" onClick={onFastForward} disabled={!isPlayerActive}>
          <ChevronsRight className="size-10" />
        </Button>
      </div>
      <div className="flex items-center gap-2">
        {[0, 0.2, 0.4, 0.6, 0.8].map((percentage, index) => (
          <Button
            key={percentage}
            variant="outline"
            size="icon"
            className="rounded-full w-10 h-10 bg-white text-black border-3 border-black font-bold"
            onClick={() => onSeek(percentage)}
            disabled={!isPlayerActive}
          >
            {index + 1}
          </Button>
        ))}
      </div>
    </>
  )
}
