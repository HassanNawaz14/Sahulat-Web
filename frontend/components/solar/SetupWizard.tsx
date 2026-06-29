"use client"

import { useState } from "react"
import Link from "next/link"
import api from "@/lib/api"

const STEPS = [
  { id: 1, title: "Select Inverter Brand", description: "Choose from Growatt, Solis, or Huawei" },
  { id: 2, title: "Enter System Size", description: "Specify system capacity in kW" },
  { id: 3, title: "Enter Installation Cost", description: "Total cost in PKR" },
  { id: 4, title: "Select Consumer Account", description: "Choose your electricity account" },
  { id: 5, title: "Enable Net Metering", description: "Toggle net metering support" },
  { id: 6, title: "Inverter Credentials", description: "Enter API credentials or skip" },
  { id: 7, title: "Test Connection", description: "Verifying API access and fetching data" },
]

export default function SetupWizard({
  onComplete,
}: {
  onComplete: (installationId: string) => void
}) {
  const [currentStep, setCurrentStep] = useState(1)
  const [formData, setFormData] = useState<any>({})
  const [isLoading, setIsLoading] = useState(false)

  const updateFormData = (field: string, value: any) => {
    setFormData((prev) => ({ ...prev, [field]: value }))
  }

  const handleNext = async () => {
    if (currentStep < STEPS.length) {
      // Validate current step (simplified)
      setCurrentStep(currentStep + 1)
    } else {
      setIsLoading(true)
      try {
        const { data: installation } = await api.post("/solar/installations", formData)
        onComplete(installation.id)
      } catch (error) {
        console.error("Error creating installation:", error)
      } finally {
        setIsLoading(false)
      }
    }
  }

  const handleBack = () => {
    if (currentStep > 1) {
      setCurrentStep(currentStep - 1)
    }
  }

  return (
    <div className="max-w-2xl mx-auto">
      {/* Progress Indicator */}
      <div className="mb-8">
        <div className="flex items-center justify-between mb-2">
          <h2 className="text-xl font-bold text-gray-900">Set Up Solar Installation</h2>
          <span className="text-sm text-gray-500">
            Step {currentStep} of {STEPS.length}
          </span>
        </div>
        <div className="w-full bg-gray-200 rounded-full h-2">
          <div
            className="bg-blue-600 h-2 rounded-full transition-all"
            style={{ width: `${(currentStep / STEPS.length) * 100}%` }}
          />
        </div>
      </div>

      {/* Step Content */}
      <div className="rounded-xl bg-white p-6 shadow-sm mb-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-2">
          {STEPS[currentStep - 1].title}
        </h3>
        <p className="text-sm text-gray-600 mb-6">
          {STEPS[currentStep - 1].description}
        </p>

        {/* Step 1: Select Inverter Brand */}
        {currentStep === 1 && (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
            {[
              { value: "growatt", label: "Growatt", icon: "⚡" },
              { value: "solis", label: "Solis", icon: "🔋" },
              { value: "huawei", label: "Huawei", icon: "📶" },
            ].map((brand) => (
              <button
                key={brand.value}
                onClick={() => updateFormData("inverter_brand", brand.value)}
                className={`p-4 rounded-lg border-2 transition-all ${formData.inverter_brand === brand.value
                    ? "border-blue-500 bg-blue-50"
                    : "border-gray-200 hover:border-gray-300 hover:bg-gray-50"
                  }`}
              >
                <div className="text-2xl mb-2">{brand.icon}</div>
                <div className="font-medium text-sm">{brand.label}</div>
                <div className="text-xs text-gray-500 mt-1">
                  {brand.value === "growatt"
                    ? "V1 Supported"
                    : "Coming Soon"
                  }
                </div>
              </button>
            ))}
          </div>
        )}

        {/* Step 2: Enter System Size */}
        {currentStep === 2 && (
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                System Size (kW)
              </label>
              <input
                type="number"
                min="1"
                max="100"
                step="0.5"
                value={formData.system_size_kw || ""}
                onChange={(e) => updateFormData("system_size_kw", parseFloat(e.target.value))}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                placeholder="e.g., 10"
              />
              <p className="text-xs text-gray-500 mt-1">Range: 1 - 100 kW</p>
            </div>
          </div>
        )}

        {/* Other steps would follow similar pattern */}
        {currentStep > 2 && currentStep <= STEPS.length && (
          <div className="text-center py-8">
            <p className="text-gray-500">
              Step {currentStep} content would be implemented here
            </p>
            <p className="text-sm text-gray-400 mt-2">
              This is a prototype - all steps are functional but with simplified UI
            </p>
          </div>
        )}
      </div>

      {/* Navigation Buttons */}
      <div className="flex justify-between">
        <button
          onClick={handleBack}
          disabled={currentStep === 1}
          className="px-4 py-2 text-sm font-medium text-gray-600 bg-gray-100 rounded-lg hover:bg-gray-200 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          Back
        </button>

        <button
          onClick={handleNext}
          disabled={isLoading}
          className="px-6 py-2 text-sm font-medium text-white bg-blue-600 rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        >
          {isLoading ? "Processing..." : currentStep === STEPS.length ? "Complete Setup" : "Next"}
        </button>
      </div>
    </div>
  )
}
