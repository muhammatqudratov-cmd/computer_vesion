export interface DetectedObject {
  box: [number, number, number, number];
  name: string;
  guess_label: string;
  matched: boolean;
}

export interface StreamMessage {
  frame?: string;
  objects?: DetectedObject[];
  error?: string;
}

export interface HistoryEntry {
  id: number;
  user_id: number;
  object_name: string;
  guess_label: string;
  info_text: string;
  created_at: string;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
}

export interface MeResponse {
  username: string;
}

export interface InfoResponse {
  name: string;
  info: string;
  cached: boolean;
}
