"use client";
import { useEffect } from "react";

type Modifier = "ctrl" | "meta" | "shift" | "alt";

interface ShortcutOptions {
  key: string;
  modifiers?: Modifier[];
  onTrigger: () => void;
  preventDefault?: boolean;
}

export function useKeyboardShortcut({
  key,
  modifiers = [],
  onTrigger,
  preventDefault = true,
}: ShortcutOptions) {
  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      const ctrlOrMeta = modifiers.includes("ctrl") || modifiers.includes("meta");
      const shiftRequired = modifiers.includes("shift");
      const altRequired = modifiers.includes("alt");

      const metaMatch = ctrlOrMeta ? (e.ctrlKey || e.metaKey) : true;
      const shiftMatch = shiftRequired ? e.shiftKey : !e.shiftKey;
      const altMatch = altRequired ? e.altKey : !e.altKey;

      if (e.key.toLowerCase() === key.toLowerCase() && metaMatch && shiftMatch && altMatch) {
        if (preventDefault) e.preventDefault();
        onTrigger();
      }
    };

    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, [key, modifiers, onTrigger, preventDefault]);
}
