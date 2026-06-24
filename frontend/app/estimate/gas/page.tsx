import type { Metadata } from "next"
import EstimatorForm from "@/components/estimator/EstimatorForm"

export const metadata: Metadata = {
  title: "Gas Bill Calculator Pakistan — SNGPL & SSGC | Sahulat",
  description:
    "Free gas bill calculator for SNGPL and SSGC. Enter MMBtu consumption and get OGRA slab-based estimate with GST and meter rent.",
}

export default function GasEstimatePage() {
  return (
    <main className="mx-auto max-w-lg px-4 py-8">
      <h1 className="mb-2 text-xl font-bold text-gray-900">Gas Bill Calculator</h1>
      <p className="mb-6 text-sm text-gray-500">
        Estimate your SNGPL or SSGC bill by entering your MMBtu consumption. Based on OGRA notified
        slab rates.
      </p>
      <EstimatorForm />
    </main>
  )
}
