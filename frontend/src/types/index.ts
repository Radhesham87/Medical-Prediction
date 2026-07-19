export type Role = "admin" | "user";
export type Status = "pending" | "approved" | "rejected";

export interface AuthResponse {
  access_token: string;
  token_type: string;
  role: Role;
  name: string;
}

export interface UserProfile {
  id: number;
  name: string;
  email: string;
  mobile: string;
  college: string;
  city: string;
  state: string;
  role: Role;
  status: Status;
  is_active: boolean;
  registration_date: string;
  last_login: string | null;
  prediction_count: number;
  active_device_count: number;
  modules: Record<string, boolean>;
  usage: Record<string, number>;
}

export interface ModuleStats {
  key: string;
  label: string;
  users_with_access: number;
  unique_users: number;
  predictions: number;
  todays_predictions: number;
  downloads: number;
}

export interface Device {
  id: number;
  device_label: string;
  browser: string;
  os: string;
  ip: string;
  is_active: boolean;
  created_at: string;
  last_seen_at: string;
}

export interface AdminStats {
  todays_by_module: Record<string, number>;
  total_users: number;
  pending_users: number;
  approved_users: number;
  rejected_users: number;
  prediction_count: number;
  todays_predictions: number;
  total_downloads: number;
}

export interface CollegeResult {
  sr_no: number;
  college_code: string;
  college_name: string;
  status: string;
  degree: string;
  neet_score: number | null;
  neet_sml: number | null;
  air: number | null;
  category_rank: string | null;
  chance: "High" | "Moderate" | "Low";
}

export interface PredictionResponse {
  student_name: string;
  mode: "score" | "air" | "sml";
  score: number | null;
  air: number | null;
  sml: number | null;
  gender: string;
  category: string;
  show_category_rank: boolean;
  generated_at: string;
  results: CollegeResult[];
}

export interface HistoryItem {
  id: number;
  student_name: string;
  mode: "score" | "air";
  score: number | null;
  air: number | null;
  gender: string;
  category: string;
  degrees: string[];
  result_count: number;
  created_at: string;
}

export const CATEGORIES = [
  "OPEN", "OBC", "SEBC", "EWS", "VJA", "NTB", "NTC", "NTD", "SC", "ST", "D1", "D2", "D3",
] as const;

export const DEGREES = ["MBBS", "BDS", "BAMS", "BHMS", "BUMS", "BPTH"] as const;
