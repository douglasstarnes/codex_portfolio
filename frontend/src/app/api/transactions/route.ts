import { cookies } from "next/headers";
import { NextRequest } from "next/server";

import { AUTH_COOKIE_NAME, proxyFastApi, readJson } from "@/lib/server/api";

export async function GET() {
  const cookieStore = await cookies();
  const token = cookieStore.get(AUTH_COOKIE_NAME)?.value;

  return proxyFastApi("/transactions", { token });
}

export async function POST(request: NextRequest) {
  const cookieStore = await cookies();
  const token = cookieStore.get(AUTH_COOKIE_NAME)?.value;
  const body = await readJson(request);

  return proxyFastApi("/transactions", {
    method: "POST",
    body,
    token,
  });
}
