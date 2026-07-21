"use client";

import { useEffect, useRef, useState } from "react";
import { ApiError, postInfo, wsStreamUrl } from "@/lib/api";
import type { DetectedObject, HistoryEntry, StreamMessage } from "@/lib/types";

interface CameraPanelProps {
  selectedEntry: HistoryEntry | null;
  onInfoSaved: () => void;
  onClearSelection: () => void;
}

interface DisplayedInfo {
  name: string;
  info: string;
}

function cropToBlob(canvas: HTMLCanvasElement, box: [number, number, number, number]): Promise<Blob> {
  const [x1, y1, x2, y2] = box;
  const width = Math.max(1, x2 - x1);
  const height = Math.max(1, y2 - y1);

  const cropCanvas = document.createElement("canvas");
  cropCanvas.width = width;
  cropCanvas.height = height;
  const ctx = cropCanvas.getContext("2d");
  if (!ctx) return Promise.reject(new Error("Canvas context topilmadi"));
  ctx.drawImage(canvas, x1, y1, width, height, 0, 0, width, height);

  return new Promise((resolve, reject) => {
    cropCanvas.toBlob((blob) => {
      if (blob) resolve(blob);
      else reject(new Error("Rasmni tayyorlab bo'lmadi"));
    }, "image/jpeg");
  });
}

