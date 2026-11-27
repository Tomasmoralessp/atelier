import { readTextFile, writeTextFile, exists, mkdir } from "@tauri-apps/plugin-fs";
import { appConfigDir, join } from "@tauri-apps/api/path";

const CONFIG_FILENAME = "atelier-config.json";

export type AppMode = "local" | "remote";

export interface AppConfig {
  /** local: the app runs its own backend; remote: it talks to a server (e.g. a NAS). */
  mode: AppMode;
  /** Library folder in local mode; null means the platform default. */
  dataDir: string | null;
  /** Server URL in remote mode. */
  apiBase: string;
  /** Last folder used for backups. */
  backupDir: string | null;
}

export const DEFAULT_CONFIG: AppConfig = {
  mode: "local",
  dataDir: null,
  apiBase: "",
  backupDir: null,
};

/** The config the app is currently running with (set once at startup). */
export let currentConfig: AppConfig = DEFAULT_CONFIG;

async function getConfigPath(): Promise<string> {
  const dir = await appConfigDir();
  await mkdir(dir, { recursive: true });
  return join(dir, CONFIG_FILENAME);
}

export async function loadConfig(): Promise<AppConfig> {
  const path = await getConfigPath();
  let stored: Partial<AppConfig> = {};
  if (await exists(path)) {
    try {
      stored = JSON.parse(await readTextFile(path));
    } catch {
      stored = {};
    }
  }
  // Configs written before local mode existed only had apiBase pointing at a
  // backend the user had to start by hand; they become local mode.
  const mode: AppMode = stored.mode === "remote" ? "remote" : "local";
  currentConfig = { ...DEFAULT_CONFIG, ...stored, mode };
  return currentConfig;
}

export async function saveConfig(config: AppConfig): Promise<void> {
  const path = await getConfigPath();
  await writeTextFile(path, JSON.stringify(config, null, 2));
  currentConfig = config;
}
