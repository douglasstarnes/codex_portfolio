import { NextRequest } from "next/server";

import { proxyFastApi, readJson } from "@/lib/server/api";

export async function POST(request: NextRequest) {
  const body = await readJson(request);

  return proxyFastApi("/auth/register", {
    method: "POST",
    body,
  });
}
