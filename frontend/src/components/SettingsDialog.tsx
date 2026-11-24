import { useState } from "react";
import { Settings } from "lucide-react";
import { toast } from "sonner";
import { loadConfig, saveConfig } from "@/lib/config";
import { setApiBase, API_BASE } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";

export function SettingsDialog() {
  const [apiBase, setApiBaseInput] = useState(API_BASE);
  const [open, setOpen] = useState(false);

  const handleSave = async () => {
    await saveConfig({ apiBase });
    setApiBase(apiBase);
    toast.success("Settings saved. Restart the app to apply.");
    setOpen(false);
  };

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button variant="ghost" size="sm">
          <Settings className="size-4" />
        </Button>
      </DialogTrigger>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Settings</DialogTitle>
        </DialogHeader>
        <div className="space-y-2">
          <Label>Backend URL</Label>
          <Input
            value={apiBase}
            onChange={(e) => setApiBaseInput(e.target.value)}
            placeholder="http://127.0.0.1:8000"
          />
        </div>
        <Button onClick={handleSave}>Save</Button>
      </DialogContent>
    </Dialog>
  );
}
