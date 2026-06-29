"use client"

import { useState, useRef, useEffect, useMemo } from "react"
import { Search, X, Loader2, AlertCircle, ChevronDown, Zap, RotateCw } from "lucide-react"
import { useFeederSearch, useSetFeeder } from "@/lib/hooks/useOutages"
import { PROVIDER_LABELS } from "@/lib/constants/utility"
import api from "@/lib/api"

const DISCO_PROVIDERS = [
  "lesco", "kelectric", "iesco", "gepco", "fesco",
  "mepco", "pesco", "qesco", "hesco", "sepco",
] as const

interface FeederSelectorProps {
  providerCode: string
  consumerAccountId?: string
  currentFeeder?: string
  onSaved?: () => void
  onFeederChange?: (feederName: string) => void
}

export default function FeederSelector({ providerCode, consumerAccountId, currentFeeder, onSaved, onFeederChange }: FeederSelectorProps) {
  const [open, setOpen] = useState(!!onFeederChange)
  const [query, setQuery] = useState("")
  const [selectedProvider, setSelectedProvider] = useState(providerCode)
  const [refreshing, setRefreshing] = useState(false)
  const [refreshError, setRefreshError] = useState("")
  const [saveError, setSaveError] = useState("")
  const dropdownRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLInputElement>(null)

  const { data: feeders, isLoading: feedersLoading, isError: feedersError, refetch: refetchFeeders } = useFeederSearch(selectedProvider)
  const { mutate: setFeeder, isPending: saving } = useSetFeeder()

  // Client-side filter: if query is empty, show ALL feeders
  const filteredFeeders = useMemo(() => {
    if (!feeders) return []
    if (!query) return feeders
    const q = query.toLowerCase()
    return feeders.filter(
      (f) => f.feeder_name.toLowerCase().includes(q) || f.feeder_code.toLowerCase().includes(q)
    )
  }, [feeders, query])

  useEffect(() => {
    if (open && inputRef.current) {
      inputRef.current.focus()
    }
  }, [open])

  // Reset selected provider when prop changes
  useEffect(() => {
    setSelectedProvider(providerCode)
  }, [providerCode])

  // Close dropdown on outside click
  useEffect(() => {
    if (!open) return
    const handleClick = (e: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target as Node)) {
        setOpen(false)
        setQuery("")
      }
    }
    document.addEventListener("mousedown", handleClick)
    return () => document.removeEventListener("mousedown", handleClick)
  }, [open])

  const handleRefresh = async () => {
    setRefreshing(true)
    setRefreshError("")
    try {
      const resp = await api.post<{ status: string; total_upserted?: number; warnings?: string[] }>("/outages/refresh-feeders", undefined, { timeout: 120000 })
      if (resp.data.status !== "ok") {
        setRefreshError("Scraper returned no data. The PDF may be unreachable.")
      } else if (resp.data.total_upserted === 0) {
        setRefreshError("No feeder schedules found in PDF.")
      } else {
        await refetchFeeders()
      }
    } catch (err: unknown) {
      const axiosErr = err as { response?: { data?: { detail?: string } }; message?: string }
      const msg = axiosErr?.response?.data?.detail || axiosErr?.message || "Refresh failed"
      setRefreshError(msg)
    } finally {
      setRefreshing(false)
    }
  }

  const handleSelect = (feederName: string) => {
    if (onFeederChange) {
      onFeederChange(feederName)
      setOpen(false)
      setQuery("")
      return
    }
    if (!consumerAccountId) return
    setSaveError("")
    setFeeder(
      { consumer_account_id: consumerAccountId, feeder_name: feederName },
      {
        onSuccess: () => {
          setOpen(false)
          setQuery("")
          setSaveError("")
          onSaved?.()
        },
        onError: (err: unknown) => {
          const axiosErr = err as { response?: { data?: { detail?: string } }; message?: string }
          setSaveError(axiosErr?.response?.data?.detail || axiosErr?.message || "Failed to save feeder")
        },
      }
    )
  }

  const isSelectOnly = !!onFeederChange

  if (!open && !isSelectOnly) {
    return (
      <button
        onClick={() => setOpen(true)}
        className="flex items-center gap-2 rounded-lg border border-gray-200 bg-white px-3 py-2 text-xs text-gray-600 transition-colors hover:border-blue-300 hover:text-blue-600"
      >
        <Search className="h-3.5 w-3.5" />
        {currentFeeder ? `Feeder: ${currentFeeder}` : "Set Feeder"}
        <ChevronDown className="h-3 w-3 text-gray-400" />
      </button>
    )
  }



  return (
    <div ref={dropdownRef} className="relative">
      <div className="rounded-xl border border-blue-300 bg-white">
        {/* Provider pills */}
        <div className="flex items-center gap-1 overflow-x-auto border-b border-gray-100 p-2">
          <Zap className="h-3.5 w-3.5 shrink-0 text-gray-400" />
          {DISCO_PROVIDERS.map((code) => (
            <button
              key={code}
              onClick={() => { setSelectedProvider(code); setQuery("") }}
              className={`shrink-0 rounded-md px-2 py-1 text-[11px] font-medium transition-colors ${
                selectedProvider === code
                  ? "bg-blue-600 text-white"
                  : "bg-gray-100 text-gray-600 hover:bg-gray-200"
              }`}
            >
              {PROVIDER_LABELS[code] ?? code.toUpperCase()}
            </button>
          ))}
        </div>

        {/* Search input */}
        <div className="flex items-center gap-2 p-3 pt-2">
          <Search className="h-4 w-4 text-gray-400" />
          <input
            ref={inputRef}
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Type to filter feeders..."
            className="flex-1 text-sm outline-none"
          />
          <button onClick={() => { setOpen(false); setQuery("") }}>
            <X className="h-4 w-4 text-gray-400" />
          </button>
        </div>
      </div>

      {/* Feeder results */}
      <div className="absolute left-0 right-0 top-full z-10 mt-1 max-h-56 overflow-y-auto rounded-lg border border-gray-200 bg-white shadow-lg">
        {feedersLoading && (
          <p className="flex items-center gap-2 p-3 text-xs text-gray-400">
            <Loader2 className="h-3 w-3 animate-spin" />
            Loading feeders...
          </p>
        )}
        {feedersError && !feedersLoading && (
          <p className="flex items-center gap-2 p-3 text-xs text-red-500">
            <AlertCircle className="h-3 w-3" />
            Failed to load feeders. Try again.
          </p>
        )}
        {!feedersLoading && !feedersError && filteredFeeders.length > 0
          ? filteredFeeders.map((f) => (
              <button
                key={f.feeder_code}
                onClick={() => handleSelect(f.feeder_name)}
                className="flex w-full items-center gap-2 px-3 py-2.5 text-left text-sm transition-colors hover:bg-blue-50"
              >
                <span className="text-gray-800">{f.feeder_name}</span>
                <span className="text-[10px] text-gray-400">{f.feeder_code}</span>
              </button>
            ))
          : !feedersLoading && !feedersError && (
              <p className="p-3 text-xs text-gray-400">
                {query ? `No feeders match "${query}"` : (
                <span>
                  No feeders available for this provider
                  <button
                    onClick={handleRefresh}
                    disabled={refreshing}
                    className="ml-2 inline-flex items-center gap-1 text-blue-600 hover:text-blue-800 disabled:opacity-50"
                  >
                    <RotateCw className={`h-3 w-3 ${refreshing ? "animate-spin" : ""}`} />
                    {refreshing ? "Refreshing..." : "Refresh"}
                  </button>
                  {refreshError && (
                    <span className="block mt-1 text-red-500">{refreshError}</span>
                  )}
                </span>
              )}
              </p>
            )}
      </div>

      {saving && (
        <p className="mt-1 text-xs text-blue-600">Saving...</p>
      )}
      {saveError && !saving && (
        <p className="mt-1 text-xs text-red-500">{saveError}</p>
      )}
    </div>
  )
}
