import { verdictConfig, type VerdictKey } from "../utils/verdict";

interface Props {
  score: number;
  verdict: string;
}

export function ScoreGauge({ score, verdict }: Props) {
  const v = verdictConfig[verdict as VerdictKey] ?? verdictConfig.inconclusive;
  const pct = Math.round(score * 100);

  // Map backend verdict names to the user-requested display labels: Authentic, Suspicious, Manipulated
  let labelText = "INCONCLUSIVE";
  if (verdict === "authentic") labelText = "AUTHENTIC";
  else if (verdict === "suspicious") labelText = "SUSPICIOUS";
  else if (verdict === "likely_fake") labelText = "MANIPULATED";

  // Score is between 0.0 (Authentic/Healthy) and 1.0 (Manipulated/Unhealthy)
  // Needle points left at score=1.0 (authentic, i.e. 100% authentic) and right at score=0.0 (fake, i.e. 0% authentic)
  // Wait, backend response format in pipeline.py:
  // auth_score = 1.0 - overall_score (where 1.0 is Authentic, 0.0 is Likely Fake)
  // So:
  // - pct = 100% -> Authentic -> Needle should point to the green (left side, i.e., -90 degrees)
  // - pct = 0% -> Manipulated -> Needle should point to the dark red (right side, i.e., 90 degrees)
  // So: rotation = (1 - score) * 180 - 90
  const rotation = (1.0 - score) * 180 - 90;

  return (
    <div className="flex flex-col items-center justify-center flex-shrink-0">
      <div className="relative w-64 h-36">
        <svg className="w-full h-full" viewBox="0 0 200 120">
          <defs>
            {/* Inner path for curved label */}
            <path id="text-path" d="M 45 96 A 55 55 0 0 1 155 96" fill="none" />
          </defs>

          {/* 6 colored arcs representing the ranges from left to right */}
          {/* Segment 1: Dark Green (Authentic) */}
          <path d="M 20 100 A 80 80 0 0 1 30.72 60" fill="none" stroke="#064e3b" strokeWidth="12" strokeLinecap="butt" />
          {/* Segment 2: Light Green */}
          <path d="M 30.72 60 A 80 80 0 0 1 60 30.72" fill="none" stroke="#22c55e" strokeWidth="12" strokeLinecap="butt" />
          {/* Segment 3: Yellow (Suspicious boundary) */}
          <path d="M 60 30.72 A 80 80 0 0 1 100 20" fill="none" stroke="#eab308" strokeWidth="12" strokeLinecap="butt" />
          {/* Segment 4: Orange */}
          <path d="M 100 20 A 80 80 0 0 1 140 30.72" fill="none" stroke="#f97316" strokeWidth="12" strokeLinecap="butt" />
          {/* Segment 5: Red (Manipulated boundary) */}
          <path d="M 140 30.72 A 80 80 0 0 1 169.28 60" fill="none" stroke="#ef4444" strokeWidth="12" strokeLinecap="butt" />
          {/* Segment 6: Dark Red */}
          <path d="M 169.28 60 A 80 80 0 0 1 180 100" fill="none" stroke="#7f1d1d" strokeWidth="12" strokeLinecap="butt" />

          {/* Curved label textPath */}
          <text className="text-[9px] font-extrabold tracking-[0.2em] font-mono fill-gray-400">
            <textPath href="#text-path" startOffset="50%" textAnchor="middle">
              {labelText}
            </textPath>
          </text>

          {/* Base border line */}
          <line x1="15" y1="100" x2="185" y2="100" stroke="#374151" strokeWidth="1.5" strokeDasharray="2 2" />

          {/* Speedometer needle */}
          <g transform={`rotate(${rotation}, 100, 100)`}>
            <line x1="100" y1="100" x2="100" y2="28" stroke="#000000" strokeWidth="3" strokeLinecap="round" />
            <polygon points="97,33 103,33 100,22" fill="#000000" />
          </g>

          {/* Center Pivot Point */}
          <circle cx="100" cy="100" r="7" fill="#1f2937" stroke="#9ca3af" strokeWidth="2" />
          <circle cx="100" cy="100" r="2" fill="#9ca3af" />
        </svg>
      </div>

      {/* Percentage value under the dial */}
      <div className="text-center -mt-2">
        <span className={`text-3xl font-extrabold tracking-tight ${v.color}`}>{pct}%</span>
        <span className="text-gray-500 text-xs block font-mono uppercase tracking-widest mt-0.5">Authenticity Score</span>
      </div>
    </div>
  );
}
