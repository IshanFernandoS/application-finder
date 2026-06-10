import { NextRequest, NextResponse } from "next/server";

const backendUrl = process.env.BACKEND_URL || process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:8000";
const allowedAdminPrefixes = new Set(["hpc", "analytics"]);

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
  if (!prefix || !allowedAdminPrefixes.has(prefix)) {
    return NextResponse.json({ detail: "Admin proxy path is not allowed." }, { status: 404 });
  }

  const adminKey = process.env.ADMIN_API_KEY || process.env.FRONTEND_ADMIN_API_KEY;
  if (!adminKey) {
    return NextResponse.json({ detail: "Frontend admin key is not configured on the server." }, { status: 503 });
  }

  const target = new URL(`/api/${path.map(encodeURIComponent).join("/")}${request.nextUrl.search}`, backendUrl);
  const headers = new Headers();
  headers.set("x-admin-api-key", adminKey);
  const contentType = request.headers.get("content-type");
  if (contentType) {
    headers.set("content-type", contentType);
  }

  const body = request.method === "GET" || request.method === "HEAD" ? undefined : await request.text();
  const response = await fetch(target, {
    method: request.method,
    headers,
    body,
    cache: "no-store"
  });

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
