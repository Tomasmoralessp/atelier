import { invoke } from "@tauri-apps/api/core";
import { api, setApiBase } from "@/lib/api";
import type { AppConfig } from "@/lib/config";

// The first launch after install is slow: macOS verifies every bundled
// library of the backend once. Later launches take a few seconds.
const LOCAL_START_TIMEOUT_MS = 180_000;
const REMOTE_TIMEOUT_MS = 10_000;

async function waitForHealth(timeoutMs: number) {
  const deadline = Date.now() + timeoutMs;
  let lastError: unknown;
  while (Date.now() < deadline) {
    try {
      return await api.health();
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

/** Start (local) or reach (remote) the backend and point the API client at it. */
export async function connectBackend(config: AppConfig) {
  if (config.mode === "remote") {
    if (!config.apiBase) throw new Error("No server URL configured");
    setApiBase(config.apiBase.replace(/\/+$/, ""));
    return waitForHealth(REMOTE_TIMEOUT_MS);
  }
  const dataDir = await resolveDataDir(config);
  setApiBase(await invoke<string>("start_backend", { dataDir }));
  return waitForHealth(LOCAL_START_TIMEOUT_MS);
}
