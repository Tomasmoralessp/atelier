import { invoke } from "@tauri-apps/api/core";
import { api, setApiBase } from "@/lib/api";
import type { AppConfig } from "@/lib/config";

// The first launch after install is slow: macOS verifies every bundled
// library of the backend once. Later launches take a few seconds.
const LOCAL_START_TIMEOUT_MS = 180_000;
const REMOTE_TIMEOUT_MS = 10_000;

async function waitForHealth(base: string, timeoutMs: number) {
  const deadline = Date.now() + timeoutMs;
  let lastError: unknown;
  while (Date.now() < deadline) {
    try {
      return await api.health(base);
    } catch (e) {
      lastError = e;
      await new Promise((r) => setTimeout(r, 500));
    }
  }
  throw lastError instanceof Error ? lastError : new Error("Backend did not respond");
}

export async function resolveDataDir(config: AppConfig): Promise<string> {
  return config.dataDir ?? (await invoke<string>("default_data_dir"));
}

/**
 * Start the local backend and point the API client at the library.
 * In remote mode the local backend still runs: it classifies imports and
 * uploads them to the server, while browsing talks to the server directly.
 */
export async function connectBackend(config: AppConfig) {
  const serverUrl = config.mode === "remote" ? config.apiBase.replace(/\/+$/, "") : null;
  if (config.mode === "remote" && !serverUrl) throw new Error("No server URL configured");

  const dataDir = await resolveDataDir(config);
  const localUrl = await invoke<string>("start_backend", { dataDir, serverUrl });
  setApiBase(serverUrl ?? localUrl, localUrl);

  if (serverUrl) {
    try {
      await waitForHealth(serverUrl, REMOTE_TIMEOUT_MS);
    } catch {
      throw new Error(`Could not reach the server at ${serverUrl}. Is it on and reachable?`);
    }
  }
  return waitForHealth(localUrl, LOCAL_START_TIMEOUT_MS);
}
