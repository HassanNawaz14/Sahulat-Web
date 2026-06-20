"use client"

import { Plus } from "lucide-react"

interface Props {
  onAddUtility: () => void
}

export default function EmptyStateCTA({ onAddUtility }: Props) {
  return (
    <div className="rounded-xl border-2 border-dashed border-gray-300 p-8 text-center">
      <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-full bg-blue-50">
        <Plus className="h-6 w-6 text-blue-600" />
      </div>
      <h2 className="mt-4 text-lg font-semibold text-gray-700">Welcome to Sahulat</h2>
      <p className="mt-2 text-sm text-gray-500">
        Add your first utility to start tracking bills, consumption, and outages.
      </p>
      <button
        onClick={onAddUtility}
        className="mt-6 inline-block rounded-lg bg-blue-600 px-6 py-3 text-sm font-medium text-white"
      >
        Add Utility
      </button>
    </div>
  )
}
