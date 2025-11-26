import { useState } from "react"
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query"
import { getCategories, deleteCategory, updateCategory, type Category } from "@/lib/clouderApi"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Skeleton } from "@/components/ui/skeleton"
import { ExternalLink, Trash2, Edit2, Save, X } from "lucide-react"
import { toast } from "sonner"

interface CategoryListProps {
  styleId: number
}

export function CategoryList({ styleId }: CategoryListProps) {
  const queryClient = useQueryClient()
  const { data: categories = [], isLoading, error } = useQuery({
    queryKey: ["categories", styleId],
    queryFn: () => getCategories(styleId),
  })

  const deleteMutation = useMutation({
    mutationFn: (id: number) => deleteCategory(id, false),
    onSuccess: () => {
      toast.success("Category deleted")
      queryClient.invalidateQueries({ queryKey: ["categories", styleId] })
    },
    onError: () => toast.error("Failed to delete category"),
  })

  if (isLoading) return <Skeleton className="h-48 w-full" />
  if (error) return <div className="text-red-500">Failed to load categories</div>
  if (categories.length === 0) return <div className="text-muted-foreground py-8 text-center">No categories found for this style.</div>

  return (
    <div className="border rounded-md">
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>Name</TableHead>
            <TableHead className="w-[100px] text-right">Spotify</TableHead>
            <TableHead className="w-[150px] text-right">Actions</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {categories.map((category) => (
            <CategoryRow key={category.id} category={category} onDelete={(id) => deleteMutation.mutate(id)} />
          ))}
        </TableBody>
      </Table>
    </div>
  )
}

function CategoryRow({ category, onDelete }: { category: Category, onDelete: (id: number) => void }) {
  const [isEditing, setIsEditing] = useState(false)
  const [name, setName] = useState(category.name)
  const queryClient = useQueryClient()

  const updateMutation = useMutation({
    mutationFn: (newName: string) => updateCategory(category.id, { name: newName }),
    onSuccess: () => {
      toast.success("Category updated")
      setIsEditing(false)
      queryClient.invalidateQueries({ queryKey: ["categories", category.style_id] })
    },
    onError: () => toast.error("Failed to update category"),
  })

  const handleSave = () => {
    if (name.trim() !== category.name) {
      updateMutation.mutate(name)
    } else {
      setIsEditing(false)
    }
  }

  return (
    <TableRow>
      <TableCell>
        {isEditing ? (
          <Input
            value={name}
            onChange={(e) => setName(e.target.value)}
            className="max-w-xs"
            autoFocus
            onKeyDown={(e) => {
              if (e.key === "Enter") handleSave()
              if (e.key === "Escape") setIsEditing(false)
            }}
          />
        ) : (
          <span className="font-medium">{category.name}</span>
        )}
      </TableCell>
      <TableCell className="text-right">
        <Button variant="ghost" size="icon" asChild>
          <a href={category.spotify_playlist_url} target="_blank" rel="noopener noreferrer">
            <ExternalLink className="size-4" />
          </a>
        </Button>
      </TableCell>
      <TableCell className="text-right">
        {isEditing ? (
          <div className="flex justify-end gap-2">
            <Button variant="ghost" size="icon" onClick={handleSave} disabled={updateMutation.isPending}>
              <Save className="size-4" />
            </Button>
            <Button variant="ghost" size="icon" onClick={() => setIsEditing(false)}>
              <X className="size-4" />
            </Button>
          </div>
        ) : (
          <div className="flex justify-end gap-2">
            <Button
              variant="ghost"
              size="icon"
              onClick={() => setIsEditing(true)}
            >
              <Edit2 className="size-4" />
            </Button>
            <Button
              variant="ghost"
              size="icon"
              onClick={() => {
                if (confirm("Are you sure? This will delete the category from the database.")) {
                  onDelete(category.id)
                }
              }}
            >
              <Trash2 className="size-4 text-destructive" />
            </Button>
          </div>
        )}
      </TableCell>
    </TableRow>
  )
}
