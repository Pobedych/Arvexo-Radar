import { NextRequest, NextResponse } from "next/server";

import { accountApiUrl, radarCallbackUrl, radarClientId, RADAR_RETURN_COOKIE, RADAR_STATE_COOKIE, safeReturnTo } from "@/lib/arvexo-auth";

export const dynamic = "force-dynamic";

export function GET(request: NextRequest) {
  const state = crypto.randomUUID();
  const callbackUrl = radarCallbackUrl(request.nextUrl.origin);
  const authorizeUrl = new URL(`${accountApiUrl()}/sso/start`);
  authorizeUrl.searchParams.set("client_id", radarClientId());
  authorizeUrl.searchParams.set("redirect_uri", callbackUrl);
  authorizeUrl.searchParams.set("state", state);

  const response = NextResponse.redirect(authorizeUrl);
  const cookieOptions = { httpOnly: true, sameSite: "lax" as const, secure: process.env.NODE_ENV === "production", path: "/", maxAge: 10 * 60 };
  response.cookies.set(RADAR_STATE_COOKIE, state, cookieOptions);
  response.cookies.set(RADAR_RETURN_COOKIE, safeReturnTo(request.nextUrl.searchParams.get("returnTo")), cookieOptions);
  return response;
}
