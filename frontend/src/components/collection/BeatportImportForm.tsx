import { useState } from "react"
import { useMutation } from "@tanstack/react-query"
import { triggerBeatportCollection, type BeatportCollectionRequest } from "@/lib/clouderApi"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { StyleSelector } from "@/components/categories/StyleSelector"
import { toast } from "sonner"
import { Download } from "lucide-react"

export function BeatportImportForm() {
  const [styleId, setStyleId] = useState<number | null>(null)
  const [dateFrom, setDateFrom] = useState("")
  const [dateTo, setDateTo] = useState("")
  const [token, setToken] = useState("")

  const mutation = useMutation({
    mutationFn: (data: BeatportCollectionRequest) => triggerBeatportCollection(data),
    onSuccess: () => {
      toast.success("Beatport collection task started")
    },
    onError: (error: any) => {
      toast.error(error.message || "Failed to start collection task")
    },
  })

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (!styleId || !dateFrom || !dateTo || !token) {
      toast.error("Please fill in all fields")
      return
    }
    mutation.mutate({
      style_id: styleId,
      date_from: dateFrom,
      date_to: dateTo,
      bp_token: token,
    })
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div className="space-y-2">
        <Label>Style</Label>
        <StyleSelector selectedStyleId={styleId} onSelect={setStyleId} useBeatportId={true} />
      </div>

      <div className="grid grid-cols-2 gap-4">
        <div className="space-y-2">
          <Label htmlFor="dateFrom">From Date</Label>
          <Input
            id="dateFrom"
            type="date"
            value={dateFrom}
            onChange={(e) => setDateFrom(e.target.value)}
          />
        </div>
        <div className="space-y-2">
          <Label htmlFor="dateTo">To Date</Label>
          <Input
            id="dateTo"
            type="date"
            value={dateTo}
            onChange={(e) => setDateTo(e.target.value)}
          />
        </div>
      </div>

      <div className="space-y-2">
        <Label htmlFor="token">Beatport Token</Label>
        <Input id="token" type="password" value={token} onChange={(e) => setToken(e.target.value)} />
      </div>

      <Button type="submit" disabled={mutation.isPending} className="w-full">
        <Download className="mr-2 size-4" /> {mutation.isPending ? "Starting..." : "Start Import"}
      </Button>
    </form>
  )
}
