"use client"

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"

import api from "@/lib/api"
import { subscribeToPush, unsubscribeFromPush } from "@/lib/notifications/push"

export type NotificationPreference = {
  id?: string
  user_id?: string
  category: string
  enabled: boolean
  channels: { push: boolean; sms: boolean }
}

export type NotificationPreferencesResponse = {
  preferences: NotificationPreference[]
}

export function useNotificationPreferences() {
  return useQuery({
    queryKey: ["notification-preferences"],
    queryFn: async () => {
      const res = await api.get<NotificationPreferencesResponse>("/notifications/preferences")
      return res.data.preferences
    },
    staleTime: 10 * 60 * 1000,
  })
}

export function useUpdateNotificationPreferences() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async (preferences: NotificationPreference[]) => {
      const res = await api.put("/notifications/preferences", { preferences })
      return res.data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["notification-preferences"] })
    },
  })
}

export function useSubscribePush() {
  return useMutation({
    mutationFn: async () => {
      const subscription = await subscribeToPush()
      return subscription
    },
  })
}

export function useUnsubscribePush() {
  return useMutation({
    mutationFn: async () => {
      await unsubscribeFromPush()
    },
  })
}

export function useTestNotification() {
  return useMutation({
    mutationFn: async () => {
      const res = await api.post("/notifications/test")
      return res.data
    },
  })
}
