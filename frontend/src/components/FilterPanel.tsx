import { useState } from "react";
import { Plus, RotateCcw, X } from "lucide-react";
import {
  IMAGE_TYPES,
  SUBJECTS,
  TECHNIQUES,
  labelize,
  type ArtworkFilters,
  type FileType,
  type ImageType,
  type Subject,
  type Technique,
} from "@/lib/api";
import { useExtensions } from "@/lib/queries";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { Slider } from "@/components/ui/slider";
import { Switch } from "@/components/ui/switch";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { TagMultiSelect } from "@/components/TagMultiSelect";

const ANY = "__any__";

function hexToRgbString(hex: string) {
  const n = parseInt(hex.slice(1), 16);
  return `${(n >> 16) & 255},${(n >> 8) & 255},${n & 255}`;
}

function SelectField<T extends string>({
  label,
  value,
  options,
  onChange,
}: {
  label: string;
  value: T | undefined;
  options: readonly T[];
  onChange: (v: T | undefined) => void;
}) {
  return (
    <div className="space-y-1.5">
      <Label className="text-xs uppercase tracking-wide text-muted-foreground">{label}</Label>
      <Select
        value={value ?? ANY}
        onValueChange={(v) => onChange(v === ANY ? undefined : (v as T))}
      >
        <SelectTrigger className="w-full">
          <SelectValue />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value={ANY}>Any</SelectItem>
          {options.map((o) => (
            <SelectItem key={o} value={o}>
              {labelize(o)}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>
    </div>
  );
}

export function FilterPanel({
  filters,
  onChange,
}: {
  filters: ArtworkFilters;
  onChange: (f: ArtworkFilters) => void;
}) {
  const { data: extensions = [] } = useExtensions();
  const [picker, setPicker] = useState("#c86a4a");
  const set = (patch: { [K in keyof ArtworkFilters]?: ArtworkFilters[K] | undefined }) => {
    const next = { ...filters, ...patch } as Record<string, unknown>;
    for (const key of Object.keys(next)) {
      if (next[key] === undefined) delete next[key];
    }
    onChange(next as ArtworkFilters);
  };

  return (
    <div className="space-y-5">
      <SelectField
        label="File type"
        value={filters.file_type}
        options={["image", "video"] as const}
        onChange={(v) => set({ file_type: v as FileType | undefined })}
      />
      <SelectField
        label="Image type"
        value={filters.image_type}
        options={IMAGE_TYPES}
        onChange={(v) => set({ image_type: v as ImageType | undefined })}
      />
      <SelectField
        label="Subject"
        value={filters.subject}
        options={SUBJECTS}
        onChange={(v) => set({ subject: v as Subject | undefined })}
      />
      <SelectField
        label="Technique"
        value={filters.art_technique}
        options={TECHNIQUES}
        onChange={(v) => set({ art_technique: v as Technique | undefined })}
      />
      <SelectField
        label="Extension"
        value={filters.file_extension}
        options={extensions}
        onChange={(v) => set({ file_extension: v })}
      />

      <div className="space-y-1.5">
        <Label className="text-xs uppercase tracking-wide text-muted-foreground">Tags</Label>
        <TagMultiSelect
          value={filters.tag_ids ?? []}
          onChange={(ids) => set({ tag_ids: ids.length ? ids : undefined })}
        />
      </div>

      <div className="space-y-2">
        <Label className="text-xs uppercase tracking-wide text-muted-foreground">Colors</Label>
        <div className="flex items-center gap-2">
          <input
            type="color"
            value={picker}
            onChange={(e) => setPicker(e.target.value)}
            className="size-9 cursor-pointer rounded-md border border-border bg-transparent"
            aria-label="Pick color"
          />
          <Button
            variant="outline"
            size="sm"
            onClick={() => set({ colors: [...(filters.colors ?? []), hexToRgbString(picker)] })}
          >
            <Plus className="size-3.5" /> Add color
          </Button>
        </div>
        {!!filters.colors?.length && (
          <div className="flex flex-wrap gap-1.5">
            {filters.colors.map((c) => (
              <button
                key={c}
                onClick={() => set({ colors: filters.colors?.filter((x) => x !== c) })}
                className="inline-flex items-center gap-1 rounded-full border border-border py-0.5 pl-0.5 pr-2 text-xs"
              >
                <span className="size-5 rounded-full" style={{ backgroundColor: `rgb(${c})` }} />
                <X className="size-3 opacity-50" />
              </button>
            ))}
          </div>
        )}
        {!!filters.colors?.length && (
          <div className="space-y-1.5 pt-1">
            <div className="flex justify-between text-xs text-muted-foreground">
              <span>Threshold</span>
              <span className="tabular-nums">{filters.color_threshold ?? 50}</span>
            </div>
            <Slider
              min={0}
              max={200}
              step={5}
              value={[filters.color_threshold ?? 50]}
              onValueChange={([v]) => set({ color_threshold: v })}
            />
          </div>
        )}
      </div>

      <div className="flex items-center justify-between rounded-md border border-border px-3 py-2">
        <Label htmlFor="pending" className="text-sm font-normal">
          Pending review only
        </Label>
        <Switch
          id="pending"
          checked={filters.reviewed === false}
          onCheckedChange={(c) => set({ reviewed: c ? false : undefined })}
        />
      </div>

      <Button variant="ghost" size="sm" className="w-full" onClick={() => onChange({})}>
        <RotateCcw className="size-3.5" /> Reset filters
      </Button>
    </div>
  );
}
