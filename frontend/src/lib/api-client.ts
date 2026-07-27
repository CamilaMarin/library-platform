import {
  getAccessToken,
  getRefreshToken,
  setTokens,
  clearTokens,
} from "./token-storage";

// === Toast handler (injectable, registered later by ToastContext) ===

let toastHandler: ((message: string, type: "error") => void) | null = null;

export function setToastHandler(
  handler: (message: string, type: "error") => void
): void {
  toastHandler = handler;
}

// === ApiError class ===

export class ApiError extends Error {
  status: number;
  detail: string | Record<string, string>;

  constructor(status: number, detail: string | Record<string, string>) {
    super(typeof detail === "string" ? detail : JSON.stringify(detail));
    this.name = "ApiError";
    this.status = status;
    this.detail = detail;
  }
}

// === Configuration ===

const BASE_URL =
  process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

// === Token refresh logic ===

let refreshPromise: Promise<boolean> | null = null;

async function attemptTokenRefresh(): Promise<boolean> {
  // Deduplicate concurrent refresh attempts
  if (refreshPromise) return refreshPromise;

  refreshPromise = (async () => {
    const refreshToken = getRefreshToken();
    if (!refreshToken) return false;

    try {
      const formData = new URLSearchParams();
      formData.append("refresh_token", refreshToken);

      const res = await fetch(`${BASE_URL}/auth/refresh`, {
        method: "POST",
        headers: { "Content-Type": "application/x-www-form-urlencoded" },
        body: formData.toString(),
      });

      if (!res.ok) return false;

      const data = await res.json();
      setTokens(data.access_token, data.refresh_token);
      return true;
    } catch {
      return false;
    }
  })();

  try {
    return await refreshPromise;
  } finally {
    refreshPromise = null;
  }
}

function handleRefreshFailure(): never {
  clearTokens();
  if (typeof window !== "undefined") {
    window.location.href = "/login";
  }
  throw new Error("Session expired");
}

// === Core fetch wrapper ===

async function request<T>(
  path: string,
  options: RequestInit,
  isRetry = false
): Promise<T> {
  const token = getAccessToken();
  const headers: Record<string, string> = {
    ...(options.headers as Record<string, string>),
  };

  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }

  let res: Response;

  try {
    res = await fetch(`${BASE_URL}${path}`, {
      ...options,
      headers,
    });
  } catch {
    // Network error (fetch threw)
    if (toastHandler) {
      toastHandler("No se pudo conectar al servidor.", "error");
    }
    throw new ApiError(0, "No se pudo conectar al servidor.");
  }

  // 401 — attempt refresh and retry once
  if (res.status === 401 && !isRetry) {
    const refreshed = await attemptTokenRefresh();
    if (refreshed) {
      return request<T>(path, options, true);
    }
    handleRefreshFailure();
  }

  if (res.status === 401 && isRetry) {
    handleRefreshFailure();
  }

  // 4xx (non-401) — throw ApiError with parsed body
  if (res.status >= 400 && res.status < 500) {
    let detail: string | Record<string, string>;
    try {
      detail = await res.json();
    } catch {
      detail = "Error del servidor";
    }
    throw new ApiError(res.status, detail);
  }

  // 5xx — toast with generic server error
  if (res.status >= 500) {
    if (toastHandler) {
      toastHandler(
        "Error de servidor. Intenta de nuevo más tarde.",
        "error"
      );
    }
    throw new ApiError(
      res.status,
      "Error de servidor. Intenta de nuevo más tarde."
    );
  }

  // Success — parse JSON (or return void for 204)
  if (res.status === 204 || res.headers.get("content-length") === "0") {
    return undefined as unknown as T;
  }

  return res.json() as Promise<T>;
}

// === Public API functions ===

export async function apiGet<T>(path: string): Promise<T> {
  return request<T>(path, {
    method: "GET",
    headers: { "Content-Type": "application/json" },
  });
}

export async function apiPost<T>(path: string, body?: unknown): Promise<T> {
  return request<T>(path, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: body !== undefined ? JSON.stringify(body) : undefined,
  });
}

export async function apiPatch<T>(path: string, body?: unknown): Promise<T> {
  return request<T>(path, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: body !== undefined ? JSON.stringify(body) : undefined,
  });
}

export async function apiDelete(path: string): Promise<void> {
  return request<void>(path, {
    method: "DELETE",
    headers: { "Content-Type": "application/json" },
  });
}

export async function apiPostForm<T>(
  path: string,
  formData: FormData
): Promise<T> {
  // Do not set Content-Type — browser sets multipart boundary automatically
  return request<T>(path, {
    method: "POST",
    body: formData,
  });
}
