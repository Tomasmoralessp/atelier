import { readTextFile, writeTextFile, exists, mkdir } from "@tauri-apps/plugin-fs";
import { appConfigDir, join } from "@tauri-apps/api/path";

const CONFIG_FILENAME = "atelier-config.json";
const DEFAULT_API_BASE = "http://127.0.0.1:8000";

interface AppConfig {
  apiBase: string;
}

async function getConfigPath(): Promise<string> {
  const dir = await appConfigDir();
  await mkdir(dir, { recursive: true });
  return join(dir, CONFIG_FILENAME);
}

export async function loadConfig(): Promise<AppConfig> {
  const path = await getConfigPath();
  if (await exists(path)) {
    const content = await readTextFile(path);
    return JSON.parse(content);
  }
  return { apiBase: DEFAULT_API_BASE };
}

export async function saveConfig(config: AppConfig): Promise<void> {
  const path = await getConfigPath();
  await writeTextFile(path, JSON.stringify(config, null, 2));
}
