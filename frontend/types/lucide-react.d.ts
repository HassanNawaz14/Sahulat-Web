declare module "lucide-react" {
  import type { FC, SVGProps } from "react"
  export interface IconProps extends SVGProps<SVGSVGElement> {
    size?: number | string
  }
  export type Icon = FC<IconProps>
  export const Chrome: Icon
  export const Mail: Icon
  export const Phone: Icon
  export const Home: Icon
  export const User: Icon
  export const Bell: Icon
  export const LogOut: Icon
  export const Settings: Icon
  export const Zap: Icon
  export const Flame: Icon
  export const Droplet: Icon
  export const Droplets: Icon
  export const Wifi: Icon
  export const Tv: Icon
  export const Smartphone: Icon
  export const Sun: Icon
  export const ShoppingCart: Icon
  export const BookOpen: Icon
  export const MoreHorizontal: Icon
  export const ArrowLeft: Icon
  export const Plus: Icon
  export const X: Icon
  export const Share2: Icon
  export const RefreshCw: Icon
  export const ExternalLink: Icon
  export const Clock: Icon
  export const BarChart3: Icon
  export const Wallet: Icon
  export const CreditCard: Icon
  export const MapPin: Icon
  export const Calculator: Icon
  export const ArrowRight: Icon
  export const LayoutDashboard: Icon

  // Outage Tracker (P09)
  export const CircleAlert: Icon
  export const CircleCheck: Icon
  export const Search: Icon
  export const AlertCircle: Icon
  export const TriangleAlert: Icon
}
