import { useEffect, useMemo, useRef, useState, type MouseEvent } from "react";
import { useNavigate } from "react-router-dom";
import { Copy, Loader2, Trash2 } from "lucide-react";
import { TagsMenuItem, SettingsMenuItem } from "@/components/HeaderMenuItems";
import { CheckSquare, X, SlidersHorizontal, Tags, MoreVertical } from "lucide-react";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { toast } from "sonner";

import { api, assetUrl, type ArtworkFilters } from "@/lib/api";
import { useArtworks, useDeleteArtworks, useInvalidateArtworks, useTags } from "@/lib/queries";
import { loadFilters, saveFilters } from "@/lib/filterStore";
import { isTauri } from "@/lib/utils";

import { ArtworkCard } from "@/components/ArtworkCard";
import { SettingsDialog } from "@/components/SettingsDialog";
import { useSelectionContainer } from "@air/react-drag-to-select";
import { FilterPanel } from "@/components/FilterPanel";
import { TagManager } from "@/components/TagManager";
import { ThemeToggle } from "@/components/ThemeToggle";
import { UploadZone } from "@/components/UploadZone";
import { Button } from "@/components/ui/button";
import { useTheme } from "@/lib/theme";

import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { Sheet, SheetContent, SheetHeader, SheetTitle, SheetTrigger } from "@/components/ui/sheet";
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger,
} from "@/components/ui/alert-dialog";

