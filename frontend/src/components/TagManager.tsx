import { useState } from "react";
import { Plus, Trash2 } from "lucide-react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { useCreateTag, useDeleteTag, useTags } from "@/lib/queries";

export function TagManager() {
  const { data: tags = [] } = useTags();
  const createTag = useCreateTag();
  const deleteTag = useDeleteTag();
  const [name, setName] = useState("");

  const submit = () => {
    const value = name.trim();
    if (!value) return;
    createTag.mutate(value, {
      onSuccess: () => {
        setName("");
        toast.success(`Tag "${value}" created`);
      },
      onError: (e) => toast.error(e.message),
    });
  };

  return (
    <div className="space-y-4">
      <div className="flex gap-2">
        <Input
          value={name}
          placeholder="New tag name"
          onChange={(e) => setName(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && submit()}
        />
        <Button onClick={submit} disabled={createTag.isPending}>
          <Plus className="size-4" />
        </Button>
      </div>
      <div className="flex flex-wrap gap-2">
        {tags.map((t) => (
          <span
            key={t.id}
            className="group inline-flex items-center gap-1.5 rounded-full border border-border bg-secondary px-3 py-1 text-xs text-secondary-foreground"
          >
            {t.name}
            <button
              aria-label={`Delete ${t.name}`}
              onClick={() => deleteTag.mutate(t.id)}
              className="opacity-40 transition-opacity hover:opacity-100"
            >
              <Trash2 className="size-3" />
            </button>
          </span>
        ))}
        {!tags.length && <p className="text-sm text-muted-foreground">No tags yet.</p>}
      </div>
    </div>
  );
}
