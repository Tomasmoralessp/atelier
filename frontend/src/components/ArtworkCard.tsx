import { useState, type MouseEvent } from "react";
import { Maximize2, RotateCw } from "lucide-react";
import { assetUrl, labelize, type Artwork } from "@/lib/api";
import { ColorSwatches } from "@/components/ColorSwatches";

export function ArtworkCard({
  artwork,
  selected,
  selectionMode,
  onSelect,
  onOpen,
}: {
  artwork: Artwork;
  selected: boolean;
  selectionMode: boolean;
  onSelect: (e: MouseEvent) => void;
  onOpen: () => void;
}) {
  const [flipped, setFlipped] = useState(false);
  const src = assetUrl(artwork.file_url);

  const handleClick = (e: MouseEvent) => {
    if (selectionMode || e.shiftKey || e.metaKey || e.ctrlKey) {
      onSelect(e);
      return;
    }
    setFlipped((f) => !f);
  };

  return (
    <div
      className={`flip-scene group relative aspect-square rounded-lg ${
        selected ? "ring-2 ring-primary ring-offset-2 ring-offset-background" : ""
      }`}
    >
      <div className={`flip-inner ${flipped ? "is-flipped" : ""}`}>
        {/* Front */}
        <div
          className="flip-face cursor-pointer overflow-hidden rounded-lg bg-surface"
          onClick={handleClick}
          onDoubleClick={onOpen}
        >
          {artwork.file_type === "video" ? (
            <video
              src={src}
              muted
              playsInline
              className="size-full object-cover"
              onMouseOver={(e) => void e.currentTarget.play().catch(() => {})}
              onMouseOut={(e) => e.currentTarget.pause()}
            />
          ) : (
            <img
              src={src}
              alt={labelize(artwork.image_type)}
              loading="lazy"
              className="size-full object-cover"
            />
          )}

          <span
            aria-label={artwork.reviewed ? "Reviewed" : "Pending review"}
            className={`absolute right-2 top-2 size-2 rounded-full shadow-sm ${
              artwork.reviewed ? "bg-emerald-500" : "bg-muted-foreground/60"
            }`}
          />
          <button
            aria-label="Open artwork"
            onClick={(e) => {
              e.stopPropagation();
              onOpen();
            }}
            className="absolute bottom-2 right-2 rounded-full bg-card/90 p-1.5 opacity-0 transition-opacity group-hover:opacity-100"
          >
            <Maximize2 className="size-3.5" />
          </button>
        </div>
        {/* Back */}
        <div
          className="flip-face flip-back cursor-pointer overflow-auto rounded-lg border border-border bg-card p-3"
          onClick={handleClick}
          onDoubleClick={onOpen}
        >
          <div className="space-y-2.5 text-xs">
            <div className="flex items-center justify-between">
              <span className="font-medium">{labelize(artwork.image_type)}</span>
              <RotateCw className="size-3 text-muted-foreground" />
            </div>
            <ColorSwatches colors={artwork.colors} />
            <dl className="space-y-1 text-muted-foreground">
              <div className="flex justify-between gap-2">
                <dt>Subject</dt>
                <dd className="text-foreground">{labelize(artwork.subject)}</dd>
              </div>
              <div className="flex justify-between gap-2">
                <dt>Technique</dt>
                <dd className="text-foreground">{labelize(artwork.art_technique)}</dd>
              </div>
              <div className="flex justify-between gap-2">
                <dt>Status</dt>
                <dd className="text-foreground">{artwork.reviewed ? "Reviewed" : "Pending"}</dd>
              </div>
            </dl>
            <div className="flex flex-wrap gap-1">
              {artwork.tags.map((t) => (
                <span
                  key={t.id}
                  className="rounded-full bg-secondary px-2 py-0.5 text-[10px] text-secondary-foreground"
                >
                  {t.name}
                </span>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
