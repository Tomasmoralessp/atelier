import { remove, exists, mkdir, readDir, writeFile } from "@tauri-apps/plugin-fs";
import { tempDir, join } from "@tauri-apps/api/path";
import { fetch } from "@tauri-apps/plugin-http";

async function getClipboardTempDir(): Promise<string> {
  const base = await tempDir();
  return join(base, "atelier-clipboard");
}

export async function clearClipboardTemp() {
  const dir = await getClipboardTempDir();
  if (await exists(dir)) {
    const entries = await readDir(dir);
    for (const entry of entries) {
      await remove(await join(dir, entry.name!));
    }
  } else {
    await mkdir(dir, { recursive: true });
  }
}

export async function downloadToClipboardTemp(url: string, filename: string): Promise<string> {
  const dir = await getClipboardTempDir();
  const response = await fetch(url);
  const bytes = new Uint8Array(await response.arrayBuffer());
  const destination = await join(dir, filename);
  await writeFile(destination, bytes);
  return destination;
}
