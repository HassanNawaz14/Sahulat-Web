"use client"

import { useEffect } from "react"

/**
 * Initializes push notifications on mount.
 * Registers the service worker and restores any existing push subscription
 * (does NOT trigger the native permission prompt — that's done explicitly
 * via PermissionPrompt during onboarding or the settings page).
 */
export default function PushInit() {
  useEffect(() => {
    if (process.env.NODE_ENV !== "production") return
    if (!("serviceWorker" in navigator)) return

    navigator.serviceWorker
      .register("/sw.js")
      .then((registration) => {
        // Restore existing push subscription silently
        registration.pushManager.getSubscription().then((sub) => {
          if (sub && "Notification" in window && Notification.permission === "granted") {
            // Subscription exists and is active — backend already has it
          }
        })
      })
      .catch((error) => {
        console.warn("SW registration failed:", error)
      })
  }, [])

  return null
}
