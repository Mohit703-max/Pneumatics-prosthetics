/**
 * Typed API client for the HASTRA backend.
 * All functions throw on network errors; callers handle display.
 */
import { API_V1 } from '@/constants/api';

// ─── Types ────────────────────────────────────────────────────────────────────

export interface Gesture {
  id: number;
  code: string;
  display_name: string;
  description: string | null;
  model_supported: boolean;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface PredictRequest {
  sample_id?: number;
  raw_emg?: number[][];
}

export interface PredictResponse {
  prediction_id: number;
  predicted_code: string;
  predicted_display_name: string | null;
  confidence: number | null;
  inference_mode: 'model' | 'fallback';
  class_probabilities: Record<string, number> | null;
  created_at: string;
}

export interface PredictionHistoryItem {
  prediction_id: number;
  predicted_code: string;
  predicted_display_name: string | null;
  confidence: number | null;
  inference_mode: 'model' | 'fallback';
  sample_id: number | null;
  created_at: string;
}

export interface PredictionHistoryResponse {
  items: PredictionHistoryItem[];
  total: number;
}

export interface HealthResponse {
  status: 'ok' | 'degraded';
  database: 'ok' | 'error';
  database_error: string | null;
  ml: {
    status: 'model_loaded' | 'fallback_active';
    model_classes: string[];
  };
}

// ─── Helpers ──────────────────────────────────────────────────────────────────

async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const url = `${API_V1}${path}`;
  const res = await fetch(url, {
    headers: { 'Content-Type': 'application/json', ...init?.headers },
    ...init,
  });
  if (!res.ok) {
    let detail = `HTTP ${res.status}`;
    try {
      const body = await res.json();
      detail = body.detail ?? detail;
    } catch {
      // ignore parse error
    }
    throw new Error(detail);
  }
  return res.json() as Promise<T>;
}

// ─── Endpoints ────────────────────────────────────────────────────────────────

export const api = {
  health(): Promise<HealthResponse> {
    return apiFetch<HealthResponse>('/health');
  },

  listGestures(): Promise<Gesture[]> {
    return apiFetch<Gesture[]>('/gestures');
  },

  predict(body: PredictRequest): Promise<PredictResponse> {
    return apiFetch<PredictResponse>('/predictions', {
      method: 'POST',
      body: JSON.stringify(body),
    });
  },

  listPredictions(limit = 20, offset = 0): Promise<PredictionHistoryResponse> {
    return apiFetch<PredictionHistoryResponse>(
      `/predictions?limit=${limit}&offset=${offset}`
    );
  },
};
