import { useState } from "react";
import { Settings } from "lucide-react";
import { toast } from "sonner";
import { open as openDialog } from "@tauri-apps/plugin-dialog";
import { currentConfig, saveConfig, type AppConfig, type AppMode } from "@/lib/config";
import { resolveDataDir } from "@/lib/startup";
import { api } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Separator } from "@/components/ui/separator";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";

async function pickFolder(title: string): Promise<string | null> {
  const selected = await openDialog({ directory: true, multiple: false, title });
  return typeof selected === "string" ? selected : null;
}

function ModeButton({
  mode,
  current,
  onSelect,
  children,
}: {
  mode: AppMode;
  current: AppMode;
  onSelect: (mode: AppMode) => void;
  children: React.ReactNode;
}) {
  return (
    <Button
      type="button"
      size="sm"
      variant={mode === current ? "default" : "outline"}
      onClick={() => onSelect(mode)}
      className="flex-1"
    >
      {children}
    </Button>
  );
}

export function SettingsDialog() {
  const [open, setOpen] = useState(false);
  const [draft, setDraft] = useState<AppConfig>(currentConfig);
  const [dataDir, setDataDir] = useState("");
  const [backingUp, setBackingUp] = useState(false);

  const handleOpenChange = (next: boolean) => {
    if (next) {
      setDraft(currentConfig);
      void resolveDataDir(currentConfig).then(setDataDir);
    }
    setOpen(next);
  };

  const needsRestart =
    draft.mode !== currentConfig.mode ||
    (draft.mode === "local" && draft.dataDir !== currentConfig.dataDir) ||
    (draft.mode === "remote" && draft.apiBase !== currentConfig.apiBase);

  const chooseDataDir = async () => {
    const folder = await pickFolder("Choose where Atelier keeps your library");
    if (folder) {
      setDraft({ ...draft, dataDir: folder });
      setDataDir(folder);
    }
  };

  const handleSave = async () => {
    if (draft.mode === "remote" && !/^https?:\/\//.test(draft.apiBase)) {
      toast.error("Server URL must start with http:// or https://");
      return;
    }
    await saveConfig(draft);
    setOpen(false);
    if (needsRestart) window.location.reload();
  };

  const backUp = async (chooseFolder: boolean) => {
    let destination = currentConfig.backupDir;
    if (chooseFolder || !destination) {
      destination = await pickFolder("Choose a backup folder (external disk, NAS share…)");
      if (!destination) return;
      await saveConfig({ ...currentConfig, backupDir: destination });
      setDraft((d) => ({ ...d, backupDir: destination }));
    }
    setBackingUp(true);
    try {
      const result = await api.backup(destination);
      toast.success(`Backup saved to ${result.backup_dir} (${result.files_copied} new files)`);
    } catch (e) {
      toast.error(e instanceof Error ? e.message : "Backup failed");
    } finally {
      setBackingUp(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={handleOpenChange}>
      <DialogTrigger asChild>
        <Button variant="ghost" size="sm" aria-label="Settings">
          <Settings className="size-4" />
        </Button>
      </DialogTrigger>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Settings</DialogTitle>
          <DialogDescription>Where Atelier keeps your library.</DialogDescription>
        </DialogHeader>

        <div className="space-y-2">
          <Label>Library</Label>
          <div className="flex gap-2">
            <ModeButton mode="local" current={draft.mode} onSelect={(mode) => setDraft({ ...draft, mode })}>
              On this computer
            </ModeButton>
            <ModeButton mode="remote" current={draft.mode} onSelect={(mode) => setDraft({ ...draft, mode })}>
              On a server
            </ModeButton>
          </div>
        </div>

        {draft.mode === "local" ? (
          <div className="space-y-2">
            <Label>Data folder</Label>
            <div className="flex gap-2">
              <Input value={dataDir} readOnly className="font-mono text-xs" />
              <Button variant="outline" onClick={chooseDataDir}>
                Change…
              </Button>
            </div>
            <p className="text-xs text-muted-foreground">
              Holds the database and all imported images. A new folder starts an empty library.
            </p>
          </div>
        ) : (
          <div className="space-y-2">
            <Label>Server URL</Label>
            <Input
              value={draft.apiBase}
              onChange={(e) => setDraft({ ...draft, apiBase: e.target.value })}
              placeholder="http://192.168.1.20:8000"
            />
          </div>
        )}

        <Button onClick={handleSave}>{needsRestart ? "Save and restart" : "Save"}</Button>

        {currentConfig.mode === "local" && (
          <>
            <Separator />
            <div className="space-y-2">
              <Label>Backup</Label>
              <p className="text-xs text-muted-foreground">
                Copies the database and any new images to{" "}
                <span className="font-mono">{currentConfig.backupDir ?? "a folder you choose"}</span>.
                A shared folder on your NAS works too.
              </p>
              <div className="flex gap-2">
                <Button variant="outline" disabled={backingUp} onClick={() => backUp(false)}>
                  {backingUp ? "Backing up…" : "Back up now"}
                </Button>
                {currentConfig.backupDir && (
                  <Button variant="ghost" disabled={backingUp} onClick={() => backUp(true)}>
                    Change folder…
                  </Button>
                )}
              </div>
            </div>
          </>
        )}
      </DialogContent>
    </Dialog>
  );
}
