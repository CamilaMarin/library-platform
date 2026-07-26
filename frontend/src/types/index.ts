// === Auth ===
export interface LoginResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

export interface RegisterRequest {
  name: string;
  email: string;
  password: string;
  consent_policy_version: string;
  consent_purpose: string;
}

export interface UserInfo {
  id: string;
  name: string;
  email: string;
}

// === Library ===
export interface Book {
  id: string;
  title: string;
  author: string;
  genres: string[];
  description: string | null;
  pages: number | null;
  isbn: string | null;
  created_at: string;
}

export interface CreateBookRequest {
  title: string;
  author: string;
  genres?: string[];
  description?: string;
  pages?: number;
  isbn?: string;
}

export interface Copy {
  id: string;
  book_id: string;
  user_id: string;
  format: "physical" | "digital";
  filename: string | null;
  created_at: string;
}

// === Groups ===
export interface FamilyGroup {
  id: string;
  name: string;
  created_at: string;
}

export interface GroupMembership {
  id: string;
  group_id: string;
  user_id: string;
  status: "pending" | "accepted";
  created_at: string;
}

// === Reading Selection ===
export interface Draw {
  id: string;
  group_id: string;
  filters: Record<string, unknown>;
  participants: string[];
  result_book_id: string | null;
  result_source_user_id: string | null;
  timestamp: string;
}

export interface NextPicker {
  next_picker_user_id: string | null;
}

export interface RunDrawRequest {
  participant_ids: string[];
  genre?: string;
  max_pages?: number;
  unread_only?: boolean;
}

// === Reviews ===
export interface Review {
  id: string;
  user_id: string;
  book_id: string;
  rating: number; // 1–5
  text: string | null;
  visibility: "private" | "shared";
  shared_with_type: "group" | "club" | null;
  shared_with_id: string | null;
  created_at: string;
  updated_at: string;
}

export interface CreateReviewRequest {
  book_id: string;
  rating: number;
  text?: string;
  visibility: "private" | "shared";
  shared_with_type?: "group" | "club";
  shared_with_id?: string;
}

// === Settings / Privacy ===
export interface ExportData {
  user: { name: string; email: string; created_at: string };
  consents: Array<{
    id: string;
    timestamp: string;
    policy_version: string;
    purpose: string;
  }>;
  memberships: Array<{
    id: string;
    group_id: string;
    status: string;
    created_at: string;
  }>;
  processing_records: Array<{
    id: string;
    data_type: string;
    purpose: string;
    legal_basis: string;
    collected_at: string;
    retention_expires_at: string;
  }>;
}

// === API Error ===
export interface ApiError {
  status: number;
  detail: string | Record<string, string>;
}
