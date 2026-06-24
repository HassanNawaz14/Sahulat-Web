import type { Metadata } from "next"
import EstimatorForm from "@/components/estimator/EstimatorForm"

export const metadata: Metadata = {
  title: "Electricity Bill Calculator Pakistan — LESCO, K-Electric & More | Sahulat",
  description:
    "Free electricity bill calculator for LESCO, K-Electric, IESCO, MEPCO, GEPCO, FESCO, PESCO, QESCO, HESCO, SEPCO. Get slab-by-slab breakdown, taxes, and total instantly.",
}

export default function ElectricityEstimatePage() {
  const schema = {
    "@context": "https://schema.org",
    "@type": "WebApplication",
    name: "Electricity Bill Calculator Pakistan",
    url: "https://sahulat.pk/estimate/electricity",
    description: "Calculate your electricity bill for any Pakistani DISCO with real-time slab rates.",
    applicationCategory: "UtilityApplication",
    operatingSystem: "All",
  }

  return (
    <main className="mx-auto max-w-lg px-4 py-8">
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(schema) }}
      />
      <h1 className="mb-2 text-xl font-bold text-gray-900">Electricity Bill Calculator</h1>
      <p className="mb-6 text-sm text-gray-500">
        Enter your units (kWh) and select your provider to get an instant estimate with full slab
        breakdown, taxes, and slab crossing warning.
      </p>
      <EstimatorForm />
    </main>
  )
}
