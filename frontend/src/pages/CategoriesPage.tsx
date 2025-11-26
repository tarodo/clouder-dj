import { useState } from "react"
import { StyleSelector } from "@/components/categories/StyleSelector"
import { CategoryList } from "@/components/categories/CategoryList"
import { CreateCategoryForm } from "@/components/categories/CreateCategoryForm"
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"

export default function CategoriesPage() {
  const [selectedStyleId, setSelectedStyleId] = useState<number | null>(null)

  return (
    <div className="space-y-6 max-w-4xl mx-auto">
      <div className="flex flex-col gap-2">
        <h1 className="text-3xl font-bold">Category Management</h1>
        <p className="text-muted-foreground">Manage music categories for different styles.</p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Select Style</CardTitle>
          <CardDescription>Choose a style to view and manage its categories.</CardDescription>
        </CardHeader>
        <CardContent>
          <StyleSelector selectedStyleId={selectedStyleId} onSelect={setSelectedStyleId} />
        </CardContent>
      </Card>

      {selectedStyleId && (
        <div className="space-y-4 animate-in fade-in slide-in-from-bottom-4 duration-500">
          <div className="flex justify-between items-center">
            <h2 className="text-xl font-semibold">Categories</h2>
            <CreateCategoryForm styleId={selectedStyleId} />
          </div>
          <CategoryList styleId={selectedStyleId} />
        </div>
      )}
    </div>
  )
}
