import { useEffect, useRef } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api, type ArtworkFilters } from "./api";

export function useArtworks(filters: ArtworkFilters) {
  return useQuery({
    queryKey: ["artworks", filters],
    queryFn: () => api.listArtworks(filters),
  });
}

export function useArtwork(id: string) {
  return useQuery({ queryKey: ["artwork", id], queryFn: () => api.getArtwork(id) });
}

export function useTags() {
  return useQuery({ queryKey: ["tags"], queryFn: api.listTags });
}

export function useExtensions() {
  return useQuery({ queryKey: ["extensions"], queryFn: api.extensions });
}

export function useInvalidateArtworks() {
  const qc = useQueryClient();
  return () => {
    qc.invalidateQueries({ queryKey: ["artworks"] });
    qc.invalidateQueries({ queryKey: ["artwork"] });
    qc.invalidateQueries({ queryKey: ["extensions"] });
  };
}

export function useUpdateArtwork() {
  const invalidate = useInvalidateArtworks();
  return useMutation({
    mutationFn: ({ id, ...patch }: Parameters<typeof api.updateArtwork>[1] & { id: string }) =>
      api.updateArtwork(id, patch),
    onSuccess: invalidate,
  });
}

export function useCreateTag() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (name: string) => api.createTag(name),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["tags"] }),
  });
}

export function useDeleteTag() {
  const qc = useQueryClient();
  const invalidate = useInvalidateArtworks();
  return useMutation({
    mutationFn: (id: number) => api.deleteTag(id),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["tags"] });
      invalidate();
    },
  });
}

export function useDeleteArtworks() {
  const invalidate = useInvalidateArtworks();
  return useMutation({
    mutationFn: (ids: string[]) => api.deleteArtworks(ids),
    onSuccess: invalidate,
  });
}

// Reloading the whole grid is not free with thousands of pieces, so refresh
// it every REFRESH_STEP classified artworks, and when the queue empties.
const REFRESH_STEP = 40;

/** How many artworks wait to be classified; refreshes the grid as they finish. */
export function useQueue() {
  const invalidate = useInvalidateArtworks();
  const lastRefresh = useRef<number | null>(null);
  const query = useQuery({
    queryKey: ["queue"],
    queryFn: api.queue,
    refetchInterval: 10_000,
  });
  const pending = query.data?.pending ?? 0;
  useEffect(() => {
    const previous = lastRefresh.current;
    if (previous === null || pending > previous) {
      if (previous !== null) invalidate(); // new uploads arrived
      lastRefresh.current = pending;
    } else if (previous - pending >= REFRESH_STEP || (pending === 0 && previous > 0)) {
      invalidate();
      lastRefresh.current = pending;
    }
  }, [pending, invalidate]);
  return pending;
}
