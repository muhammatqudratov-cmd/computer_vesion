"use client";

import { useCallback, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { clearToken, fetchHistory, fetchMe, getToken } from "@/lib/api";
import Sidebar from "@/components/Sidebar";
import CameraPanel from "@/components/CameraPanel";
import type { HistoryEntry } from "@/lib/types";

export default function HomePage() {
  const router = useRouter();
  const [checking, setChecking] = useState(true);
  const [username, setUsername] = useState<string | null>(null);
  const [history, setHistory] = useState<HistoryEntry[]>([]);
  const [selectedEntry, setSelectedEntry] = useState<HistoryEntry | null>(null);

  const refreshHistory = useCallback(async () => {
    try {
      const data = await fetchHistory();
      setHistory(data.history);
    } catch {
      // sidebar simply stays as-is if the refresh fails
    }
  }, []);

  useEffect(() => {
    const token = getToken();
    if (!token) {
      router.replace("/login");
      return;
    }

    fetchMe()
      .then((me) => {
        setUsername(me.username);
        setChecking(false);
        refreshHistory();
      })
      .catch(() => {
        clearToken();
        router.replace("/login");
      });
  }, [router, refreshHistory]);

  function handleLogout() {
    clearToken();
    router.replace("/login");
  }

  function handleSelectEntry(entry: HistoryEntry) {
    setSelectedEntry((current) => (current?.id === entry.id ? null : entry));
  }

  if (checking) {
    return (
      <div className="flex min-h-screen items-center justify-center text-sm text-neutral-500">
        Yuklanmoqda...
      </div>
    );
  }

  return (
    <div className="flex h-screen overflow-hidden bg-white">
      <Sidebar
        username={username ?? ""}
        history={history}
        selectedId={selectedEntry?.id ?? null}
        onSelect={handleSelectEntry}
        onLogout={handleLogout}
      />
      <main className="flex-1 overflow-y-auto">
        <CameraPanel
          selectedEntry={selectedEntry}
          onInfoSaved={refreshHistory}
          onClearSelection={() => setSelectedEntry(null)}
        />
      </main>
    </div>
  );
}
