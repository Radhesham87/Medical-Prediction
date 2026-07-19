import { getToken, clearAuth } from "@/lib/auth";
import type {
  AdminStats,
  AuthResponse,
  HistoryItem,
  PredictionResponse,
  UserProfile,
} from "@/types";

const BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api";

class ApiError extends Error {
  status: number;
  constructor(message: string, status: number) {
    super(message);
    this.status = status;
  }
}

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const token = getToken();
  const headers = new Headers(options.headers);
  if (token) headers.set("Authorization", `Bearer ${token}`);
  if (!(options.body instanceof FormData) && options.body) {
    headers.set("Content-Type", "application/json");
  }

  const res = await fetch(`${BASE}${path}`, { ...options, headers });

  if (res.status === 401) {
    clearAuth();
    throw new ApiError("Session expired. Please log in again.", 401);
  }
  if (!res.ok) {
    let detail = `Request failed (${res.status})`;
    try {
      const data = await res.json();
      detail = typeof data.detail === "string" ? data.detail : detail;
    } catch {
      /* ignore */
    }
    throw new ApiError(detail, res.status);
  }
  if (res.status === 204) return undefined as T;
  return res.json();
}

async function download(path: string, filename: string) {
  const token = getToken();
  const res = await fetch(`${BASE}${path}`, {
    headers: token ? { Authorization: `Bearer ${token}` } : undefined,
  });
  if (!res.ok) throw new ApiError(`Download failed (${res.status})`, res.status);
  const blob = await res.blob();
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  a.click();
  URL.revokeObjectURL(url);
}

async function downloadPost(path: string, payload: unknown, filename: string) {
  const token = getToken();
  const res = await fetch(`${BASE}${path}`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
    body: JSON.stringify(payload),
  });
  if (!res.ok) throw new ApiError(`Download failed (${res.status})`, res.status);
  const blob = await res.blob();
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  a.click();
  URL.revokeObjectURL(url);
}

export type ModuleKey = "aiims" | "all-india" | "deemed";

export interface InstituteOptions {
  states: string[];
  categories: string[];
  degrees: string[];
}

export interface InstitutePredictPayload {
  student_name: string;
  mode: "score" | "air";
  score?: number;
  air?: number;
  degrees?: string[];
  categories?: string[];
  states?: string[];
}

export interface InstituteResultRow {
  sr_no: number;
  institute_name: string;
  state_name: string;
  degree: string | null;
  category: string | null;
  air: number;
  score: number;
  chance: "High" | "Moderate" | "Low";
}

export interface InstitutePredictResult {
  module: string;
  student_name: string;
  mode: "score" | "air";
  score: number | null;
  air: number | null;
  generated_at: string;
  show_degree: boolean;
  show_category: boolean;
  results: InstituteResultRow[];
}

export interface RegisterPayload {
  name: string;
  email: string;
  mobile: string;
  password: string;
  confirm_password: string;
  college: string;
  city: string;
  state: string;
}

export interface PredictPayload {
  student_name: string;
  mode: "score" | "air" | "sml";
  score?: number;
  air?: number;
  sml?: number;
  degrees: string[];
  gender: "Male" | "Female";
  category: string;
}

export const api = {
  ApiError,

  async login(email: string, password: string): Promise<AuthResponse> {
    const body = new URLSearchParams({ username: email, password });
    const res = await fetch(`${BASE}/auth/login`, {
      method: "POST",
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
      body,
    });
    if (!res.ok) {
      const data = await res.json().catch(() => ({}));
      throw new ApiError(data.detail ?? "Login failed", res.status);
    }
    return res.json();
  },

  register: (payload: RegisterPayload) =>
    request<{ message: string; status: string }>("/auth/register", {
      method: "POST",
      body: JSON.stringify(payload),
    }),

  me: () => request<UserProfile>("/users/me"),

  predict: (payload: PredictPayload) =>
    request<PredictionResponse>("/predict", {
      method: "POST",
      body: JSON.stringify(payload),
    }),

  history: () => request<HistoryItem[]>("/history"),
  deleteHistory: (id: number) => request<void>(`/history/${id}`, { method: "DELETE" }),
  downloadPdf: (id: number, student: string) =>
    download(`/predict/${id}/pdf`, `NEET_Prediction_${student.replace(/\s+/g, "_")}_${id}.pdf`),

  // ---- Institute modules (AIIMS / All-India / Deemed) ----
  instituteOptions: (module: ModuleKey) =>
    request<InstituteOptions>(`/institute/${module}/options`),
  institutePredict: (module: ModuleKey, payload: InstitutePredictPayload) =>
    request<InstitutePredictResult>(`/institute/${module}/predict`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  institutePdf: (module: ModuleKey, result: InstitutePredictResult) =>
    downloadPost(
      `/institute/${module}/pdf`,
      {
        module,
        student_name: result.student_name,
        mode: result.mode,
        score: result.score,
        air: result.air,
        show_degree: result.show_degree,
        show_category: result.show_category,
        results: result.results,
      },
      `${module}_prediction_${result.student_name.replace(/\s+/g, "_")}.pdf`
    ),

  // ---- Admin ----
  adminStats: () => request<AdminStats>("/admin/stats"),
  adminUsers: (status?: string) =>
    request<UserProfile[]>(`/admin/users${status ? `?status_filter=${status}` : ""}`),
  approve: (id: number) => request<UserProfile>(`/admin/users/${id}/approve`, { method: "POST" }),
  reject: (id: number) => request<UserProfile>(`/admin/users/${id}/reject`, { method: "POST" }),
  enable: (id: number) => request<UserProfile>(`/admin/users/${id}/enable`, { method: "POST" }),
  disable: (id: number) => request<UserProfile>(`/admin/users/${id}/disable`, { method: "POST" }),
  deleteUser: (id: number) => request<void>(`/admin/users/${id}`, { method: "DELETE" }),
  resetPassword: (id: number, new_password: string) =>
    request<UserProfile>(`/admin/users/${id}/reset-password`, {
      method: "POST",
      body: JSON.stringify({ new_password }),
    }),
  exportUsers: () => download("/admin/export/users.xlsx", "Registered_Users.xlsx"),
  exportPredictions: () => download("/admin/export/predictions.xlsx", "Predictions.xlsx"),
  adminModuleStats: () => request<import("@/types").ModuleStats[]>("/admin/module-stats"),
  adminUserDevices: (id: number) => request<import("@/types").Device[]>(`/admin/users/${id}/devices`),
  revokeDevice: (id: number, sessionId: number) =>
    request<void>(`/admin/users/${id}/devices/${sessionId}`, { method: "DELETE" }),
  setUserModules: (
    id: number,
    modules: { aiims: boolean; all_india: boolean; maharashtra: boolean; deemed: boolean }
  ) =>
    request<UserProfile>(`/admin/users/${id}/modules`, {
      method: "PUT",
      body: JSON.stringify(modules),
    }),
  adminHistory: (search?: string, sort: "asc" | "desc" = "desc") =>
    request<HistoryItem[]>(
      `/admin/history?sort=${sort}${search ? `&search=${encodeURIComponent(search)}` : ""}`
    ),
  datasetStats: () =>
    request<{ valid_rows: number; colleges: number; degrees: string[]; loaded_at: string | null }>(
      "/dataset/stats"
    ),
};

export { ApiError };
