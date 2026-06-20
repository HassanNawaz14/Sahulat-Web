import { createServerClient } from "@supabase/ssr"
import { NextResponse, type NextRequest } from "next/server"

export async function middleware(request: NextRequest) {
  let supabaseResponse = NextResponse.next({ request })

  const supabase = createServerClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!,
    {
      cookies: {
        get(name: string) {
          return request.cookies.get(name)?.value
        },
        set(name: string, value: string, options: Record<string, unknown>) {
          request.cookies.set(name, value)
          supabaseResponse = NextResponse.next({ request })
          supabaseResponse.cookies.set(name, value, options)
        },
        remove(name: string, options: Record<string, unknown>) {
          request.cookies.set(name, "")
          supabaseResponse = NextResponse.next({ request })
          supabaseResponse.cookies.set(name, "", { ...options, maxAge: 0 })
        },
      },
    },
  )

  const { data: { user } } = await supabase.auth.getUser()
  const pathname = request.nextUrl.pathname

  const unprotectedPaths = ["/auth/login", "/auth/verify", "/auth/callback"]

  if (!user && !unprotectedPaths.some((p) => pathname.startsWith(p)) && pathname !== "/") {
    return NextResponse.redirect(new URL("/auth/login", request.url))
  }

  if (user && unprotectedPaths.some((p) => pathname.startsWith(p))) {
    return NextResponse.redirect(new URL("/dashboard", request.url))
  }

  return supabaseResponse
}

export const config = {
  matcher: ["/((?!_next/static|_next/image|favicon.ico|.*\\.(?:svg|png|jpg|jpeg|gif|webp)$).*)"],
}
