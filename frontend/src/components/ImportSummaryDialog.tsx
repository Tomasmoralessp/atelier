import type { ImportSummary } from "@/lib/api";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";

function FileList({ title, items }: { title: string; items: string[] }) {
  if (!items.length) return null;
  return (
    <div className="space-y-1">
      <p className="text-sm font-medium">{title}</p>
      <ul className="max-h-40 overflow-y-auto rounded-md border border-border p-2 font-mono text-xs text-muted-foreground">
        {items.map((item, i) => (
          <li key={i} className="truncate">
            {item}
          </li>
        ))}
      </ul>
    </div>
  );
}

export function ImportSummaryDialog({
  summary,
  onClose,
}: {
  summary: ImportSummary | null;
  onClose: () => void;
}) {
  if (!summary) return null;
  const { imported, duplicates, skipped } = summary;
  return (
    <Dialog open onOpenChange={(open) => !open && onClose()}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Import finished</DialogTitle>
          <DialogDescription>
            {imported.length} imported · {duplicates.length} already in the library ·{" "}
            {skipped.length} skipped
          </DialogDescription>
        </DialogHeader>
        <FileList title="Already in the library" items={duplicates} />
        <FileList title="Skipped" items={skipped.map((s) => `${s.name} — ${s.reason}`)} />
      </DialogContent>
    </Dialog>
  );
}
