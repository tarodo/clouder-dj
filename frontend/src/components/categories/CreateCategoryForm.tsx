import { useState } from "react"
import { useMutation, useQueryClient } from "@tanstack/react-query"
import { createCategory } from "@/lib/clouderApi"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { toast } from "sonner"
import { Plus } from "lucide-react"

interface CreateCategoryFormProps {
  styleId: number
}

export function CreateCategoryForm({ styleId }: CreateCategoryFormProps) {
  const [name, setName] = useState("")
  const queryClient = useQueryClient()

  const mutation = useMutation({
    mutationFn: (categoryName: string) => createCategory(styleId, { name: categoryName }),
    onSuccess: () => {
      toast.success("Category created")
      setName("")
      queryClient.invalidateQueries({ queryKey: ["categories", styleId] })
    },
    onError: (error: any) => {
      toast.error(error.message)
    },
  })

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (!name.trim()) return
    mutation.mutate(name)
  }

  return (
    <form onSubmit={handleSubmit} className="flex gap-2 items-center">
      <Input
        placeholder="New category name..."
        value={name}
        onChange={(e) => setName(e.target.value)}
        className="max-w-xs"
      />
      <Button type="submit" disabled={mutation.isPending || !name.trim()}>
        {mutation.isPending ? "Creating..." : (
          <>
            <Plus className="mr-2 size-4" /> Create
          </>
        )}
      </Button>
    </form>
  )
}
