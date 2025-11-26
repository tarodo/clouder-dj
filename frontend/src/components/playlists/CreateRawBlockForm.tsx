import { useState } from "react"
import { useMutation, useQueryClient } from "@tanstack/react-query"
import { createRawLayerBlock, type RawLayerBlockCreate } from "@/lib/clouderApi"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { StyleSelector } from "@/components/categories/StyleSelector"
import { toast } from "sonner"
import { Plus } from "lucide-react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"

export function CreateRawBlockForm() {
  const [styleId, setStyleId] = useState<number | null>(null)
  const [name, setName] = useState("")
  const [startDate, setStartDate] = useState("")
  const [endDate, setEndDate] = useState("")
  const queryClient = useQueryClient()

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
