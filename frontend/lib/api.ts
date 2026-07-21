import type {
  AuthResponse,
  HistoryEntry,
  InfoResponse,
  MeResponse,
} from "./types";

export const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";
export const WS_BASE_URL =
  process.env.NEXT_PUBLIC_WS_BASE_URL ?? "ws://localhost:8000";

const TOKEN_KEY = "access_token";

export class ApiError extends Error {
  status: number;
  constructor(status: number, message: string) {
    super(message);
    this.status = status;
  }
}

export function getToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem(TOKEN_KEY);
}

export function setToken(token: string) {
  localStorage.setItem(TOKEN_KEY, token);
}

export function clearToken() {
  localStorage.removeItem(TOKEN_KEY);
}

export function wsStreamUrl(): string {
  const token = getToken();
  return `${WS_BASE_URL}/ws/stream?token=${encodeURIComponent(token ?? "")}`;
}

async function parseErrorDetail(res: Response, fallback: string): Promise<string> {
  try {
    const body = await res.json();
    return body.detail ?? fallback;
  } catch {
    return fallback;
  }
}

async function authedFetch(path: string, options: RequestInit = {}): Promise<Response> {
  const token = getToken();
  const headers = new Headers(options.headers);
  if (token) headers.set("Authorization", `Bearer ${token}`);
  return fetch(`${API_BASE_URL}${path}`, { ...options, headers });
}

export async function signup(username: string, password: string): Promise<AuthResponse> {
  const res = await fetch(`${API_BASE_URL}/auth/signup`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ username, password }),
  });
  if (!res.ok) {
    throw new ApiError(res.status, await parseErrorDetail(res, "Ro'yxatdan o'tishda xatolik"));
  }
  return res.json();
}

export async function login(username: string, password: string): Promise<AuthResponse> {
  const res = await fetch(`${API_BASE_URL}/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ username, password }),
  });
  if (!res.ok) {
    throw new ApiError(res.status, await parseErrorDetail(res, "Username yoki parol noto'g'ri"));
  }
  return res.json();
}

export async function fetchMe(): Promise<MeResponse> {
  const res = await authedFetch("/auth/me");
  if (!res.ok) {
    throw new ApiError(res.status, await parseErrorDetail(res, "Avtorizatsiya xatosi"));
  }
  return res.json();
}

export async function fetchHistory(): Promise<{ history: HistoryEntry[] }> {
  const res = await authedFetch("/history");
  if (!res.ok) {
    throw new ApiError(res.status, await parseErrorDetail(res, "Tarixni yuklab bo'lmadi"));
  }
  return res.json();
}

export async function postInfo(
  name: string,
  guessLabel: string,
  imageBlob: Blob,
): Promise<InfoResponse> {
  const formData = new FormData();
  formData.append("name", name);
  formData.append("guess_label", guessLabel);
  formData.append("image", imageBlob, "crop.jpg");

  const res = await authedFetch("/info", {
    method: "POST",
    body: formData,
  });
  if (!res.ok) {
    throw new ApiError(res.status, await parseErrorDetail(res, "Ma'lumot olishda xatolik"));
  }
  return res.json();
}
