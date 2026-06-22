export interface ConsumerNumberPattern {
  pattern: RegExp
  placeholder: string
  hint: string
}

export const CONSUMER_NUMBER_PATTERNS: Record<string, ConsumerNumberPattern> = {
  lesco: {
    pattern: /^\d{8,14}$/,
    placeholder: "e.g. 13112621101009",
    hint: "14-digit reference number",
  },
  kelectric: {
    pattern: /^\d{8,14}$/,
    placeholder: "e.g. 112233445566",
    hint: "11-digit consumer number",
  },
  iesco: {
    pattern: /^\d{8,14}$/,
    placeholder: "e.g. 12112621101009",
    hint: "14-digit reference number",
  },
  gepco: {
    pattern: /^\d{8,14}$/,
    placeholder: "e.g. 14112621101009",
    hint: "14-digit reference number",
  },
  fesco: {
    pattern: /^\d{8,14}$/,
    placeholder: "e.g. 15112621101009",
    hint: "14-digit reference number",
  },
  mepco: {
    pattern: /^\d{8,14}$/,
    placeholder: "e.g. 16112621101009",
    hint: "14-digit reference number",
  },
  pesco: {
    pattern: /^\d{8,14}$/,
    placeholder: "e.g. 17112621101009",
    hint: "14-digit reference number",
  },
  qesco: {
    pattern: /^\d{8,14}$/,
    placeholder: "e.g. 18112621101009",
    hint: "14-digit reference number",
  },
  hesco: {
    pattern: /^\d{8,14}$/,
    placeholder: "e.g. 19112621101009",
    hint: "14-digit reference number",
  },
  sepco: {
    pattern: /^\d{8,14}$/,
    placeholder: "e.g. 20112621101009",
    hint: "14-digit reference number",
  },
  sngpl: {
    pattern: /^\d{7,12}$/,
    placeholder: "e.g. 1234567",
    hint: "7-12 digit consumer number",
  },
  ssgc: {
    pattern: /^\d{7,12}$/,
    placeholder: "e.g. 7654321",
    hint: "7-12 digit consumer number",
  },
  wasa_lhr: {
    pattern: /^\d{8,12}$/,
    placeholder: "e.g. 12345678",
    hint: "8-12 digit account number",
  },
  kwsb: {
    pattern: /^\d{8,12}$/,
    placeholder: "e.g. 87654321",
    hint: "8-12 digit account number",
  },
  ptcl: {
    pattern: /^\d{10,11}$/,
    placeholder: "e.g. 04212345678 or 0511234567",
    hint: "10 or 11-digit phone number with area code",
  },
  nayatel: {
    pattern: /^[A-Z0-9]{6,12}$/i,
    placeholder: "e.g. AC123456",
    hint: "6-12 digit account number",
  },
}

export function getConsumerNumberPattern(providerCode: string): ConsumerNumberPattern {
  return CONSUMER_NUMBER_PATTERNS[providerCode] || {
    pattern: /^\d{3,}$/,
    placeholder: "Enter consumer number",
    hint: "Consumer number",
  }
}
