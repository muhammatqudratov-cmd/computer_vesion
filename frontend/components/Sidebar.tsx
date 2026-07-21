"use client";

import { useState } from "react";
import type { HistoryEntry } from "@/lib/types";

interface SidebarProps {
  username: string;
  history: HistoryEntry[];
  selectedId: number | null;
  onSelect: (entry: HistoryEntry) => void;
  onLogout: () => void;
}

function formatTime(iso: string) {
  const normalized = iso.includes("T") ? iso : `${iso.replace(" ", "T")}Z`;
  const date = new Date(normalized);
  if (Number.isNaN(date.getTime())) return iso;
  return date.toLocaleString("uz-UZ", {
    day: "2-digit",
    month: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  });
}

export default function Sidebar({
  username,
  history,
  selectedId,
  onSelect,
  onLogout,
}: SidebarProps) {
  const [collapsed, setCollapsed] = useState(false);

  if (collapsed) {
    return (
      <div className="flex h-full w-12 flex-col items-center border-r border-neutral-800 bg-neutral-950 py-3">
        <button
          onClick={() => setCollapsed(false)}
          className="rounded-md p-2 text-neutral-400 hover:bg-neutral-800 hover:text-white"
          title="Tarixni ochish"
        >
          »
        </button>
      </div>
    );
  }

  return (
    <div className="flex h-full w-72 shrink-0 flex-col border-r border-neutral-800 bg-neutral-950 text-neutral-100">
      <div className="flex items-center justify-between border-b border-neutral-800 px-4 py-3">
        <span className="text-sm font-semibold">Mahsulot Detektor</span>
        <button
          onClick={() => setCollapsed(true)}
          className="rounded-md p-1 text-neutral-400 hover:bg-neutral-800 hover:text-white"
          title="Tarixni yopish"
        >
          «
        </button>
      </div>

      <div className="flex-1 overflow-y-auto px-2 py-3">
        <p className="mb-2 px-2 text-xs font-medium uppercase tracking-wide text-neutral-500">
          Tarix
        </p>
        {history.length === 0 && (
          <p className="px-2 text-sm text-neutral-500">
            Hali hech narsa aniqlanmagan.
          </p>
        )}
        <ul className="space-y-1">
          {history.map((entry) => (
            <li key={entry.id}>
              <button
                onClick={() => onSelect(entry)}
                className={`w-full rounded-lg px-3 py-2 text-left text-sm transition-colors ${
                  selectedId === entry.id
                    ? "bg-neutral-800 text-white"
                    : "text-neutral-300 hover:bg-neutral-900"
                }`}
              >
                <div className="truncate font-medium">{entry.object_name}</div>
                <div className="truncate text-xs text-neutral-500">
                  {entry.guess_label} · {formatTime(entry.created_at)}
                </div>
              </button>
            </li>
          ))}
        </ul>
      </div>

      <div className="flex items-center justify-between border-t border-neutral-800 px-4 py-3">
        <span className="truncate text-sm text-neutral-300">{username}</span>
        <button
          onClick={onLogout}
          className="rounded-md px-2 py-1 text-xs font-medium text-neutral-400 hover:bg-neutral-800 hover:text-white"
        >
          Chiqish
        </button>
      </div>
    </div>
  );
}
