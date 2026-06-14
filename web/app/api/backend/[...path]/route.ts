import { NextRequest, NextResponse } from "next/server";

import { backendBaseUrl } from "../../../../lib/api";

async function proxy(request: NextRequest, path: string[]) {
  const url = new URL(`${backendBaseUrl()}/${path.join("/")}`);
  url.search = request.nextUrl.search;

  const response = await fetch(url, {
    method: request.method,
    headers: {
      "content-type": request.headers.get("content-type") ?? "application/json",
    },
    body: request.method === "GET" || request.method === "HEAD" ? undefined : await request.text(),
  });

  return new NextResponse(response.body, {
    status: response.status,
    headers: {
      "content-type": response.headers.get("content-type") ?? "application/json",
    },
  });
}

export async function GET(request: NextRequest, context: { params: Promise<{ path: string[] }> }) {
  const { path } = await context.params;
  return proxy(request, path);
}

export async function POST(request: NextRequest, context: { params: Promise<{ path: string[] }> }) {
  const { path } = await context.params;
  return proxy(request, path);
}
