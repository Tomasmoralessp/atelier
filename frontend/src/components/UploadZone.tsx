import { useRef, useState } from "react";
import { FolderInput, UploadCloud } from "lucide-react";
import { toast } from "sonner";
import { open as openDialog } from "@tauri-apps/plugin-dialog";
import { api, emptySummary, mergeSummary, type ImportSummary } from "@/lib/api";
import { useInvalidateArtworks } from "@/lib/queries";
import { isTauri } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import { ImportSummaryDialog } from "@/components/ImportSummaryDialog";

// Each request classifies its files before answering, so small chunks keep
// the progress bar moving.
const CHUNK_SIZE = 8;

function chunks<T>(items: T[]): T[][] {
  const out: T[][] = [];
  for (let i = 0; i < items.length; i += CHUNK_SIZE) out.push(items.slice(i, i + CHUNK_SIZE));
  return out;
}

export function UploadZone() {
  const [dragging, setDragging] = useState(false);
  const [progress, setProgress] = useState<{ done: number; total: number } | null>(null);
  const [summary, setSummary] = useState<ImportSummary | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  const invalidate = useInvalidateArtworks();
  const canImportFolder = isTauri;
  const busy = progress !== null;

  const run = async <T,>(
    items: T[],
    send: (chunk: T[]) => Promise<ImportSummary>,
    initial = emptySummary(),
  ) => {
    const total = items.length + initial.skipped.length;
    let done = initial.skipped.length;
    const result = initial;
    setProgress({ done, total });
    try {
      for (const chunk of chunks(items)) {
        mergeSummary(result, await send(chunk));
        done += chunk.length;
        setProgress({ done, total });
        invalidate();
      }
      setSummary(result);
    } catch (e) {
      toast.error(e instanceof Error ? e.message : "Import failed");
      invalidate();
    } finally {
      setProgress(null);
    }
  };

  const uploadFiles = (files: File[]) => {
    if (files.length) void run(files, (chunk) => api.upload(chunk));
  };

  const importFolder = async () => {
    const folder = await openDialog({ directory: true, title: "Import a folder of images" });
    if (typeof folder !== "string") return;
    try {
      const scan = await api.scanFolder(folder);
      if (!scan.files.length && !scan.skipped.length) {
        toast.info("That folder has no files to import");
        return;
      }
      await run(scan.files, api.importFiles, { ...emptySummary(), skipped: scan.skipped });
    } catch (e) {
      toast.error(e instanceof Error ? e.message : "Could not read that folder");
    }
  };

  return (
    <div className="space-y-2">
      <div
        onDragOver={(e) => {
          e.preventDefault();
          setDragging(true);
        }}
        onDragLeave={() => setDragging(false)}
        onDrop={(e) => {
          e.preventDefault();
          setDragging(false);
          if (!busy) uploadFiles(Array.from(e.dataTransfer.files));
        }}
        onClick={() => !busy && inputRef.current?.click()}
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
            uploadFiles(Array.from(e.target.files ?? []));
            e.target.value = "";
          }}
        />
        <UploadCloud className="mx-auto size-5 text-muted-foreground" />
        <p className="mt-2 text-sm text-foreground">Drop files here</p>
        <p className="text-xs text-muted-foreground">or click to browse</p>
        {progress && (
          <div className="mt-3 space-y-1">
            <Progress value={(progress.done / Math.max(progress.total, 1)) * 100} />
            <p className="text-xs text-muted-foreground">
              Importing {progress.done} / {progress.total}…
            </p>
          </div>
        )}
      </div>
      {canImportFolder && (
        <Button variant="outline" size="sm" className="w-full" disabled={busy} onClick={importFolder}>
          <FolderInput className="size-4" /> Import folder…
        </Button>
      )}
      <ImportSummaryDialog summary={summary} onClose={() => setSummary(null)} />
    </div>
  );
}
