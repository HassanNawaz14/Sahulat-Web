import type { Metadata } from "next"
import "./globals.css"
import { AuthProvider } from "@/components/providers"

export const metadata: Metadata = {
  title: "Sahulat — Apni utilities, ek jagah",
  description:
    "Track electricity, gas, water, internet & solar bills — all in one place. Stay ahead of load shedding, slab boundaries, and due dates.",
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body className="min-h-screen bg-gray-50 antialiased">
        <AuthProvider>{children}</AuthProvider>
      </body>
    </html>
  )
}
