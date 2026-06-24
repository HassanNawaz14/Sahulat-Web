import type { Metadata } from "next"
import EstimatorForm from "@/components/estimator/EstimatorForm"

export const metadata: Metadata = {
  title: "Utility Bill Calculator Pakistan — Electricity, Gas & Water | Sahulat",
  description:
    "Calculate your LESCO, MEPCO, GEPCO, K-Electric, SNGPL, SSGC, WASA bill for free. Instant slab-by-slab breakdown with tax calculation.",
}

export default function EstimatePage() {
  return (
    <main className="mx-auto max-w-lg px-4 py-8">
      <h1 className="mb-2 text-xl font-bold text-gray-900">Utility Bill Estimator</h1>
      <p className="mb-6 text-sm text-gray-500">
        Estimate your electricity, gas, or water bill before the official bill arrives.
      </p>
      <EstimatorForm />
    </main>
  )
}
