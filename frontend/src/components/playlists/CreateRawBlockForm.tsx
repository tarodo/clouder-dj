import { useEffect, useState } from "react"
import { useMutation, useQueryClient } from "@tanstack/react-query"
import { createRawLayerBlock, type RawLayerBlockCreate } from "@/lib/clouderApi"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { StyleSelector } from "@/components/categories/StyleSelector"
import { toast } from "sonner"
import { Plus } from "lucide-react"
import { Card, CardContent, CardTitle } from "@/components/ui/card"

const formatISODate = (date: Date) => date.toISOString().slice(0, 10)

const getISOWeekRange = (weekNumber: number, year: number) => {
  const simple = new Date(Date.UTC(year, 0, 1 + (weekNumber - 1) * 7))
  const dayOfWeek = simple.getUTCDay() || 7
  const weekStart = new Date(simple)
  weekStart.setUTCDate(simple.getUTCDate() - dayOfWeek + 1)
  const weekEnd = new Date(weekStart)
  weekEnd.setUTCDate(weekStart.getUTCDate() + 6)
  return { start: weekStart, end: weekEnd }
}

const padWeek = (weekNumber: number) => weekNumber.toString().padStart(2, "0")

export function CreateRawBlockForm() {
  const [styleId, setStyleId] = useState<number | null>(null)
  const [name, setName] = useState("")
  const [startDate, setStartDate] = useState("")
  const [endDate, setEndDate] = useState("")
  const [weekNumber, setWeekNumber] = useState("")
  const [weekYear, setWeekYear] = useState(() => new Date().getFullYear().toString())
  const queryClient = useQueryClient()

  useEffect(() => {
    const week = Number(weekNumber)
    const year = Number(weekYear)
    const isValidWeek = Number.isFinite(week) && week >= 1 && week <= 53
    const isValidYear = Number.isFinite(year) && weekYear.trim().length === 4
    if (!isValidWeek || !isValidYear) return

    const { start, end } = getISOWeekRange(week, year)
    const isoStart = formatISODate(start)
    const isoEnd = formatISODate(end)
    setStartDate(isoStart)
    setEndDate(isoEnd)
    setName(`WEEK ${padWeek(week)}`)
  }, [weekNumber, weekYear])

  const mutation = useMutation({
    mutationFn: (data: RawLayerBlockCreate) => {
      if (!styleId) throw new Error("Style is required")
      return createRawLayerBlock(styleId, data)
    },
    onSuccess: () => {
      toast.success("Raw layer block created")
      setName("")
      setStartDate("")
      setEndDate("")
      setWeekNumber("")
      setWeekYear(new Date().getFullYear().toString())
      queryClient.invalidateQueries({ queryKey: ["raw-layer-blocks"] })
    },
    onError: (error: any) => {
      toast.error(error.message)
    },
  })

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (!styleId || !name || !startDate || !endDate) {
      toast.error("Please fill in all fields")
      return
    }
    mutation.mutate({
      block_name: name,
      start_date: startDate,
      end_date: endDate,
    })
  }

  const labelClass = "text-[11px] font-medium uppercase tracking-wide text-muted-foreground"
  const weekPreview =
    weekNumber && startDate && endDate
      ? `WEEK ${padWeek(Number(weekNumber))}: ${startDate} → ${endDate}`
      : "Waiting for ISO week"

  return (
    <Card className="mb-8 border border-dashed border-muted bg-muted/30">
      <CardContent className="p-4">
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="flex flex-wrap items-center gap-3">
            <div>
              <p className="text-[11px] uppercase tracking-[0.2em] text-muted-foreground">Raw Layer</p>
              <CardTitle className="text-base font-semibold tracking-tight">Create New Block</CardTitle>
            </div>
            <div className="ml-auto flex shrink-0 items-center gap-2">
              <div className="rounded-md border bg-background px-2 py-1 font-mono text-xs text-muted-foreground">{weekPreview}</div>
              <Button type="submit" size="sm" disabled={mutation.isPending} className="gap-1">
                <Plus className="size-3" />
                {mutation.isPending ? "Creating..." : "Create"}
              </Button>
            </div>
          </div>
          <div className="grid gap-3 md:grid-cols-5">
            <div className="space-y-1.5 md:col-span-3">
              <Label className={labelClass}>Style</Label>
              <StyleSelector selectedStyleId={styleId} onSelect={setStyleId} />
            </div>
            <div className="space-y-1.5 md:col-span-2">
              <Label htmlFor="blockName" className={labelClass}>
                Block Name
              </Label>
              <Input id="blockName" value={name} onChange={(e) => setName(e.target.value)} placeholder="e.g. WEEK 08" />
            </div>
          </div>
          <div className="grid gap-3 md:grid-cols-4">
            <div className="space-y-1.5">
              <Label htmlFor="weekNumber" className={labelClass}>
                Week #
              </Label>
              <Input
                id="weekNumber"
                type="number"
                min={1}
                max={53}
                value={weekNumber}
                onChange={(e) => setWeekNumber(e.target.value)}
                placeholder="08"
              />
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="weekYear" className={labelClass}>
                Year
              </Label>
              <Input
                id="weekYear"
                type="number"
                min={2000}
                max={2100}
                value={weekYear}
                onChange={(e) => setWeekYear(e.target.value)}
              />
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="startDate" className={labelClass}>
                Start
              </Label>
              <Input id="startDate" type="date" value={startDate} onChange={(e) => setStartDate(e.target.value)} />
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="endDate" className={labelClass}>
                End
              </Label>
              <Input id="endDate" type="date" value={endDate} onChange={(e) => setEndDate(e.target.value)} />
            </div>
          </div>
        </form>
      </CardContent>
    </Card>
  )
}
