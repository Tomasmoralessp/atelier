import type { ArtworkColor } from "@/lib/api";
import { toast } from "sonner";

function rgbToHex(r: number, g: number, b: number) {
  return `#${[r, g, b].map((x) => x.toString(16).padStart(2, "0")).join("")}`;
}

export function ColorSwatches({
  colors,
  size = "sm",
}: {
  colors: ArtworkColor[];
  size?: "sm" | "lg";
}) {
  if (!colors?.length) return <p className="text-xs text-muted-foreground">No palette</p>;

  const handleCopy = (r: number, g: number, b: number) => {
    const hex = rgbToHex(r, g, b);
    navigator.clipboard.writeText(hex);
    toast.success(`Copied ${hex}`);
  };

  return (
    <div className="flex flex-wrap gap-1.5">
      {colors.map((c, i) => (
        <div key={i} className="flex flex-col items-center gap-1">
          <button
            onClick={() => handleCopy(c.r, c.g, c.b)}
            className={`${size === "lg" ? "size-9" : "size-6"} rounded-full border border-border/60 transition-transform hover:scale-110`}
            style={{ backgroundColor: `rgb(${c.r},${c.g},${c.b})` }}
            title={`${rgbToHex(c.r, c.g, c.b)} — ${c.percentage.toFixed(1)}% (click to copy)`}
          />
          {size === "lg" && (
            <span className="text-[10px] tabular-nums text-muted-foreground">
              {c.percentage.toFixed(0)}%
            </span>
          )}
        </div>
      ))}
    </div>
  );
}
