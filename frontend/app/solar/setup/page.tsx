"use client"

const STEPS = [
  { id: 1, title: "Select Inverter Brand", description: "Choose from supported solar inverter brands" },
  { id: 2, title: "Enter System Size", description: "Specify your solar panel system capacity" },
  { id: 3, title: "Enter Installation Cost", description: "Total investment in PKR" },
  { id: 4, title: "Link Consumer Account", description: "Connect to your electricity bill account" },
  { id: 5, title: "Configure Net Metering", description: "Set up net metering preferences" },
  { id: 6, title: "Enter Inverter Credentials", description: "Upload API credentials for monitoring" },
  { id: 7, title: "Test Connection", description: "Verify API access and fetch production data" },
]

export default function SolarSetupPage() {
  const [currentStep, setCurrentStep] = useState(1)
  const [formData, setFormData] = useState<any>({})
  const [isLoading, setIsLoading] = useState(false)

  const updateFormData = (field: string, value: any) => {
    setFormData((prev) => ({ ...prev, [field]: value }))
  }

  const validateCurrentStep = () => {
    // Simplified validation for demonstration
    switch (currentStep) {
      case 1:
        return formData.inverter_brand && ["growatt", "solis", "huawei"].includes(formData.inverter_brand)
      case 2:
        return formData.system_size_kw && formData.system_size_kw > 0 && formData.system_size_kw <= 100
      case 3:
        return formData.system_cost_pkr && formData.system_cost_pkr > 0
      default:
        return true
    }
  }

  const handleNext = () => {
    if (validateCurrentStep()) {
      if (currentStep < STEPS.length) {
        setCurrentStep(currentStep + 1)
      } else {
        handleSubmit()
      }
    }
  }

  const handleBack = () => {
    if (currentStep > 1) {
      setCurrentStep(currentStep - 1)
    }
  }

  const handleSubmit = async () => {
    setIsLoading(true)
    try {
      const response = await fetch("/api/solar/installations", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          ...formData,
          user_id: "current-user-id", // In real app, this from auth context
        }),
      })

      if (response.ok) {
        const installation = await response.json()
        // Redirect to dashboard
        window.location.href = `/solar/${installation.id}`
      } else {
        console.error("Failed to create installation")
      }
    } catch (error) {
      console.error("Error creating installation:", error)
    } finally {
      setIsLoading(false)
    }
  }

  const renderStepContent = () => {
    switch (currentStep) {
      case 1:
        return (
          <div className="space-y-4">
            <h3 className="text-lg font-semibold">Select Inverter Brand</h3>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {[
                { value: "growatt", label: "Growatt", icon: "⚡", status: "V1 Supported" },
                { value: "solis", label: "Solis", icon: "🔋", status: "Coming Soon" },
                { value: "huawei", label: "Huawei", icon: "📶", status: "Coming Soon" },
              ].map((brand) => (
                <button
                  key={brand.value}
                  onClick={() => updateFormData("inverter_brand", brand.value)}
                  className={`p-6 rounded-lg border-2 transition-all ${formData.inverter_brand === brand.value
                      ? "border-blue-500 bg-blue-50"
                      : "border-gray-200 hover:border-gray-300 hover:bg-gray-50"
                    }`}
                >
                  <div className="text-3xl mb-3">{brand.icon}</div>
                  <div className="font-semibold text-gray-900">{brand.label}</div>
                  <div className="text-sm text-gray-500 mt-1">{brand.status}</div>
                </button>
              ))}
            </div>
          </div>
        )

      case 2:
        return (
          <div className="space-y-6">
            <h3 className="text-lg font-semibold">Enter System Size</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  System Size (kW) <span className="text-red-500">*</span>
                </label>
                <input
                  type="number"
                  min="1"
                  max="100"
                  step="0.5"
                  value={formData.system_size_kw || ""}
                  onChange={(e) => updateFormData("system_size_kw", parseFloat(e.target.value))}
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  placeholder="e.g., 10"
                />
                <p className="text-sm text-gray-500 mt-1">Range: 1 - 100 kW</p>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Panel Count (optional)
                </label>
                <input
                  type="number"
                  min="1"
                  max="10000"
                  value={formData.panel_count || ""}
                  onChange={(e) => updateFormData("panel_count", parseInt(e.target.value))}
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  placeholder="e.g., 20"
                />
              </div>
            </div>
          </div>
        )

      case 3:
        return (
          <div className="space-y-6">
            <h3 className="text-lg font-semibold">Enter Installation Cost</h3>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Installation Cost (PKR) <span className="text-red-500">*</span>
              </label>
              <div className="relative">
                <span className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-500">Rs.</span>
                <input
                  type="number"
                  min="1"
                  max="99999999"
                  value={formData.system_cost_pkr || ""}
                  onChange={(e) => updateFormData("system_cost_pkr", parseFloat(e.target.value))}
                  className="w-full pl-12 pr-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  placeholder="e.g., 1,200,000"
                />
              </div>
              <p className="text-sm text-gray-500 mt-1">Maximum: 99,999,999 PKR</p>
            </div>
          </div>
        )

      case 4:
        return (
          <div className="space-y-6">
            <h3 className="text-lg font-semibold">Link Consumer Account</h3>
            <p className="text-sm text-gray-600">
              Select your electricity consumer account to automatically calculate savings based on your DISCO tariffs.
            </p>
            <div className="border border-gray-200 rounded-lg p-4 bg-gray-50">
              <div className="flex items-center justify-between mb-3">
                <div>
                  <h4 className="font-medium text-gray-900">LESCO - Main Meter</h4>
                  <p className="text-sm text-gray-600">Consumer: 13-11262-1101009-U</p>
                </div>
                <button
                  onClick={() => updateFormData("home_id", "home_123")}
                  className="px-4 py-2 bg-white border border-gray-300 text-sm font-medium rounded-lg hover:bg-gray-50"
                >
                  Select
                </button>
              </div>
            </div>
            <div className="text-center">
              <button
                onClick={() => updateFormData("home_id", null)}
                className="text-sm text-blue-600 hover:text-blue-800 font-medium"
              >
                Skip for now (manual calculations)
              </button>
            </div>
          </div>
        )

      case 5:
        return (
          <div className="space-y-6">
            <h3 className="text-lg font-semibold">Configure Net Metering</h3>
            <div className="space-y-4">
              <div className="flex items-center justify-between p-4 border border-gray-200 rounded-lg">
                <div>
                  <h4 className="font-medium text-gray-900">Enable Net Metering</h4>
                  <p className="text-sm text-gray-600">
                    Calculate export credits based on NEPRA buyback rates
                  </p>
                </div>
                <label className="relative inline-block w-12 h-6">
                  <input
                    type="checkbox"
                    checked={formData.net_metering_enabled || false}
                    onChange={(e) => updateFormData("net_metering_enabled", e.target.checked)}
                    className="sr-only"
                  />
                  <div
                    className={`w-12 h-6 rounded-full transition-colors ${formData.net_metering_enabled ? "bg-blue-600" : "bg-gray-300"}`}
                  >
                    <div
                      className={`w-5 h-5 bg-white rounded-full shadow-md transform transition-transform ${formData.net_metering_enabled ? "translate-x-6" : "translate-x-0.5"}`}
                    />
                  </div>
                </label>
              </div>

              {formData.net_metering_enabled && (
                <div className="p-4 bg-blue-50 border border-blue-200 rounded-lg">
                  <p className="text-sm text-blue-800">
                    <strong>Export Rate:</strong> Rs. 27/unit (NEPRA buyback rate)
                  </p>
                  <p className="text-xs text-blue-700 mt-1">
                    Your exported solar energy will earn credits at this rate
                  </p>
                </div>
              )}
            </div>
          </div>
        )

      case 6:
        return (
          <div className="space-y-6">
            <h3 className="text-lg font-semibold">Enter Inverter Credentials</h3>
            <p className="text-sm text-gray-600">
              Connect your solar inverter account to automatically fetch production data. You can skip this and enter data manually later.
            </p>

            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Username
                </label>
                <input
                  type="text"
                  value={formData.api_username || ""}
                  onChange={(e) => updateFormData("api_username", e.target.value)}
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  placeholder="Growatt username or account ID"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Password
                </label>
                <input
                  type="password"
                  value={formData.api_password || ""}
                  onChange={(e) => updateFormData("api_password", e.target.value)}
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  placeholder="Growatt password"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Plant ID (optional)
                </label>
                <input
                  type="text"
                  value={formData.plant_id || ""}
                  onChange={(e) => updateFormData("plant_id", e.target.value)}
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  placeholder="e.g., plant_123"
                />
              </div>
            </div>

            <div className="border-t border-gray-200 pt-4">
              <button
                onClick={() => updateFormData("api_username", null)
                className="text-sm text-blue-600 hover:text-blue-800 font-medium"
              >
                Skip API connection (manual data entry)
              </button>
            </div>
          </div>
        )

      case 7:
        return (
          <div className="space-y-6">
            <h3 className="text-lg font-semibold">Test Connection</h3>
            <div className="p-6 bg-gray-50 rounded-lg border border-gray-200">
              {isLoading ? (
                <div className="text-center">
                  <div className="h-8 w-8 border-4 border-blue-600 border-t-transparent rounded-full animate-spin mx-auto mb-4" />
                  <p className="text-sm text-gray-600">Testing inverter connection...</p>
                </div>
              ) : (
                <div className="text-center">
                  {formData.api_username && formData.api_password ? (
                    <>
                      <div className="h-12 w-12 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4">
                        <svg className="h-6 w-6 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                        </svg>
                      </div>
                      <h4 className="font-semibold text-gray-900 mb-2">Ready to Connect</h4>
                      <p className="text-sm text-gray-600">
                        Your inverter credentials are configured and ready for connection.
                      </p>
                    </>
                  ) : (
                    <>
                      <div className="h-12 w-12 bg-amber-100 rounded-full flex items-center justify-center mx-auto mb-4">
                        <svg className="h-6 w-6 text-amber-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.5M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                        </svg>
                      </div>
                      <h4 className="font-semibold text-gray-900 mb-2">Manual Entry Mode</h4>
                      <p className="text-sm text-gray-600">
                        No API credentials provided. You'll enter production data manually.
                      </p>
                    </>
                  )}
                </div>
              )}
            </div>
          </div>
        )

      default:
        return null
    }
  }

  return (
    <main className="mx-auto max-w-4xl px-4 py-8">
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-gray-900">Set Up Solar Installation</h1>
        <p className="text-sm text-gray-600 mt-1">
          Follow the steps to add your solar system to Sahulat
        </p>
      </div>

      {/* Progress Indicator */}
      <div className="mb-8">
        <div className="flex items-center justify-between mb-2">
          {STEPS.map((_, index) => (
            <div
              key={index}
              className={`flex-1 h-2 mx-1 rounded-full ${index < currentStep
                  ? "bg-blue-600"
                  : index === currentStep
                  ? "bg-blue-300"
                  : "bg-gray-200"
                }`}
            />
          ))}
        </div>
        <div className="flex justify-between text-xs text-gray-500 mt-1">
          {STEPS.map((_, index) => (
            <span key={index} className={index === currentStep - 1 ? "font-medium text-blue-600" : ""}>
              {index === 0
                ? "Brand"
                : index === 1
                ? "Size"
                : index === 2
                ? "Cost"
                : index === 3
                ? "Account"
                : index === 4
                ? "Metering"
                : index === 5
                ? "API"
                : index === 6
                ? "Test"
                : ""
              }
            </span>
          ))}
        </div>
      </div>

      {/* Step Content */}
      <div className="mb-8">{renderStepContent()}</div>

      {/* Navigation Buttons */}
      <div className="flex justify-between">
        <button
          onClick={handleBack}
          disabled={currentStep === 1}
          className="px-6 py-3 text-sm font-medium text-gray-600 bg-gray-100 rounded-lg hover:bg-gray-200 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          Back
        </button>

        <button
          onClick={handleNext}
          disabled={isLoading || (currentStep === STEPS.length && !validateCurrentStep())}
          className="px-8 py-3 text-sm font-medium text-white bg-blue-600 rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        >
          {isLoading
            ? "Processing..."
            : currentStep === STEPS.length
            ? "Complete Setup"
            : "Next"
          }
        </button>
      </div>
    </main>
  )
}
