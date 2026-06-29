import api from "@/lib/api"

export async function subscribeToPush(): Promise<PushSubscription | null> {
  if (!("serviceWorker" in navigator) || !("PushManager" in window)) {
    console.warn("Push notifications not supported")
    return null
  }

  try {
    const registration = await navigator.serviceWorker.ready

    // Check for existing subscription
    const existing = await registration.pushManager.getSubscription()
    if (existing) {
      // Already subscribed — make sure backend knows
      await sendSubscriptionToBackend(existing)
      return existing
    }

    const vapidKey = process.env.NEXT_PUBLIC_VAPID_PUBLIC_KEY
    if (!vapidKey) {
      console.warn("VAPID public key not configured")
      return null
    }

    const subscription = await registration.pushManager.subscribe({
      userVisibleOnly: true,
      applicationServerKey: urlBase64ToUint8Array(vapidKey) as unknown as BufferSource,
    })

    await sendSubscriptionToBackend(subscription)
    return subscription
  } catch (error) {
    console.error("Push subscription failed:", error)
    return null
  }
}

export async function unsubscribeFromPush(): Promise<boolean> {
  if (!("serviceWorker" in navigator)) return false

  try {
    const registration = await navigator.serviceWorker.ready
    const subscription = await registration.pushManager.getSubscription()
    if (!subscription) return false

    const json = subscription.toJSON()
    await api.post("/notifications/unsubscribe", {
      endpoint: json.endpoint,
      p256dh: (json.keys as Record<string, string>)?.p256dh ?? "",
      auth: (json.keys as Record<string, string>)?.auth ?? "",
      user_agent: navigator.userAgent,
    })

    await subscription.unsubscribe()
    return true
  } catch (error) {
    console.error("Push unsubscription failed:", error)
    return false
  }
}

async function sendSubscriptionToBackend(subscription: PushSubscription) {
  const json = subscription.toJSON()
  await api.post("/notifications/subscribe", {
    endpoint: json.endpoint,
    p256dh: (json.keys as Record<string, string>)?.p256dh ?? "",
    auth: (json.keys as Record<string, string>)?.auth ?? "",
    user_agent: navigator.userAgent,
  })
}

function urlBase64ToUint8Array(base64String: string): Uint8Array {
  const padding = "=".repeat((4 - (base64String.length % 4)) % 4)
  const base64 = (base64String + padding).replace(/-/g, "+").replace(/_/g, "/")
  const rawData = atob(base64)
  const outputArray = new Uint8Array(rawData.length)
  for (let i = 0; i < rawData.length; ++i) {
    outputArray[i] = rawData.charCodeAt(i)
  }
  return outputArray
}
