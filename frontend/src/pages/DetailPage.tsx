import { useEffect, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { ArrowLeft, ChevronLeft, ChevronRight, Copy, Loader2, Trash2 } from "lucide-react";
import { toast } from "sonner";
import { assetUrl, labelize, type ArtworkFilters } from "@/lib/api";
import { useArtwork, useArtworks, useDeleteArtworks } from "@/lib/queries";
import { loadFilters } from "@/lib/filterStore";
import { isTauri } from "@/lib/utils";
import { ColorSwatches } from "@/components/ColorSwatches";
import { ReviewPanel } from "@/components/ReviewPanel";
import { ThemeToggle } from "@/components/ThemeToggle";
import { Button } from "@/components/ui/button";
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

export default function DetailPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [filters, setFilters] = useState<ArtworkFilters>({});
  useEffect(() => setFilters(loadFilters()), []);

  const { data: artwork, isLoading, error } = useArtwork(id!);
  const { data: siblings = [] } = useArtworks(filters);
  const deleteArtworks = useDeleteArtworks();

  const index = siblings.findIndex((a) => a.id === id);
  const prev = index > 0 ? siblings[index - 1] : undefined;
  const next = index >= 0 && index < siblings.length - 1 ? siblings[index + 1] : undefined;

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "ArrowLeft" && prev) navigate(`/artwork/${prev.id}`);
      if (e.key === "ArrowRight" && next) navigate(`/artwork/${next.id}`);
      if (e.key === "Escape") navigate("/");
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [prev, next, navigate]);

  const handleCopy = async () => {
    if (!artwork) return;
    try {
      const { writeFiles } = await import("tauri-plugin-clipboard-api");
      await writeFiles([artwork.file_path]);
      toast.success("Copied to clipboard");
    } catch (e) {
      toast.error(e instanceof Error ? e.message : "Could not copy file");
    }
  };

  const handleDelete = async () => {
    if (!artwork) return;
    try {
      await deleteArtworks.mutateAsync([artwork.id]);
      toast.success("Artwork deleted");
      navigate("/");
    } catch (e) {
      toast.error(e instanceof Error ? e.message : "Could not delete artwork");
    }
  };

  return (
    <div className="flex min-h-screen flex-col bg-background text-foreground">
      <header className="flex items-center justify-between border-b border-border px-6 py-4">
        <Button variant="ghost" size="sm" asChild>
          <Link to="/">
            <ArrowLeft className="size-4" /> Back to grid
          </Link>
        </Button>
        <div className="flex items-center gap-1">
          <Button
            variant="ghost"
            size="icon"
            disabled={!prev}
            aria-label="Previous artwork"
            onClick={() => prev && navigate(`/artwork/${prev.id}`)}
          >
            <ChevronLeft className="size-4" />
          </Button>
          <Button
            variant="ghost"
            size="icon"
            disabled={!next}
            aria-label="Next artwork"
            onClick={() => next && navigate(`/artwork/${next.id}`)}
          >
            <ChevronRight className="size-4" />
          </Button>
          <ThemeToggle />
        </div>
      </header>

      {isLoading && (
        <div className="flex flex-1 items-center justify-center text-muted-foreground">
          <Loader2 className="size-5 animate-spin" />
        </div>
      )}
      {error && (
        <p className="flex-1 py-24 text-center text-sm text-destructive">
          Could not load this artwork.
        </p>
      )}

      {artwork && (
        <div className="flex flex-1 flex-col lg:flex-row">
          <section className="flex flex-1 items-center justify-center bg-surface p-6 lg:p-12">
            {artwork.file_type === "video" ? (
              <video
                src={assetUrl(artwork.file_url)}
                controls
                className="max-h-[calc(100vh-10rem)] max-w-full rounded-md"
              />
            ) : (
              <img
                src={assetUrl(artwork.file_url)}
                alt={labelize(artwork.image_type)}
                className="max-h-[calc(100vh-10rem)] max-w-full rounded-md object-contain"
              />
            )}
          </section>

          <aside className="w-full shrink-0 space-y-6 border-t border-border px-6 py-8 lg:h-[calc(100vh-69px)] lg:w-96 lg:overflow-y-auto lg:border-l lg:border-t-0">
            <div>
              <h2 className="text-lg">{labelize(artwork.image_type)}</h2>
              <p className="text-xs uppercase tracking-wide text-muted-foreground">
                {artwork.file_extension} · {artwork.file_type} ·{" "}
                <span className={artwork.reviewed ? "text-emerald-600" : "text-destructive"}>
                  {artwork.reviewed ? "Reviewed" : "Pending review"}
                </span>
              </p>
            </div>

            <div className="space-y-2">
              <h3 className="text-xs uppercase tracking-wide text-muted-foreground">Palette</h3>
              <ColorSwatches colors={artwork.colors} size="lg" />
            </div>

            <div className="space-y-2 border-t border-border pt-5">
              <h3 className="text-xs uppercase tracking-wide text-muted-foreground">
                Quick review
              </h3>
              <ReviewPanel artwork={artwork} />
            </div>

            <div className="flex gap-2 border-t border-border pt-5">
              {isTauri && (
                <Button variant="outline" size="sm" className="flex-1" onClick={handleCopy}>
                  <Copy className="size-4" /> Copy
                </Button>
              )}
              <AlertDialog>
                <AlertDialogTrigger asChild>
                  <Button variant="outline" size="sm" className="flex-1 text-destructive">
                    <Trash2 className="size-4" /> Delete
                  </Button>
                </AlertDialogTrigger>
                <AlertDialogContent>
                  <AlertDialogHeader>
                    <AlertDialogTitle>Delete this artwork?</AlertDialogTitle>
                    <AlertDialogDescription>
                      This will permanently remove the file and its data. This cannot be undone.
                    </AlertDialogDescription>
                  </AlertDialogHeader>
                  <AlertDialogFooter>
                    <AlertDialogCancel>Cancel</AlertDialogCancel>
                    <AlertDialogAction onClick={handleDelete}>Delete</AlertDialogAction>
                  </AlertDialogFooter>
                </AlertDialogContent>
              </AlertDialog>
            </div>
          </aside>
        </div>
      )}
    </div>
  );
}
