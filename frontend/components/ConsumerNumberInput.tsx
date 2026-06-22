"use client"

import { useMemo } from "react"
import { getConsumerNumberPattern } from "@/lib/constants/consumerPatterns"

interface Props {
  providerCode: string
  value: string
  onChange: (value: string) => void
  error?: string
}

function maxLengthFromPattern(pattern: RegExp): number {
  const m = pattern.source.match(/\{(\d+),(\d+)\}|\{(\d+)\}|\+$/)
  if (m) return parseInt(m[2] || m[3] || "14", 10)
  return 14
}

function isDigitsOnly(pattern: RegExp): boolean {
  return pattern.source.startsWith("^\\d") || pattern.source.startsWith("^[0-9")
}

export default function ConsumerNumberInput({ providerCode, value, onChange, error }: Props) {
  const pattern = useMemo(() => getConsumerNumberPattern(providerCode), [providerCode])
  const maxLen = useMemo(() => maxLengthFromPattern(pattern.pattern), [pattern.pattern])

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const raw = e.target.value
    if (isDigitsOnly(pattern.pattern)) {
      onChange(raw.replace(/[^0-9]/g, ""))
    } else {
      onChange(raw.replace(/[^A-Za-z0-9]/g, "").toUpperCase())
    }
  }

  return (
    <div>
      <label className="text-xs font-medium text-gray-600">Consumer Number</label>
      <input
        value={value}
        onChange={handleChange}
        placeholder={pattern.placeholder}
        className="mt-1.5 w-full rounded-lg border border-gray-200 p-2.5 text-sm"
        maxLength={maxLen}
      />
      <div className="mt-1 flex items-center justify-between">
        {error ? (
          <p className="text-xs text-red-500">{error}</p>
        ) : (
          <p className="text-xs text-gray-400">{pattern.hint}</p>
        )}
        {value && (
          <span className={`text-xs ${pattern.pattern.test(value) ? "text-green-500" : "text-red-400"}`}>
            {pattern.pattern.test(value) ? "Valid format" : "Invalid format"}
          </span>
        )}
      </div>
    </div>
  )
}
