export const verdictConfig = {
  authentic: {
    label: "Likely Authentic",
    color: "text-emerald-600",
    bg: "bg-emerald-50",
    border: "border-emerald-200",
    emoji: "✓",
  },
  suspicious: {
    label: "Suspicious",
    color: "text-amber-600",
    bg: "bg-amber-50",
    border: "border-amber-200",
    emoji: "⚠",
  },
  likely_fake: {
    label: "Manipulated",
    color: "text-red-600",
    bg: "bg-red-50",
    border: "border-red-200",
    emoji: "✗",
  },
  inconclusive: {
    label: "Inconclusive",
    color: "text-slate-500",
    bg: "bg-slate-50",
    border: "border-slate-200",
    emoji: "?",
  },
} as const;

export type VerdictKey = keyof typeof verdictConfig;
