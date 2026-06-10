const defaultBackendUrl = "http://localhost:8000";
const browserProxyBase = "/api/backend";
const transientRetryDelaysMs = [1000, 2500, 5000];

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
  const response = await fetchWithTransientRetry(apiUrl(path), {
    ...init,
    next: { revalidate: 10 },
    headers: {
      "content-type": "application/json",
      ...(init?.headers || {})
    }
  });
  if (!response.ok) {
    const detail = await errorMessage(response);
    throw new Error(detail || `API request failed: ${response.status}`);
  }
  return response.json() as Promise<T>;
}

export async function apiPost<T>(path: string, body?: unknown, init?: RequestInit): Promise<T> {
  const headers = body === undefined ? init?.headers : { "content-type": "application/json", ...(init?.headers || {}) };
  const response = await fetchWithTransientRetry(apiUrl(path), {
    method: "POST",
    body: body === undefined ? undefined : JSON.stringify(body),
    cache: "no-store",
    ...init,
    headers
  });
  if (!response.ok) {
    const detail = await errorMessage(response);
    throw new Error(detail || `API request failed: ${response.status}`);
  }
  return response.json() as Promise<T>;
}

export async function apiUpload<T>(path: string, body: FormData, init?: RequestInit): Promise<T> {
  const response = await fetchWithTransientRetry(apiUrl(path), {
    method: "POST",
    body,
    cache: "no-store",
    ...init
  });
  if (!response.ok) {
    const detail = await errorMessage(response);
    throw new Error(detail || `API request failed: ${response.status}`);
  }
  return response.json() as Promise<T>;
}

async function fetchWithTransientRetry(input: RequestInfo | URL, init?: RequestInit): Promise<Response> {
  let lastError: unknown;
  for (let attempt = 0; attempt <= transientRetryDelaysMs.length; attempt += 1) {
    try {
      const response = await fetch(input, init);
      if (!(await isRetryableBackendResponse(response)) || attempt === transientRetryDelaysMs.length) {
        return response;
      }
    } catch (exc) {
      lastError = exc;
      if (attempt === transientRetryDelaysMs.length) {
        throw exc;
      }
    }
    await sleep(transientRetryDelaysMs[attempt]);
  }
  throw lastError instanceof Error ? lastError : new Error(String(lastError || "Backend request failed"));
}

async function isRetryableBackendResponse(response: Response) {
  if (![502, 503, 504].includes(response.status)) {
    return false;
  }
  if (response.headers.get("x-application-finder-retryable") === "true") {
    return true;
  }
  try {
    const payload = await response.clone().json() as { retryable?: unknown };
    return payload.retryable === true;
  } catch {
    return false;
  }
}

async function errorMessage(response: Response) {
  const text = await response.text();
  try {
    const payload = JSON.parse(text) as { detail?: unknown };
    return typeof payload.detail === "string" ? payload.detail : text;
  } catch {
    return text;
  }
}

function sleep(delayMs: number) {
  return new Promise((resolve) => setTimeout(resolve, delayMs));
}
