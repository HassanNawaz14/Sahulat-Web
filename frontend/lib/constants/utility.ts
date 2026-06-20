import { Zap, Flame, Droplets, Wifi, type Icon } from "lucide-react"

export const UTILITY_ICONS: Record<string, Icon> = {
  electricity: Zap,
  gas: Flame,
  water: Droplets,
  internet: Wifi,
}

export const UTILITY_COLORS: Record<string, string> = {
  electricity: "text-yellow-500",
  gas: "text-orange-500",
  water: "text-blue-500",
  internet: "text-purple-500",
}

export const UTILITY_BG_COLORS: Record<string, string> = {
  electricity: "bg-yellow-50 border-yellow-200",
  gas: "bg-orange-50 border-orange-200",
  water: "bg-blue-50 border-blue-200",
  internet: "bg-purple-50 border-purple-200",
}

export const STATUS_COLORS: Record<string, string> = {
  unpaid: "text-red-600 bg-red-50",
  paid: "text-green-600 bg-green-50",
  overdue: "text-orange-600 bg-orange-50",
}

export const PROVIDER_LABELS: Record<string, string> = {
  lesco: "LESCO",
  kelectric: "K-Electric",
  iesco: "IESCO",
  gepco: "GEPCO",
  fesco: "FESCO",
  mepco: "MEPCO",
  pesco: "PESCO",
  qesco: "QESCO",
  hesco: "HESCO",
  sepco: "SEPCO",
  sngpl: "SNGPL",
  ssgc: "SSGC",
  wasa_lhr: "WASA Lahore",
  kwsb: "KW&SB",
  ptcl: "PTCL",
  nayatel: "Nayatel",
}
