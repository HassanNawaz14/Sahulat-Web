import type { ReactNode } from "react"

export default function SettingsLayout({ children }: { children: ReactNode }) {
  return (
    <div className="mx-auto max-w-lg px-4 py-8">
      <h1 className="text-2xl font-bold mb-6">Settings</h1>
      {children}
    </div>
  )
}