export default function CameraPanel({
  selectedEntry,
  onInfoSaved,
  onClearSelection,
}: CameraPanelProps) {
  const wsRef = useRef<WebSocket | null>(null);
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const frameImgRef = useRef<HTMLImageElement | null>(null);

  const [connecting, setConnecting] = useState(false);
  const [streaming, setStreaming] = useState(false);
  const [streamError, setStreamError] = useState<string | null>(null);
  const [objects, setObjects] = useState<DetectedObject[]>([]);
  const [loadingInfoFor, setLoadingInfoFor] = useState<string | null>(null);
  const [liveInfo, setLiveInfo] = useState<DisplayedInfo | null>(null);
  const [infoError, setInfoError] = useState<string | null>(null);

  useEffect(() => {
    frameImgRef.current = new Image();
  }, []);

  useEffect(() => {
    return () => {
      wsRef.current?.close();
    };
  }, []);

  function startCamera() {
    setStreamError(null);
    setConnecting(true);

    const ws = new WebSocket(wsStreamUrl());
    wsRef.current = ws;

    ws.onopen = () => {
      setConnecting(false);
      setStreaming(true);
    };

    ws.onmessage = (event) => {
      const data: StreamMessage = JSON.parse(event.data);

      if (data.error) {
        setStreamError(data.error);
        return;
      }

      if (data.frame) {
        const img = frameImgRef.current ?? new Image();
        img.onload = () => {
          const canvas = canvasRef.current;
          if (!canvas) return;
          canvas.width = img.width;
          canvas.height = img.height;
          const ctx = canvas.getContext("2d");
          if (!ctx) return;

          ctx.drawImage(img, 0, 0);
          ctx.lineWidth = 3;
          ctx.strokeStyle = "#22c55e";
          ctx.font = "16px sans-serif";
          ctx.fillStyle = "#22c55e";

          (data.objects ?? []).forEach((obj) => {
            const [x1, y1, x2, y2] = obj.box;
            ctx.strokeRect(x1, y1, x2 - x1, y2 - y1);
            ctx.fillText(obj.name, x1, Math.max(16, y1 - 6));
          });
        };
        img.src = `data:image/jpeg;base64,${data.frame}`;
      }

      setObjects(data.objects ?? []);
    };

    ws.onerror = () => {
      setStreamError("WebSocket xatosi - backend server (port 8000) ishga tushganini tekshiring");
    };

    ws.onclose = () => {
      setStreaming(false);
      setConnecting(false);
    };
  }

  function stopCamera() {
    wsRef.current?.close();
    wsRef.current = null;
    setStreaming(false);
    setObjects([]);
  }

  async function handleGetInfo(obj: DetectedObject) {
    const canvas = canvasRef.current;
    if (!canvas) return;

    setInfoError(null);
    setLoadingInfoFor(obj.name);
    try {
      const blob = await cropToBlob(canvas, obj.box);
      const result = await postInfo(obj.name, obj.guess_label, blob);
      setLiveInfo({ name: result.name, info: result.info });
      onClearSelection();
      onInfoSaved();
    } catch (err) {
      setInfoError(err instanceof ApiError ? err.message : "Ma'lumot olishda xatolik yuz berdi");
    } finally {
      setLoadingInfoFor(null);
    }
  }

  const displayedInfo: DisplayedInfo | null = selectedEntry
    ? { name: selectedEntry.object_name, info: selectedEntry.info_text }
    : liveInfo;

  return (
    <div className="mx-auto flex max-w-3xl flex-col gap-6 px-6 py-8">
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-semibold text-neutral-900">Kamera</h1>
        {!streaming ? (
          <button
            onClick={startCamera}
            disabled={connecting}
            className="rounded-lg bg-neutral-900 px-4 py-2 text-sm font-medium text-white hover:bg-neutral-800 disabled:opacity-50"
          >
            {connecting ? "Ulanmoqda..." : "Kamerani ishga tushirish"}
          </button>
        ) : (
          <button
            onClick={stopCamera}
            className="rounded-lg bg-red-600 px-4 py-2 text-sm font-medium text-white hover:bg-red-500"
          >
            Kamerani to&apos;xtatish
          </button>
        )}
      </div>

      {streamError && (
        <p className="rounded-lg bg-red-50 px-3 py-2 text-sm text-red-700">{streamError}</p>
      )}

      {streaming && (
        <div className="overflow-hidden rounded-xl border border-neutral-200 bg-black">
          <canvas ref={canvasRef} className="w-full max-w-full" />
        </div>
      )}

      {streaming && (
        <div>
          <p className="mb-2 text-sm font-medium text-neutral-700">
            Aniqlangan obyektlar ({objects.length})
          </p>
          {objects.length === 0 ? (
            <p className="text-sm text-neutral-500">Hech narsa aniqlanmadi.</p>
          ) : (
            <ul className="space-y-2">
              {objects.map((obj, idx) => (
                <li
                  key={`${obj.name}-${idx}`}
                  className="flex items-center justify-between rounded-lg border border-neutral-200 px-3 py-2"
                >
                  <div>
                    <div className="text-sm font-medium text-neutral-900">{obj.name}</div>
                    <div className="text-xs text-neutral-500">
                      {obj.matched ? "Tanildi" : "Yangi"} · {obj.guess_label}
                    </div>
                  </div>
                  <button
                    onClick={() => handleGetInfo(obj)}
                    disabled={loadingInfoFor === obj.name}
                    className="rounded-md bg-neutral-100 px-3 py-1.5 text-xs font-medium text-neutral-800 hover:bg-neutral-200 disabled:opacity-50"
                  >
                    {loadingInfoFor === obj.name ? "So'ralmoqda..." : "Ma'lumot olish"}
                  </button>
                </li>
              ))}
            </ul>
          )}
        </div>
      )}

      {infoError && (
        <p className="rounded-lg bg-red-50 px-3 py-2 text-sm text-red-700">{infoError}</p>
      )}

      {displayedInfo && (
        <div className="rounded-xl border border-neutral-200 bg-neutral-50 p-4">
          <div className="mb-2 flex items-center justify-between">
            <h2 className="text-sm font-semibold text-neutral-900">{displayedInfo.name}</h2>
            <button
              onClick={() => {
                setLiveInfo(null);
                onClearSelection();
              }}
              className="text-xs font-medium text-neutral-500 hover:text-neutral-800"
            >
              Yopish
            </button>
          </div>
          <p className="whitespace-pre-wrap text-sm text-neutral-700">{displayedInfo.info}</p>
        </div>
      )}

      {!streaming && !displayedInfo && (
        <p className="text-sm text-neutral-500">
          Boshlash uchun &quot;Kamerani ishga tushirish&quot; tugmasini bosing, yoki chap
          tomondagi tarixdan biror yozuvni tanlang.
        </p>
      )}
    </div>
  );
}
