import { cookies } from "next/headers";

import { AUTH_COOKIE_NAME, proxyFastApi } from "@/lib/server/api";

type RouteContext = {
  params: Promise<{
    id: string;
  }>;
};

export async function GET(_request: Request, context: RouteContext) {
  const { id } = await context.params;
  const cookieStore = await cookies();
  const token = cookieStore.get(AUTH_COOKIE_NAME)?.value;

  return proxyFastApi(`/transactions/${id}`, { token });
}
