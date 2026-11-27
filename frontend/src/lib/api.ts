export let API_BASE = "";

export function setApiBase(url: string) {
  API_BASE = url;
}

export type FileType = "image" | "video";

export const IMAGE_TYPES = [
  "photograph",
  "painting",
  "drawing",
  "illustration",
  "comic_art",
  "graphic_design",
  "logo",
  "product_design",
] as const;

export const SUBJECTS = ["landscape", "person", "animal", "abstract", "object"] as const;

export const TECHNIQUES = [
  "watercolor",
  "oil",
  "acrylic",
  "pencil_sketch",
  "ink",
  "collage",
  "vector_art",
] as const;

export type ImageType = (typeof IMAGE_TYPES)[number];
export type Subject = (typeof SUBJECTS)[number];
export type Technique = (typeof TECHNIQUES)[number];

export interface Tag {
  id: number;
  name: string;
}

export interface ArtworkColor {
  r: number;
  g: number;
  b: number;
  percentage: number;
}

export interface Artwork {
  id: string;
  file_type: FileType;
  file_extension: string;
  file_path: string;
  file_url: string;
  image_type: ImageType | null;
  subject: Subject | null;
  art_technique: Technique | null;
  tags: Tag[];
  reviewed: boolean;
  colors: ArtworkColor[];
}

export interface ArtworkFilters {
  file_type?: FileType;
  image_type?: ImageType;
  subject?: Subject;
  art_technique?: Technique;
  tag_ids?: number[];
  reviewed?: boolean;
  colors?: string[];
  color_threshold?: number;
  file_extension?: string;
}

export interface ImportSummary {
  imported: string[];
  duplicates: string[];
  skipped: { name: string; reason: string }[];
}

export interface Health {
  status: string;
  mode: "local" | "remote";
  data_dir: string;
  local_import: boolean;
}

export interface BackupResult {
  backup_dir: string;
  files_copied: number;
  finished_at: string;
}

export function emptySummary(): ImportSummary {
  return { imported: [], duplicates: [], skipped: [] };
}

export function mergeSummary(into: ImportSummary, next: ImportSummary) {
  into.imported.push(...next.imported);
  into.duplicates.push(...next.duplicates);
  into.skipped.push(...next.skipped);
}

function postJson<T>(path: string, body: unknown) {
  return request<T>(path, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
}

export function assetUrl(fileUrl: string) {
  if (!fileUrl) return "";
  if (/^https?:\/\//.test(fileUrl)) return fileUrl;
  return `${API_BASE}${fileUrl.startsWith("/") ? "" : "/"}${fileUrl}`;
}

export function labelize(value: string | null | undefined) {
  if (!value) return "—";
  return value.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, init);
  if (!res.ok) {
    const text = await res.text().catch(() => "");
    throw new Error(text || `Request failed (${res.status})`);
  }
  if (res.status === 204) return undefined as T;
  return (await res.json()) as T;
}

function toSearch(filters: ArtworkFilters) {
  const p = new URLSearchParams();
  if (filters.file_type) p.set("file_type", filters.file_type);
  if (filters.image_type) p.set("image_type", filters.image_type);
  if (filters.subject) p.set("subject", filters.subject);
  if (filters.art_technique) p.set("art_technique", filters.art_technique);
  if (filters.file_extension) p.set("file_extension", filters.file_extension);
  if (typeof filters.reviewed === "boolean") p.set("reviewed", String(filters.reviewed));
  filters.tag_ids?.forEach((id) => p.append("tag_ids", String(id)));
  if (filters.colors?.length) {
    filters.colors.forEach((c) => p.append("colors", c));
    p.set("color_threshold", String(filters.color_threshold ?? 50));
  }
  const q = p.toString();
  return q ? `?${q}` : "";
}

export const api = {
  health: () => request<Health>(`/health`),
  scanFolder: (folder: string) =>
    postJson<{ files: string[]; skipped: ImportSummary["skipped"] }>(`/import/scan`, { folder }),
  importFiles: (paths: string[]) => postJson<ImportSummary>(`/import/files`, { paths }),
  backup: (destination: string) => postJson<BackupResult>(`/backup`, { destination }),
  listArtworks: (filters: ArtworkFilters) => request<Artwork[]>(`/artworks/${toSearch(filters)}`),
  getArtwork: (id: string) => request<Artwork>(`/artworks/${id}`),
  extensions: () => request<string[]>(`/artworks/extensions`),
  listTags: () => request<Tag[]>(`/tags/`),
  createTag: (name: string) =>
    request<Tag>(`/tags/`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ name }),
    }),
  deleteTag: (id: number) => request<void>(`/tags/${id}`, { method: "DELETE" }),
  deleteArtworks: (ids: string[]) =>
    request<boolean>(`/artworks/`, {
      method: "DELETE",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ artwork_ids: ids }),
    }),
  updateArtwork: (
    id: string,
    patch: {
      subject?: Subject | null;
      image_type?: ImageType | null;
      art_technique?: Technique | null;
      tag_ids?: number[];
      reviewed?: boolean;
    },
  ) => {
    const p = new URLSearchParams();
    if (patch.subject) p.set("subject", patch.subject);
    if (patch.image_type) p.set("image_type", patch.image_type);
    if (patch.art_technique) p.set("art_technique", patch.art_technique);
    if (typeof patch.reviewed === "boolean") p.set("reviewed", String(patch.reviewed));
    patch.tag_ids?.forEach((id2) => p.append("tag_ids", String(id2)));
    const q = p.toString();
    return request<Artwork>(`/artworks/${id}${q ? `?${q}` : ""}`, { method: "PATCH" });
  },
  upload: (files: File[], onProgress?: (pct: number) => void) =>
    new Promise<ImportSummary>((resolve, reject) => {
      const form = new FormData();
      files.forEach((f) => form.append("files", f));
      const xhr = new XMLHttpRequest();
      xhr.open("POST", `${API_BASE}/artworks`);
      xhr.upload.onprogress = (e) => {
        if (e.lengthComputable) onProgress?.(Math.round((e.loaded / e.total) * 100));
      };
      xhr.onload = () => {
        if (xhr.status >= 200 && xhr.status < 300) {
          try {
            resolve(JSON.parse(xhr.responseText));
          } catch {
            reject(new Error("Unexpected response from server"));
          }
        } else reject(new Error(xhr.responseText || `Upload failed (${xhr.status})`));
      };
      xhr.onerror = () => reject(new Error("Network error during upload"));
      xhr.send(form);
    }),
};
