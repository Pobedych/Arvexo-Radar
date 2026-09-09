import { NextRequest, NextResponse } from "next/server";

import { RADAR_SESSION_COOKIE } from "@/lib/arvexo-auth";

export function GET(request: NextRequest) {
  const response = NextResponse.redirect(new URL("/", request.url));
  response.cookies.delete(RADAR_SESSION_COOKIE);
  return response;
}
