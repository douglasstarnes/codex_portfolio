import { type NextRequest, NextResponse } from "next/server";

import type { ApiErrorBody } from "@/lib/types";

export const AUTH_COOKIE_NAME = "codex_portfolio_token";

const API_BASE_URL =
  process.env.API_BASE_URL ??
  process.env.NEXT_PUBLIC_API_BASE_URL ??
  "http://127.0.0.1:8000";

type ProxyOptions = {
  method?: string;
  body?: unknown;
  token?: string;
};

export function apiUrl(path: string) {
  return new URL(path, API_BASE_URL).toString();
}

export function errorMessage(body: unknown, fallback: string) {
  if (typeof body === "object" && body !== null) {
    const errorBody = body as ApiErrorBody;
    return errorBody.detail ?? errorBody.message ?? fallback;
  }

  return fallback;
}

export async function readJson(request: NextRequest) {
  try {
    return await request.json();
  } catch {
    return {};
  }
}

export async function proxyFastApi(path: string, options: ProxyOptions = {}) {
  const headers = new Headers({
    Accept: "application/json",
  });

  let body: BodyInit | undefined;
  if (options.body !== undefined) {
    headers.set("Content-Type", "application/json");
    body = JSON.stringify(options.body);
  }

  if (options.token) {
    headers.set("Authorization", `Bearer ${options.token}`);
  }

  let response: Response;
  try {
    response = await fetch(apiUrl(path), {
      method: options.method ?? "GET",
      headers,
      body,
      cache: "no-store",
    });
  } catch {
    return NextResponse.json(
      { detail: "Could not reach the backend API. Is FastAPI running?" },
      { status: 503 },
    );
  }

  const responseText = await response.text();
  const data = responseText ? JSON.parse(responseText) : null;

  if (!response.ok) {
    return NextResponse.json(
      { detail: errorMessage(data, "The backend API returned an error.") },
      { status: response.status },
    );
  }

  return NextResponse.json(data, { status: response.status });
}
