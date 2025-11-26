import { useEffect, useState } from "react"
import { useMutation, useQueryClient } from "@tanstack/react-query"
import { createRawLayerBlock, type RawLayerBlockCreate } from "@/lib/clouderApi"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { StyleSelector } from "@/components/categories/StyleSelector"
import { toast } from "sonner"
import { Plus } from "lucide-react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"

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

  return (
    <Card className="mb-8">
      <CardHeader>
        <CardTitle className="text-lg">Create New Block</CardTitle>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="space-y-2">
            <Label>Style</Label>
            <StyleSelector selectedStyleId={styleId} onSelect={setStyleId} />
          </div>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="space-y-2">
              <Label htmlFor="weekNumber">Week Number (1-53)</Label>
              <Input
                id="weekNumber"
                type="number"
                min={1}
                max={53}
                value={weekNumber}
                onChange={(e) => setWeekNumber(e.target.value)}
                placeholder="e.g. 8"
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="weekYear">Week Year</Label>
              <Input
                id="weekYear"
                type="number"
                min={2000}
                max={2100}
                value={weekYear}
                onChange={(e) => setWeekYear(e.target.value)}
              />
            </div>
            <div className="space-y-2">
              <Label>Auto Week Preview</Label>
              <div className="h-10 rounded-md border px-3 py-2 text-sm text-muted-foreground flex items-center">
                {weekNumber && startDate && endDate
                  ? `WEEK ${padWeek(Number(weekNumber))}: ${startDate} → ${endDate}`
                  : "Pick a week to auto-fill dates and name"}
              </div>
            </div>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="space-y-2">
              <Label htmlFor="blockName">Block Name</Label>
              <Input id="blockName" value={name} onChange={(e) => setName(e.target.value)} placeholder="e.g. Summer 2025" />
            </div>
            <div className="space-y-2">
              <Label htmlFor="startDate">Start Date</Label>
              <Input id="startDate" type="date" value={startDate} onChange={(e) => setStartDate(e.target.value)} />
            </div>
            <div className="space-y-2">
              <Label htmlFor="endDate">End Date</Label>
              <Input id="endDate" type="date" value={endDate} onChange={(e) => setEndDate(e.target.value)} />
            </div>
          </div>
          <div className="flex justify-end">
            <Button type="submit" disabled={mutation.isPending}>
              <Plus className="mr-2 size-4" /> {mutation.isPending ? "Creating..." : "Create Block"}
            </Button>
          </div>
        </form>
      </CardContent>
    </Card>
  )
}
