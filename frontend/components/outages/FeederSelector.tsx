"use client"

import { useState, useRef, useEffect } from "react"
import { Search, X } from "lucide-react"
import { useFeederSearch, useSetFeeder } from "@/lib/hooks/useOutages"

interface FeederSelectorProps {
  providerCode: string
  consumerAccountId: string
  currentFeeder?: string
  onSaved?: () => void
}

export default function FeederSelector({ providerCode, consumerAccountId, currentFeeder, onSaved }: FeederSelectorProps) {
  const [open, setOpen] = useState(false)
  const [query, setQuery] = useState("")
  const [showDropdown, setShowDropdown] = useState(false)
  const inputRef = useRef<HTMLInputElement>(null)

  const { data: feeders, isLoading: feedersLoading } = useFeederSearch(providerCode, query)
  const { mutate: setFeeder, isPending: saving } = useSetFeeder()

  useEffect(() => {
    if (open && inputRef.current) {
      inputRef.current.focus()
    }
  }, [open])

  const handleSelect = (feederName: string) => {
    setFeeder(
      { consumer_account_id: consumerAccountId, feeder_name: feederName },
      {
        onSuccess: () => {
          setOpen(false)
          setQuery("")
          onSaved?.()
        },
      }
    )
  }

  if (!open) {
    return (
      <button
        onClick={() => setOpen(true)}
        className="flex items-center gap-2 rounded-lg border border-gray-200 bg-white px-3 py-2 text-xs text-gray-600 transition-colors hover:border-blue-300 hover:text-blue-600"
      >
        <Search className="h-3.5 w-3.5" />
        {currentFeeder ? `Feeder: ${currentFeeder}` : "Set Feeder"}
      </button>
    )
  }

  return (
    <div className="relative rounded-xl border border-gray-200 bg-white p-3">
      <div className="flex items-center gap-2">
        <Search className="h-4 w-4 text-gray-400" />
        <input
          ref={inputRef}
          type="text"
          value={query}
          onChange={(e) => {
            setQuery(e.target.value)
            setShowDropdown(true)
          }}
          onFocus={() => setShowDropdown(true)}
          placeholder="Search feeder name..."
          className="flex-1 text-sm outline-none"
        />
        <button onClick={() => { setOpen(false); setQuery(""); setShowDropdown(false) }}>
          <X className="h-4 w-4 text-gray-400" />
        </button>
      </div>

      {showDropdown && (query.length >= 1 || feedersLoading) && (
        <div className="absolute left-0 right-0 top-full z-10 mt-1 max-h-48 overflow-y-auto rounded-lg border border-gray-200 bg-white shadow-lg">
          {feedersLoading && query.length >= 1 && (
            <p className="p-3 text-xs text-gray-400">Searching...</p>
          )}
          {!feedersLoading && feeders && feeders.length > 0
            ? feeders.map((f) => (
                <button
                  key={f.feeder_code}
                  onClick={() => handleSelect(f.feeder_name)}
                  className="flex w-full items-center gap-2 px-3 py-2.5 text-left text-sm transition-colors hover:bg-blue-50"
                >
                  <span className="text-gray-800">{f.feeder_name}</span>
                  <span className="text-[10px] text-gray-400">{f.feeder_code}</span>
                </button>
              ))
            : !feedersLoading && query.length >= 1 && (
                <p className="p-3 text-xs text-gray-400">No feeders found for &quot;{query}&quot;</p>
              )}
        </div>
      )}

      {saving && (
        <p className="mt-1 text-xs text-blue-600">Saving...</p>
      )}
    </div>
  )
}
