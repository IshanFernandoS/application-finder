const defaultBackendUrl = "http://localhost:8000";
const browserProxyBase = "/api/backend";

function apiUrl(path: string) {
  const cleanPath = path.startsWith("/") ? path : `/${path}`;
  const configuredBaseUrl =
    typeof window === "undefined"
      ? process.env.BACKEND_URL || absoluteUrl(process.env.NEXT_PUBLIC_BACKEND_URL) || defaultBackendUrl
      : process.env.NEXT_PUBLIC_BACKEND_URL || browserProxyBase;
  const baseUrl = configuredBaseUrl.replace(/\/$/, "");
  return baseUrl.endsWith("/api/backend") ? `${baseUrl}${cleanPath}` : `${baseUrl}/api${cleanPath}`;
}

function absoluteUrl(value?: string) {
  return value?.startsWith("http://") || value?.startsWith("https://") ? value : undefined;
}

export async function apiGet<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(apiUrl(path), {
    ...init,
    next: { revalidate: 10 },
    headers: {
      "content-type": "application/json",
      ...(init?.headers || {})
    }
  });
  if (!response.ok) {
    const detail = await response.text();
    throw new Error(detail || `API request failed: ${response.status}`);
  }
  return response.json() as Promise<T>;
}

export async function apiPost<T>(path: string, body?: unknown, init?: RequestInit): Promise<T> {
  const headers = body === undefined ? init?.headers : { "content-type": "application/json", ...(init?.headers || {}) };
  const response = await fetch(apiUrl(path), {
    method: "POST",
    body: body === undefined ? undefined : JSON.stringify(body),
    cache: "no-store",
    ...init,
    headers
  });
  if (!response.ok) {
    const detail = await response.text();
    throw new Error(detail || `API request failed: ${response.status}`);
  }
  return response.json() as Promise<T>;
}

export async function apiUpload<T>(path: string, body: FormData, init?: RequestInit): Promise<T> {
  const response = await fetch(apiUrl(path), {
    method: "POST",
    body,
    cache: "no-store",
    ...init
  });
  if (!response.ok) {
    const detail = await response.text();
    throw new Error(detail || `API request failed: ${response.status}`);
  }
  return response.json() as Promise<T>;
}
