import { useState } from "react";
import { Tags } from "lucide-react";
import { DropdownMenuItem } from "@/components/ui/dropdown-menu";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { TagManager } from "@/components/TagManager";
import { SettingsDialog } from "@/components/SettingsDialog";

export function TagsMenuItem() {
  const [open, setOpen] = useState(false);
  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <DropdownMenuItem onSelect={(e) => e.preventDefault()}>
          <Tags className="size-4" /> Tags
        </DropdownMenuItem>
      </DialogTrigger>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Manage tags</DialogTitle>
        </DialogHeader>
        <TagManager />
      </DialogContent>
    </Dialog>
  );
}

export function SettingsMenuItem() {
  return <SettingsDialog />;
}
