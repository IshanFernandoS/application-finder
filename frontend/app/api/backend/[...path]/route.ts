import { NextRequest, NextResponse } from "next/server";

const backendUrl = process.env.BACKEND_URL || process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:8000";
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
  let response: Response;
  try {
    response = await fetch(target, {
      method: request.method,
      headers,
      body,
      cache: "no-store"
    });
  } catch (exc) {
    const message = exc instanceof Error ? exc.message : String(exc);
    return NextResponse.json({ detail: `Backend request failed: ${message}` }, { status: 502 });
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
