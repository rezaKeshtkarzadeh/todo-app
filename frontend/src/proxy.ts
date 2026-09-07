import { NextResponse, type NextRequest } from "next/server";

const locales = ["en", "fa"] as const;

const defaultLocale = "en";

const cookieName = "NEXT_LOCALE";

export function proxy(request: NextRequest) {
  const response = NextResponse.next();

  const localeCookie = request.cookies.get(cookieName)?.value;

  const locale =
    localeCookie &&
    locales.includes(localeCookie as (typeof locales)[number])
      ? localeCookie
      : defaultLocale;

  response.headers.set("x-next-intl-locale", locale);

  return response;
}

export const config = {
  matcher: ["/((?!api|_next|_vercel|.*\\..*).*)", "/"],
}