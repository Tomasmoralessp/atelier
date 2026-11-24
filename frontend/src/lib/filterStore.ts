import type { ArtworkFilters } from "./api";

const KEY = "atelier-filters";

export function saveFilters(filters: ArtworkFilters) {
  if (typeof window === "undefined") return;
  sessionStorage.setItem(KEY, JSON.stringify(filters));
}

export function loadFilters(): ArtworkFilters {
  if (typeof window === "undefined") return {};
  try {
    return JSON.parse(sessionStorage.getItem(KEY) ?? "{}") as ArtworkFilters;
  } catch {
    return {};
  }
}
