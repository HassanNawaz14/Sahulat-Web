import axios from "axios"

import { createClient } from "@/lib/supabase/client"

const api = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_BASE_URL,
})

api.interceptors.request.use(async (config) => {
  const supabase = createClient()
  const { data } = await supabase.auth.getSession()
  const token = data.session?.access_token
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

api.interceptors.response.use(
  (res) => res,
  async (error) => {
    if (error.response?.status === 401) {
      const supabase = createClient()
      const { error: refreshError } = await supabase.auth.refreshSession()
      if (refreshError) {
        await supabase.auth.signOut()
        if (typeof window !== "undefined") {
          window.location.href = "/auth/login"
        }
        return Promise.reject(error)
      }
      const { data } = await supabase.auth.getSession()
      if (data.session?.access_token) {
        error.config.headers.Authorization = `Bearer ${data.session.access_token}`
        return api(error.config)
      }
    }
    return Promise.reject(error)
  },
)

export default api
