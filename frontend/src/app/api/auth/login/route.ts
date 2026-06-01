import { cookies } from "next/headers";
import { NextRequest, NextResponse } from "next/server";

import {
  AUTH_COOKIE_NAME,
  apiUrl,
  errorMessage,
  readJson,
} from "@/lib/server/api";
import type { TokenResponse } from "@/lib/types";

export async function POST(request: NextRequest) {
  const body = await readJson(request);

  let response: Response;
  try {
    response = await fetch(apiUrl("/auth/login"), {
      method: "POST",
      headers: {
        Accept: "application/json",
        "Content-Type": "application/json",
      },
      body: JSON.stringify(body),
      cache: "no-store",
    });
  } catch {
    return NextResponse.json(
      { detail: "Could not reach the backend API. Is FastAPI running?" },
      { status: 503 },
    );
  }

  const data = await response.json();

  if (!response.ok) {
    return NextResponse.json(
      { detail: errorMessage(data, "Incorrect username or password.") },
      { status: response.status },
    );
  }

  const token = data as TokenResponse;
  const cookieStore = await cookies();
  cookieStore.set(AUTH_COOKIE_NAME, token.access_token, {
    httpOnly: true,
    sameSite: "lax",
    secure: process.env.NODE_ENV === "production",
    path: "/",
  });

  return NextResponse.json({ token_type: token.token_type });
}
