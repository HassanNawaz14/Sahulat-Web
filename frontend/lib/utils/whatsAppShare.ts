export function buildWhatsAppShareText(
  providerLabel: string,
  accountLabel: string | null,
  billingMonth: string | null,
  amountPayable: number,
  dueDate: string | null,
  unitsConsumed: number | null,
): string {
  const month = billingMonth
    ? new Date(billingMonth).toLocaleDateString("en", { month: "long", year: "numeric" })
    : "Current"

  const parts = [
    `*Sahulat Bill Summary*`,
    `Utility: ${providerLabel}${accountLabel ? ` (${accountLabel})` : ""}`,
    `Month: ${month}`,
    `Amount: Rs. ${(amountPayable || 0).toLocaleString()}`,
  ]

  if (dueDate) {
    parts.push(`Due Date: ${dueDate}`)
  }

  if (unitsConsumed != null) {
    parts.push(`Units: ${unitsConsumed} kWh`)
  }

  parts.push(``)
  parts.push(`Track your bills on Sahulat: https://sahulat.pk`)

  return encodeURIComponent(parts.join("\n"))
}

export function openWhatsAppShare(text: string) {
  window.open(`https://wa.me/?text=${text}`, "_blank")
}
