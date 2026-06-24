import type { Metadata } from "next"
import EstimatorForm from "@/components/estimator/EstimatorForm"

export const metadata: Metadata = {
  title: "Water Bill Calculator Pakistan — WASA Lahore & KW&SB | Sahulat",
  description:
    "Free water bill calculator for WASA Lahore and KW&SB Karachi. Flat-rate estimate based on property size and type.",
}

export default function WaterEstimatePage() {
  return (
    <main className="mx-auto max-w-lg px-4 py-8">
      <h1 className="mb-2 text-xl font-bold text-gray-900">Water Bill Calculator</h1>
      <p className="mb-6 text-sm text-gray-500">
        Estimate your WASA or KW&SB water bill based on property type and size.
      </p>
      <EstimatorForm />
    </main>
  )
}