export default function GridPage() {
  const navigate = useNavigate();
  const { theme } = useTheme();
  const [filters, setFilters] = useState<ArtworkFilters>({});
  const [selected, setSelected] = useState<string[]>([]);
  const [selectionMode, setSelectionMode] = useState(false);
  const [lastIndex, setLastIndex] = useState<number | null>(null);
  const { data: artworks, isLoading, error } = useArtworks(filters);
  const cardRefs = useRef<Map<string, HTMLDivElement>>(new Map());
  const { data: tags = [] } = useTags();
  const invalidate = useInvalidateArtworks();
  const deleteArtworks = useDeleteArtworks();
  const [applying, setApplying] = useState(false);

  useEffect(() => setFilters(loadFilters()), []);
  useEffect(() => saveFilters(filters), [filters]);

  const items = useMemo(() => artworks ?? [], [artworks]);

  const handleCopySelection = async () => {
    try {
      const { writeFiles } = await import("tauri-plugin-clipboard-api");
      const { clearClipboardTemp, downloadToClipboardTemp } = await import("@/lib/clipboardTemp");

      await clearClipboardTemp();

      const selectedItems = selected
        .map((id) => items.find((i) => i.id === id))
        .filter((item): item is NonNullable<typeof item> => !!item);

      const tempPaths = await Promise.all(
        selectedItems.map((item) =>
          downloadToClipboardTemp(assetUrl(item.file_url), `${item.id}.${item.file_extension}`),
        ),
      );

      await writeFiles(tempPaths);
      toast.success(`Copied ${tempPaths.length} files`);
    } catch (e) {
      console.error("Error al copiar:", e);
      toast.error(e instanceof Error ? e.message : "Could not copy files");
    }
  };

  const handleSelect = (index: number, e: MouseEvent) => {
    const id = items[index]!.id;
    if (e.shiftKey && lastIndex !== null) {
      const [a, b] = [Math.min(lastIndex, index), Math.max(lastIndex, index)];
      const range = items.slice(a, b + 1).map((i) => i.id);
      setSelected((prev) => Array.from(new Set([...prev, ...range])));
    } else {
      setSelected((prev) => (prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id]));
      setLastIndex(index);
    }
  };

  const { DragSelection } = useSelectionContainer({
    isEnabled: selectionMode,
    onSelectionChange: (box) => {
      const newSelected: string[] = [];
      items.forEach((artwork) => {
        const el = cardRefs.current.get(artwork.id);
        if (!el) return;
        const rect = el.getBoundingClientRect();
        const intersects =
          rect.left < box.left + box.width &&
          rect.left + rect.width > box.left &&
          rect.top < box.top + box.height &&
          rect.top + rect.height > box.top;
        if (intersects) newSelected.push(artwork.id);
      });
      setSelected(newSelected);
    },
  });

  const applyTagToSelection = async (tagId: number) => {
    setApplying(true);
    try {
      await Promise.all(
        selected.map((id) => {
          const art = items.find((i) => i.id === id);
          const ids = Array.from(new Set([...(art?.tags.map((t) => t.id) ?? []), tagId]));
          return api.updateArtwork(id, { tag_ids: ids });
        }),
      );
      toast.success(`Tag applied to ${selected.length} artworks`);
      invalidate();
    } catch (e) {
      toast.error(e instanceof Error ? e.message : "Could not apply tag");
    } finally {
      setApplying(false);
    }
  };

  const handleDeleteSelection = async () => {
    try {
      await deleteArtworks.mutateAsync(selected);
      toast.success(`${selected.length} artworks deleted`);
      setSelected([]);
    } catch (e) {
      toast.error(e instanceof Error ? e.message : "Could not delete artworks");
    }
  };

  return (
    <div className="min-h-screen bg-background text-foreground">
      <header className="sticky top-0 z-30 flex items-center justify-between border-b border-border bg-background/85 px-4 py-3 backdrop-blur sm:px-6 sm:py-4">
        <div className="flex min-w-0 items-center gap-2 sm:gap-3">
          <div className="min-w-0">
            {!isTauri && <h1 className="truncate text-base tracking-tight sm:text-xl">Atelier</h1>}
            <p
              className={`truncate text-muted-foreground ${
                isTauri
                  ? "hidden text-base tracking-tight xs:block sm:text-xl"
                  : "hidden text-xs sm:block"
              }`}
            >
              {items.length} piece{items.length === 1 ? "" : "s"} in the archive
            </p>
          </div>
        </div>
        <div className="flex shrink-0 items-center gap-0.5 sm:gap-1">
          <Sheet>
            <SheetTrigger asChild>
              <Button variant="ghost" size="sm" className="lg:hidden">
                <SlidersHorizontal className="size-4" />
                <span className="hidden sm:inline">Filters</span>
              </Button>
            </SheetTrigger>
            <SheetContent side="left" className="w-full overflow-y-auto sm:max-w-sm">
              <SheetHeader>
                <SheetTitle>Filters</SheetTitle>
              </SheetHeader>
              <div className="mt-6">
                <UploadZone />
                <div className="mt-6">
                  <FilterPanel filters={filters} onChange={setFilters} />
                </div>
              </div>
            </SheetContent>
          </Sheet>

          <Button
            variant={selectionMode ? "default" : "ghost"}
            size="sm"
            onClick={() => {
              setSelectionMode((s) => !s);
              setSelected([]);
            }}
          >
            {selectionMode ? <X className="size-4" /> : <CheckSquare className="size-4" />}
            <span className="hidden sm:inline">{selectionMode ? "Done" : "Select"}</span>
          </Button>

          <div className="hidden items-center gap-0.5 sm:flex sm:gap-1">
            <Dialog>
              <DialogTrigger asChild>
                <Button variant="ghost" size="sm">
                  <Tags className="size-4" />
                </Button>
              </DialogTrigger>
              <DialogContent>
                <DialogHeader>
                  <DialogTitle>Manage tags</DialogTitle>
                </DialogHeader>
                <TagManager />
              </DialogContent>
            </Dialog>
            {isTauri && <SettingsDialog />}
          </div>

          <div className="sm:hidden">
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button variant="ghost" size="icon">
                  <MoreVertical className="size-4" />
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end">
                <TagsMenuItem />
                {isTauri && <SettingsMenuItem />}
              </DropdownMenuContent>
            </DropdownMenu>
          </div>

          <ThemeToggle />
        </div>
      </header>

      <div className="flex">
        <aside className="sticky top-[73px] hidden h-[calc(100vh-73px)] w-72 shrink-0 overflow-y-auto border-r border-border bg-surface px-5 py-6 lg:block">
          <UploadZone />
          <div className="mt-6">
            <FilterPanel filters={filters} onChange={setFilters} />
          </div>
        </aside>

        <main className="flex-1 px-6 py-8">
          <div className="mb-6 lg:hidden">
            <UploadZone />
          </div>
          {isLoading && (
            <div className="flex justify-center py-24 text-muted-foreground">
              <Loader2 className="size-5 animate-spin" />
            </div>
          )}
          {error && (
            <p className="py-24 text-center text-sm text-destructive">
              Could not reach the archive API. Is the backend running?
            </p>
          )}
          {!isLoading && !error && !items.length && (
            <p className="py-24 text-center text-sm text-muted-foreground">
              Nothing here yet — drop some files to begin.
            </p>
          )}

          <div className="relative">
            <DragSelection />
            <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 xl:grid-cols-4 2xl:grid-cols-5">
              {items.map((artwork, index) => (
                <div
                  key={artwork.id}
                  ref={(el) => {
                    if (el) cardRefs.current.set(artwork.id, el);
                    else cardRefs.current.delete(artwork.id);
                  }}
                >
                  <ArtworkCard
                    artwork={artwork}
                    selected={selected.includes(artwork.id)}
                    selectionMode={selectionMode}
                    onSelect={(e) => handleSelect(index, e)}
                    onOpen={() => navigate(`/artwork/${artwork.id}`)}
                  />
                </div>
              ))}
            </div>
          </div>
        </main>
      </div>

      {selected.length > 0 && (
        <div className="fixed bottom-4 left-1/2 z-40 flex -translate-x-1/2 items-center gap-1 rounded-full border border-border bg-card px-2 py-1.5 shadow-lg sm:gap-2 sm:px-3 sm:py-2">
          <div className="flex flex-col items-center px-1 leading-none sm:flex-row sm:gap-1 sm:px-2">
            <span className="text-sm font-medium sm:text-sm sm:font-normal">{selected.length}</span>
            <span className="text-[10px] text-muted-foreground sm:text-sm">selected</span>
          </div>
          <Popover>
            <PopoverTrigger asChild>
              <Button size="sm" variant="outline" disabled={applying}>
                {applying ? (
                  <Loader2 className="size-3.5 animate-spin" />
                ) : (
                  <Tags className="size-3.5" />
                )}
                <span className="hidden sm:inline">Apply tag</span>
              </Button>
            </PopoverTrigger>
            <PopoverContent className="w-52 p-1" align="center">
              <div className="max-h-64 overflow-y-auto">
                {tags.map((t) => (
                  <button
                    key={t.id}
                    onClick={() => void applyTagToSelection(t.id)}
                    className="w-full rounded-sm px-2 py-1.5 text-left text-sm hover:bg-accent"
                  >
                    {t.name}
                  </button>
                ))}
                {!tags.length && <p className="p-2 text-xs text-muted-foreground">No tags yet.</p>}
              </div>
            </PopoverContent>
          </Popover>
          {isTauri && (
            <Button size="sm" variant="outline" onClick={handleCopySelection}>
              <Copy className="size-3.5" />
              <span className="hidden sm:inline">Copy</span>
            </Button>
          )}
          <AlertDialog>
            <AlertDialogTrigger asChild>
              <Button size="sm" variant="outline" className="text-destructive">
                <Trash2 className="size-3.5" />
                <span className="hidden sm:inline">Delete</span>
              </Button>
            </AlertDialogTrigger>
            <AlertDialogContent>
              <AlertDialogHeader>
                <AlertDialogTitle>Delete {selected.length} artworks?</AlertDialogTitle>
                <AlertDialogDescription>
                  This will permanently remove the files and their data. This cannot be undone.
                </AlertDialogDescription>
              </AlertDialogHeader>
              <AlertDialogFooter>
                <AlertDialogCancel>Cancel</AlertDialogCancel>
                <AlertDialogAction onClick={handleDeleteSelection}>Delete</AlertDialogAction>
              </AlertDialogFooter>
            </AlertDialogContent>
          </AlertDialog>
          <Button size="icon" variant="ghost" onClick={() => setSelected([])}>
            <X className="size-4" />
          </Button>
        </div>
      )}
    </div>
  );
}
