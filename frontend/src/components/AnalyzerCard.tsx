import { useState } from "react";
import type { AnalyzerResult } from "../utils/types";
import { verdictConfig, type VerdictKey } from "../utils/verdict";

interface Props {
  result: AnalyzerResult;
}

export function AnalyzerCard({ result }: Props) {
  const [expanded, setExpanded] = useState(false);
  const v = verdictConfig[result.verdict as VerdictKey] ?? verdictConfig.inconclusive;

  return (
    <div className="bg-white border border-[#BAE8FF]/60 rounded-lg overflow-hidden shadow-sm hover:shadow-md transition-all">
      <button
        onClick={() => setExpanded(!expanded)}
        className="w-full flex items-center justify-between p-4 hover:bg-slate-50 transition-colors text-left"
      >
        <div className="flex items-center gap-3">
          <span className={`text-lg ${v.color}`}>{v.emoji}</span>
          <span className="font-bold text-slate-700">{result.analyzer}</span>
        </div>
        <div className="flex items-center gap-3">
          <span className={`text-sm font-mono font-bold ${v.color}`}>
            {(result.score * 100).toFixed(1)}%
          </span>
          <svg
            className={`w-4 h-4 text-slate-400 transition-transform ${expanded ? "rotate-180" : ""}`}
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
          </svg>
        </div>
      </button>

      {expanded && (
        <div className="border-t border-[#BAE8FF]/60 bg-slate-50/50 px-4 pb-4">
          <table className="w-full text-sm mt-3">
            <thead>
              <tr className="text-slate-500 text-left font-semibold">
                <th className="pb-2 pr-4">Check</th>
                <th className="pb-2 pr-4">Value</th>
                <th className="pb-2">Status</th>
              </tr>
            </thead>
            <tbody>
              {result.findings.map((f, i) => (
                <tr key={i} className="border-t border-slate-100">
                  <td className="py-2 pr-4 text-slate-700 font-medium">{f.name}</td>
                  <td className="py-2 pr-4 font-mono text-slate-500 text-xs max-w-xs truncate">
                    {String(f.value)}
                  </td>
                  <td className="py-2">
                    <span
                      className={`text-xs font-bold px-2 py-0.5 rounded-full ${
                        f.suspicious
                          ? "bg-red-50 text-red-600 border border-red-200"
                          : "bg-emerald-50 text-emerald-600 border border-emerald-200"
                      }`}
                    >
                      {f.suspicious ? "Suspicious" : "OK"}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
