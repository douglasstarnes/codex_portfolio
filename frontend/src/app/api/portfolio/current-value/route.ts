import { cookies } from "next/headers";

import { AUTH_COOKIE_NAME, proxyFastApi } from "@/lib/server/api";

export async function GET() {
  const cookieStore = await cookies();
  const token = cookieStore.get(AUTH_COOKIE_NAME)?.value;

  return proxyFastApi("/portfolio/current_value", { token });
}
