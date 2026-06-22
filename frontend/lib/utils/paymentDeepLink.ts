export function buildJazzCashDeepLink(consumerNumber: string, amount: number): string {
  return `jazzcash://pay?type=utility&consumer=${encodeURIComponent(consumerNumber)}&amount=${amount}`
}

export function buildEasypaisaDeepLink(consumerNumber: string): string {
  return `easypaisa://billpayment?ref=${encodeURIComponent(consumerNumber)}`
}

export function buildJazzCashWebUrl(consumerNumber: string, amount: number): string {
  return `https://jazzcash.com.pk/pay?consumer=${encodeURIComponent(consumerNumber)}&amount=${amount}`
}

export function buildEasypaisaWebUrl(consumerNumber: string): string {
  return `https://easypaisa.com.pk/billpayment?ref=${encodeURIComponent(consumerNumber)}`
}
