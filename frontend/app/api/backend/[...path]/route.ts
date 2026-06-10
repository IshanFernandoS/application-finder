import { NextRequest, NextResponse } from "next/server";

const backendUrl = process.env.BACKEND_URL || process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:8000";
const transientRetryDelaysMs = [800, 2000, 4000];
const allowedAdminPrefixes = new Set(["hpc", "analytics"]);
const allowedPublicPrefixes = new Set([
  "application-space",
  "evals",
  "gaps",
  "health",
  "ingest",
  "materials",
  "mattergen",
  "pathways",
  "rag",
  "reports",
  "scopes"
]);

type RouteContext = {
  params: Promise<{ path?: string[] }>;
};

export const dynamic = "force-dynamic";

export async function GET(request: NextRequest, context: RouteContext) {
  return proxy(request, context);
}

export async function POST(request: NextRequest, context: RouteContext) {
  return proxy(request, context);
}

async function proxy(request: NextRequest, context: RouteContext) {
  const params = await context.params;
  const path = params.path || [];
  const prefix = path[0];
  const isAdminPath = Boolean(prefix && allowedAdminPrefixes.has(prefix));
  const isPublicPath = Boolean(prefix && allowedPublicPrefixes.has(prefix));
  if (!isAdminPath && !isPublicPath) {
    return NextResponse.json({ detail: "Backend proxy path is not allowed." }, { status: 404 });
  }

  const target = new URL(`/api/${path.map(encodeURIComponent).join("/")}${request.nextUrl.search}`, backendUrl);
  const headers = new Headers();
  if (isAdminPath) {
    const adminKey = process.env.ADMIN_API_KEY || process.env.FRONTEND_ADMIN_API_KEY;
    if (!adminKey) {
      return NextResponse.json({ detail: "Frontend admin key is not configured on the server." }, { status: 503 });
    }
    headers.set("x-admin-api-key", adminKey);
  }
  const contentType = request.headers.get("content-type");
  if (contentType) {
    headers.set("content-type", contentType);
  }

  const body = request.method === "GET" || request.method === "HEAD" ? undefined : await request.arrayBuffer();
  const response = await fetchBackendWithRetry(target, {
    method: request.method,
    headers,
    body,
    cache: "no-store"
  });
  if (response instanceof NextResponse) {
    return response;
  }

  const responseHeaders = new Headers();
  const responseContentType = response.headers.get("content-type");
  if (responseContentType) {
    responseHeaders.set("content-type", responseContentType);
  }
  return new Response(response.body, {
    status: response.status,
    statusText: response.statusText,
    headers: responseHeaders
  });
}

async function fetchBackendWithRetry(target: URL, init: RequestInit): Promise<Response | NextResponse> {
  let lastError: unknown;
  for (let attempt = 0; attempt <= transientRetryDelaysMs.length; attempt += 1) {
    try {
      const response = await fetch(target, init);
      if (!isTransientRenderUnavailable(response)) {
        return response;
      }
      if (attempt === transientRetryDelaysMs.length) {
        return NextResponse.json(
          {
            detail: "The backend is restarting on Render. Please try the action again in a moment.",
            retryable: true
          },
          {
            status: 503,
            headers: {
              "x-application-finder-retryable": "true"
            }
          }
        );
      }
    } catch (exc) {
      lastError = exc;
      if (attempt === transientRetryDelaysMs.length) {
        const message = exc instanceof Error ? exc.message : String(exc);
        return NextResponse.json({ detail: `Backend request failed: ${message}`, retryable: true }, { status: 502 });
      }
    }
    await sleep(transientRetryDelaysMs[attempt]);
  }
  const message = lastError instanceof Error ? lastError.message : String(lastError || "unknown backend error");
  return NextResponse.json({ detail: `Backend request failed: ${message}`, retryable: true }, { status: 502 });
}

function isTransientRenderUnavailable(response: Response) {
  if (![502, 503, 504].includes(response.status)) {
    return false;
  }
  const routingState = response.headers.get("x-render-routing")?.toLowerCase();
  return routingState === "no-deploy";
}

function sleep(delayMs: number) {
  return new Promise((resolve) => setTimeout(resolve, delayMs));
}
