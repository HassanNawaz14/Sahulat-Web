import { ArrowLeft, ArrowRight } from "lucide-react"

interface MonthSelectorProps {
  value: string
  onChange: (month: string) => void
}

export default function MonthSelector({ value, onChange }: MonthSelectorProps) {
  const [year, month] = value.split("-").map(Number)
  const months = [
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December",
  ]

  const prevMonth = () => {
    if (month === 1) onChange(`${year - 1}-12`)
    else onChange(`${year}-${String(month - 1).padStart(2, "0")}`)
  }

  const nextMonth = () => {
    if (month === 12) onChange(`${year + 1}-01`)
    else onChange(`${year}-${String(month + 1).padStart(2, "0")}`)
  }

  return (
    <div className="flex items-center justify-between rounded-lg bg-white px-4 py-2">
      <button onClick={prevMonth} className="rounded-full p-1 text-gray-500 hover:bg-gray-100">
        <ArrowLeft className="h-5 w-5" />
      </button>
      <span className="text-sm font-medium">
        {months[month - 1]} {year}
      </span>
      <button onClick={nextMonth} className="rounded-full p-1 text-gray-500 hover:bg-gray-100">
        <ArrowRight className="h-5 w-5" />
      </button>
    </div>
  )
}
