import { NextResponse, type NextRequest } from "next/server";

export async function middleware(request: NextRequest) {
  const sessionRes = await fetch(
    `${request.nextUrl.origin}/api/auth/get-session`,
    {
      headers: {
        cookie: request.headers.get("cookie") || "",
      },
    },
  );

  let isAuth = false;
  if (sessionRes.ok) {
    const session = await sessionRes.json();
    isAuth = !!session?.user;
  }

  const { pathname } = request.nextUrl;
  const isAuthPage = pathname.startsWith("/login");
  const isProfilePage = pathname.startsWith("/profile");
  const isTicketsPage = pathname.startsWith("/tickets");
  const isAdminPage = pathname.startsWith("/admin");

  if (isAuthPage && isAuth) {
    return NextResponse.redirect(new URL("/", request.url));
  }

  if ((isProfilePage || isTicketsPage || isAdminPage) && !isAuth) {
    return NextResponse.redirect(new URL("/login", request.url));
  }

  return NextResponse.next();
}

export const config = {
  matcher: [
    "/login",
    "/profile",
    "/tickets",
    "/tickets/:path*",
    "/admin",
    "/admin/:path*",
  ],
};
