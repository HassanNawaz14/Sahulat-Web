"use client"

import { useUpdateBillStatus } from "@/lib/hooks/useBills"

interface Props {
  billId: string
  currentStatus: string
}

export default function MarkPaidButton({ billId, currentStatus }: Props) {
  const updateStatus = useUpdateBillStatus()

  if (currentStatus === "paid") return null

  const handleClick = () => {
    updateStatus.mutate({ billId, status: "paid" })
  }

  return (
    <button
      onClick={handleClick}
      disabled={updateStatus.isPending}
      className="flex-1 rounded-lg bg-green-600 py-2 text-center text-xs font-medium text-white disabled:opacity-50"
    >
      {updateStatus.isPending ? "Updating..." : "Mark as Paid"}
    </button>
  )
}
