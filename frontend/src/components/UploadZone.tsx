import { useRef, useState } from "react";
import { UploadCloud } from "lucide-react";
import { toast } from "sonner";
import { api } from "@/lib/api";
import { useInvalidateArtworks } from "@/lib/queries";
import { Progress } from "@/components/ui/progress";

export function UploadZone() {
  const [dragging, setDragging] = useState(false);
  const [progress, setProgress] = useState<number | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  const invalidate = useInvalidateArtworks();

  const upload = async (files: File[]) => {
    if (!files.length) return;
    setProgress(0);
    try {
      await api.upload(files, setProgress);
      toast.success(`${files.length} file${files.length > 1 ? "s" : ""} uploaded`);
      invalidate();
    } catch (e) {
      toast.error(e instanceof Error ? e.message : "Upload failed");
    } finally {
      setProgress(null);
    }
  };

  return (
    <div
      onDragOver={(e) => {
        e.preventDefault();
        setDragging(true);
      }}
      onDragLeave={() => setDragging(false)}
      onDrop={(e) => {
        e.preventDefault();
        setDragging(false);
        void upload(Array.from(e.dataTransfer.files));
      }}
      onClick={() => inputRef.current?.click()}
      className={`cursor-pointer rounded-lg border border-dashed p-6 text-center transition-colors ${
        dragging ? "border-primary bg-accent/60" : "border-border hover:border-primary/50"
      }`}
    >
      <input
        ref={inputRef}
        type="file"
        multiple
        hidden
        onChange={(e) => {
          void upload(Array.from(e.target.files ?? []));
          e.target.value = "";
        }}
      />
      <UploadCloud className="mx-auto size-5 text-muted-foreground" />
      <p className="mt-2 text-sm text-foreground">Drop files here</p>
      <p className="text-xs text-muted-foreground">or click to browse</p>
      {progress !== null && (
        <div className="mt-3 space-y-1">
          <Progress value={progress} />
          <p className="text-xs text-muted-foreground">
            {progress < 100 ? `Uploading ${progress}%` : "Processing…"}
          </p>
        </div>
      )}
    </div>
  );
}
