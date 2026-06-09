const baseUrl = process.env.NEXT_PUBLIC_BACKEND_URL || process.env.BACKEND_URL || "http://localhost:8000";

export async function apiGet<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${baseUrl}/api${path}`, {
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
  const response = await fetch(`${baseUrl}/api${path}`, {
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
