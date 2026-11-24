import { useState } from "react";
import { Check, ChevronsUpDown, Plus, X } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  Command,
  CommandEmpty,
  CommandGroup,
  CommandInput,
  CommandItem,
  CommandList,
} from "@/components/ui/command";
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";
import { useTags, useCreateTag } from "@/lib/queries";

export function TagMultiSelect({
  value,
  onChange,
  placeholder = "Tags",
}: {
  value: number[];
  onChange: (ids: number[]) => void;
  placeholder?: string;
}) {
  const { data: tags = [] } = useTags();
  const createTag = useCreateTag();
  const [open, setOpen] = useState(false);
  const [search, setSearch] = useState("");
  const selected = tags.filter((t) => value.includes(t.id));
  const toggle = (id: number) =>
    onChange(value.includes(id) ? value.filter((v) => v !== id) : [...value, id]);

  const exactMatch = tags.some((t) => t.name.toLowerCase() === search.trim().toLowerCase());

  const handleCreate = async () => {
    const name = search.trim();
    if (!name) return;
    const newTag = await createTag.mutateAsync(name);
    onChange([...value, newTag.id]);
    setSearch("");
  };

  return (
    <div className="space-y-2">
      <Popover open={open} onOpenChange={setOpen}>
        <PopoverTrigger asChild>
          <Button variant="outline" className="w-full justify-between font-normal">
            <span className="truncate text-muted-foreground">
              {selected.length ? `${selected.length} selected` : placeholder}
            </span>
            <ChevronsUpDown className="size-4 opacity-50" />
          </Button>
        </PopoverTrigger>
        <PopoverContent className="w-[240px] p-0" align="start">
          <Command>
            <CommandInput placeholder="Search tags…" value={search} onValueChange={setSearch} />
            <CommandList>
              {!exactMatch && search.trim() && (
                <CommandItem onSelect={handleCreate} className="text-primary">
                  <Plus className="mr-2 size-4" />
                  Create "{search.trim()}"
                </CommandItem>
              )}
              {!search.trim() && <CommandEmpty>No tags found.</CommandEmpty>}
              <CommandGroup>
                {tags
                  .filter((t) => t.name.toLowerCase().includes(search.toLowerCase()))
                  .map((t) => (
                    <CommandItem key={t.id} value={t.name} onSelect={() => toggle(t.id)}>
                      <Check
                        className={`mr-2 size-4 ${value.includes(t.id) ? "opacity-100" : "opacity-0"}`}
                      />
                      {t.name}
                    </CommandItem>
                  ))}
              </CommandGroup>
            </CommandList>
          </Command>
        </PopoverContent>
      </Popover>
      {selected.length > 0 && (
        <div className="flex flex-wrap gap-1.5">
          {selected.map((t) => (
            <button
              key={t.id}
              onClick={() => toggle(t.id)}
              className="inline-flex items-center gap-1 rounded-full bg-secondary px-2.5 py-0.5 text-xs text-secondary-foreground"
            >
              {t.name}
              <X className="size-3 opacity-50" />
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
