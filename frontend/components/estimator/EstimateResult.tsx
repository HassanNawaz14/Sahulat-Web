"use client"

import { Bell, BarChart3, Wallet, Zap, Flame, Droplets, Sun, CreditCard, MapPin } from "lucide-react"
import type { EstimateResult } from "@/types/estimate"
import SlabProgressBar from "./SlabProgressBar"

interface Props {
  result: EstimateResult
}

function CtaCard({ icon: Icon, title, description, module }: { icon: any; title: string; description: string; module: string }) {
  return (
    <a
      href="/auth/login"
      className="flex items-start gap-3 rounded-lg border border-gray-100 bg-white p-3 transition hover:border-blue-200 hover:bg-blue-50/50"
    >
      <div className="mt-0.5 flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-blue-50">
        <Icon className="h-4 w-4 text-blue-600" />
      </div>
      <div className="min-w-0">
        <p className="text-sm font-medium text-gray-900">{title}</p>
        <p className="mt-0.5 text-xs leading-relaxed text-gray-500">{description}</p>
        <span className="mt-1 inline-block text-[10px] font-medium uppercase tracking-wider text-blue-500">
          {module}
        </span>
      </div>
    </a>
  )
}

export default function EstimateResultCard({ result }: Props) {
  const isElec = result.utility_type === "electricity"
  const isGas = result.utility_type === "gas"
  const isWater = result.utility_type === "water"

  return (
    <div className="rounded-xl border border-gray-200 bg-white p-5 shadow-sm">
      <div className="mb-4 flex items-baseline justify-between">
        <div>
          <p className="text-xs text-gray-500">Estimated Total</p>
          <p className="text-3xl font-bold text-gray-900">
            Rs. {result.estimated_total.toLocaleString()}
          </p>
        </div>
        <span className="rounded-full bg-blue-50 px-2.5 py-1 text-xs font-medium text-blue-700">
          {result.tariff_version}
        </span>
      </div>

      {isElec && (
        <div className="mb-4">
          <SlabProgressBar breakdown={result.breakdown} currentUnits={result.units} />
        </div>
      )}

      <table className="w-full text-sm">
        <thead>
          <tr className="border-b border-gray-100 text-xs text-gray-500">
            <th className="pb-1.5 text-left font-medium">Slab</th>
            <th className="pb-1.5 text-right font-medium">Units</th>
            <th className="pb-1.5 text-right font-medium">Rate</th>
            <th className="pb-1.5 text-right font-medium">Amount</th>
          </tr>
        </thead>
        <tbody>
          {result.breakdown.map((line) => (
            <tr key={line.label} className="border-b border-gray-50">
              <td className="py-1.5 text-gray-700">{line.label}</td>
              <td className="py-1.5 text-right text-gray-600">
                {line.units > 0 ? line.units : "-"}
              </td>
              <td className="py-1.5 text-right text-gray-600">
                {line.rate > 0 ? line.rate : "-"}
              </td>
              <td className="py-1.5 text-right font-medium text-gray-900">
                Rs. {line.amount.toLocaleString()}
              </td>
            </tr>
          ))}
          <tr className="border-b border-gray-100 font-medium">
            <td className="py-1.5 text-gray-700">Taxes</td>
            <td />
            <td />
            <td className="py-1.5 text-right text-gray-900">
              Rs. {result.taxes.toLocaleString()}
            </td>
          </tr>
        </tbody>
        <tfoot>
          <tr className="text-base font-bold text-gray-900">
            <td className="pt-2">Total</td>
            <td />
            <td />
            <td className="pt-2 text-right">
              Rs. {result.estimated_total.toLocaleString()}
            </td>
          </tr>
        </tfoot>
      </table>

      {result.slab_warning && (
        <div className="mt-4 rounded-lg border border-amber-200 bg-amber-50 p-3">
          <div className="flex items-start gap-2">
            <Bell className="mt-0.5 h-4 w-4 shrink-0 text-amber-600" />
            <div>
              <p className="text-xs font-medium text-amber-800">
                Slab crossing warning — {result.slab_warning.units_to_next_slab} units away from next slab
              </p>
              <p className="mt-0.5 text-xs text-amber-700">
                Crossing to {result.slab_warning.next_slab_threshold}+ could cost an extra Rs.{" "}
                {result.slab_warning.estimated_extra_cost_if_crossed}/unit
                {result.slab_warning.units_to_next_slab && result.slab_warning.estimated_extra_cost_if_crossed > 0 && (
                  <> (approx. Rs. {(result.slab_warning.units_to_next_slab * result.slab_warning.estimated_extra_cost_if_crossed).toLocaleString()} if you cross)</>
                )}
              </p>
            </div>
          </div>
          <a
            href="/auth/login"
            className="mt-2 inline-flex items-center gap-1 text-xs font-medium text-amber-700 underline"
          >
            Get notified before you cross this slab →
          </a>
        </div>
      )}

      <p className="mt-3 text-[10px] text-gray-400">
        Tariff version: {result.tariff_version} | Based on NEPRA/OGRA notified rates
      </p>

      {/* ── Contextual sign-up CTAs ── */}
      <div className="mt-5 space-y-3">
        <p className="text-xs font-semibold uppercase tracking-wider text-gray-400">
          What you get after signing up
        </p>

        {isElec && result.slab_warning && (
          <CtaCard
            icon={Bell}
            title="Know before you cross a slab"
            description={`You are ${result.slab_warning.units_to_next_slab} units away from slab ${result.slab_warning.next_slab_threshold}+. Sahulat sends a push alert at 50, 20, and 10 units — giving you time to reduce usage and save Rs. 1,000+/month. No other Pakistani app offers this.`}
            module="P07 Consumption Monitor"
          />
        )}

        {isElec && !result.slab_warning && (
          <CtaCard
            icon={BarChart3}
            title="Track your actual consumption"
            description="Enter meter readings every few days and see your daily usage rate, projected end-of-month bill, and a live chart of your consumption — all before the official bill arrives."
            module="P07 Consumption Monitor"
          />
        )}

        {isGas && (
          <CtaCard
            icon={Flame}
            title="Track your gas consumption"
            description="Enter your gas meter readings and get end-of-month projections. Compare winter vs summer usage and never be surprised by your SNGPL/SSGC bill again."
            module="P07 Consumption Monitor"
          />
        )}

        {isWater && (
          <CtaCard
            icon={Droplets}
            title="Monitor your water usage"
            description="Track your WASA or KW&SB bills over time, set consumption goals, and get alerts if your usage spikes unexpectedly."
            module="P06 Bill Tracker"
          />
        )}

        <CtaCard
          icon={Zap}
          title="Auto-fetch your actual bill from the utility portal"
          description="Link your consumer account and Sahulat automatically fetches your bill from the official utility portal. No more visiting multiple websites or losing paper bills."
          module="P06 Bill Tracker"
        />

        <CtaCard
          icon={Wallet}
          title="Compare estimate vs actual & set budgets"
          description="Save this estimate and compare it with your actual bill when it arrives. Set monthly budget limits and get notified at 80% and 100% spend."
          module="P10 Budget Manager"
        />

        <CtaCard
          icon={Sun}
          title="See how much solar would save you"
          description="Enter your monthly bill amount and city — get a personalized solar recommendation: system size, estimated cost, monthly savings, and payback period."
          module="P16 Solar Sizing Tool"
        />

        <CtaCard
          icon={MapPin}
          title="Get load shedding alerts for your area"
          description="Know exactly when your area's scheduled power outage will hit. Get a push notification 15 minutes before — enough time to save your work and charge devices."
          module="P09 Outage Tracker"
        />

        <CtaCard
          icon={CreditCard}
          title="Pay with one tap"
          description="Deep-link directly to JazzCash or EasyPaisa with your consumer number pre-filled. No copying numbers or switching between apps."
          module="P15 Pay Gateway Lite"
        />
      </div>

      <a
        href="/auth/login"
        className="mt-5 flex w-full items-center justify-center gap-2 rounded-lg bg-blue-600 py-3 text-sm font-medium text-white transition hover:bg-blue-700"
      >
        Sign up free — Link your first utility in 30 seconds
      </a>

      {/* Ad slot: must stay below result, never above input form */}
      <div className="mt-4 h-24 rounded-lg bg-gray-50 flex items-center justify-center text-xs text-gray-400">
        Ad Slot
      </div>
    </div>
  )
}
