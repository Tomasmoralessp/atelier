import { useEffect, useState } from "react";
import { Check } from "lucide-react";
import { toast } from "sonner";

import {
  IMAGE_TYPES,
  SUBJECTS,
  TECHNIQUES,
  labelize,
  type Artwork,
  type ImageType,
  type Subject,
  type Technique,
} from "@/lib/api";
import { useUpdateArtwork } from "@/lib/queries";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { TagMultiSelect } from "@/components/TagMultiSelect";

export function ReviewPanel({ artwork, compact }: { artwork: Artwork; compact?: boolean }) {
  const [imageType, setImageType] = useState<ImageType | "">(artwork.image_type ?? "");
  const [subject, setSubject] = useState<Subject | "">(artwork.subject ?? "");
  const [technique, setTechnique] = useState<Technique | "">(artwork.art_technique ?? "");
  const [tagIds, setTagIds] = useState<number[]>(artwork.tags.map((t) => t.id));
  const update = useUpdateArtwork();

  useEffect(() => {
    setImageType(artwork.image_type ?? "");
    setSubject(artwork.subject ?? "");
    setTechnique(artwork.art_technique ?? "");
    setTagIds(artwork.tags.map((t) => t.id));
  }, [artwork]);

  const save = (reviewed: boolean) => {
    const patch: {
      id: string;
      image_type?: ImageType;
      subject?: Subject;
      art_technique?: Technique;
      tag_ids?: number[];
      reviewed?: boolean;
    } = { id: artwork.id, tag_ids: tagIds, reviewed };
    if (imageType) patch.image_type = imageType;
    if (subject) patch.subject = subject;
    if (technique) patch.art_technique = technique;
    update.mutate(patch, {
      onSuccess: () => toast.success(reviewed ? "Marked as reviewed" : "Changes saved"),
      onError: (e) => toast.error(e.message),
    });
  };

  const isImage = artwork.file_type === "image";

  return (
    <div className={compact ? "space-y-3" : "space-y-4"}>
      {isImage && (
        <>
          <div className="space-y-1.5">
            <Label className="text-xs uppercase tracking-wide text-muted-foreground">Type</Label>
            <Select value={imageType} onValueChange={(v) => setImageType(v as ImageType)}>
              <SelectTrigger className="w-full">
                <SelectValue placeholder="Not set" />
              </SelectTrigger>
              <SelectContent>
                {IMAGE_TYPES.map((t) => (
                  <SelectItem key={t} value={t}>
                    {labelize(t)}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          <div className="space-y-1.5">
            <Label className="text-xs uppercase tracking-wide text-muted-foreground">Subject</Label>
            <Select value={subject} onValueChange={(v) => setSubject(v as Subject)}>
              <SelectTrigger className="w-full">
                <SelectValue placeholder="Not set" />
              </SelectTrigger>
              <SelectContent>
                {SUBJECTS.map((s) => (
                  <SelectItem key={s} value={s}>
                    {labelize(s)}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          <div className="space-y-1.5">
            <Label className="text-xs uppercase tracking-wide text-muted-foreground">
              Technique
            </Label>
            <Select value={technique} onValueChange={(v) => setTechnique(v as Technique)}>
              <SelectTrigger className="w-full">
                <SelectValue placeholder="Not set" />
              </SelectTrigger>
              <SelectContent>
                {TECHNIQUES.map((t) => (
                  <SelectItem key={t} value={t}>
                    {labelize(t)}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        </>
      )}

      <div className="space-y-1.5">
        <Label className="text-xs uppercase tracking-wide text-muted-foreground">Tags</Label>
        <TagMultiSelect value={tagIds} onChange={setTagIds} />
      </div>

      <div className="flex gap-2 pt-1">
        <Button
          variant="outline"
          size="sm"
          className="flex-1"
          disabled={update.isPending}
          onClick={() => save(artwork.reviewed)}
        >
          Save
        </Button>
        <Button size="sm" className="flex-1" disabled={update.isPending} onClick={() => save(true)}>
          <Check className="size-3.5" /> Confirm review
        </Button>
      </div>
    </div>
  );
}
