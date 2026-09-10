import { NextRequest, NextResponse } from "next/server";

import { radarPublicUrl, RADAR_SESSION_COOKIE } from "@/lib/arvexo-auth";

export function GET(request: NextRequest) {
  const response = NextResponse.redirect(radarPublicUrl("/", request.nextUrl.origin));
  response.cookies.delete(RADAR_SESSION_COOKIE);
  return response;
}
