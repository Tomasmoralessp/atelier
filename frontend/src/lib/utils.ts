import { clsx, type ClassValue } from "clsx";
import { isTauri as checkIsTauri } from "@tauri-apps/api/core";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export const isTauri = checkIsTauri();
