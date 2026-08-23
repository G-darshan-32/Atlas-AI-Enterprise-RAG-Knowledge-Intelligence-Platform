"use client";
import { useWorkspaceStore } from "@/store/workspace.store";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Check, Zap, Building2, ArrowUpRight } from "lucide-react";
import { formatBytes } from "@/lib/utils";

const PLANS = [
  {
    id: "free",
    name: "Free",
    price: "$0",
    period: "forever",
    storage: "5 GB",
    members: "3 members",
    docs: "100 documents",
    color: "border-white/10",
    badge: "outline" as const,
    features: ["Basic RAG chat", "Semantic search", "3 workspaces", "Community support"],
  },
  {
    id: "pro",
    name: "Pro",
    price: "$49",
    period: "per workspace / month",
    storage: "50 GB",
    members: "25 members",
    docs: "Unlimited documents",
    color: "border-atlas-500/40",
    badge: "atlas" as const,
    highlight: true,
    features: [
      "Everything in Free",
      "Multi-agent AI (LangGraph)",
      "GitHub integration",
      "Advanced analytics",
      "AI-generated reports",
      "Priority support",
    ],
  },
  {
    id: "enterprise",
    name: "Enterprise",
    price: "Custom",
    period: "annual contract",
    storage: "Unlimited",
    members: "Unlimited members",
    docs: "Unlimited documents",
    color: "border-purple-500/30",
    badge: "info" as const,
    features: [
      "Everything in Pro",
      "SSO / SAML",
      "Custom embedding models",
      "On-premise deployment",
      "SLA guarantee",
      "Dedicated success manager",
      "Audit logs + SIEM export",
    ],
  },
];

export default function BillingPage() {
  const { activeWorkspace } = useWorkspaceStore();
  const currentTier = activeWorkspace?.tier || "free";

  return (
    <div className="p-6 max-w-5xl">
      <div className="mb-8">
        <h1 className="text-2xl font-bold">Billing</h1>
        <p className="text-white/40 text-sm mt-0.5">Manage your plan and usage</p>
      </div>

      {/* Current plan banner */}
      <div className="p-5 rounded-xl border border-atlas-500/20 bg-atlas-500/5 mb-8 flex items-center justify-between">
        <div>
          <p className="text-sm text-white/60">Current plan</p>
          <p className="text-xl font-bold text-white capitalize mt-0.5">{currentTier}</p>
          {activeWorkspace && (
            <div className="flex items-center gap-4 mt-2 text-xs text-white/40">
              <span>{formatBytes(activeWorkspace.storage_used_bytes)} / {formatBytes(activeWorkspace.storage_quota_bytes)} storage</span>
            </div>
          )}
        </div>
        <Badge variant={currentTier === "enterprise" ? "atlas" : currentTier === "pro" ? "info" : "outline"} className="capitalize">
          {currentTier}
        </Badge>
      </div>

      {/* Plans */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
        {PLANS.map((plan) => (
          <div
            key={plan.id}
            className={`rounded-xl border p-5 flex flex-col ${plan.color} ${
              plan.highlight ? "bg-atlas-500/5" : "bg-white/[0.02]"
            } relative`}
          >
            {plan.highlight && (
              <span className="absolute -top-3 left-1/2 -translate-x-1/2 bg-gradient-to-r from-atlas-500 to-purple-500 text-white text-xs font-semibold px-3 py-1 rounded-full">
                Most Popular
              </span>
            )}

            <div className="mb-4">
              <div className="flex items-center justify-between mb-1">
                <h3 className="font-semibold text-white">{plan.name}</h3>
                {currentTier === plan.id && <Badge variant="success" className="text-xs">Current</Badge>}
              </div>
              <div className="flex items-baseline gap-1">
                <span className="text-2xl font-bold text-white">{plan.price}</span>
                {plan.price !== "Custom" && <span className="text-xs text-white/30">{plan.period}</span>}
              </div>
            </div>

            <ul className="space-y-2 mb-5 flex-1">
              {plan.features.map((f) => (
                <li key={f} className="flex items-start gap-2 text-xs text-white/60">
                  <Check className="w-3.5 h-3.5 text-emerald-400 flex-shrink-0 mt-0.5" />
                  {f}
                </li>
              ))}
            </ul>

            <Button
              variant={plan.highlight ? "atlas" : "outline"}
              size="sm"
              className={!plan.highlight ? "border-white/10 text-white/60 hover:text-white" : ""}
              disabled={currentTier === plan.id}
            >
              {currentTier === plan.id
                ? "Current plan"
                : plan.price === "Custom"
                ? "Contact sales"
                : `Upgrade to ${plan.name}`}
            </Button>
          </div>
        ))}
      </div>

      {/* Demo notice */}
      <div className="rounded-xl border border-amber-500/20 bg-amber-500/5 p-4 text-center">
        <p className="text-sm text-amber-300/80">
          This is a demo billing UI. No real payments are processed.
          In production, this would integrate with Stripe.
        </p>
      </div>
    </div>
  );
}
