import { useState } from "react";
import { AlertTriangle } from "lucide-react";
import type { AnalysisResponse } from "../utils/types";
import { ScoreGauge } from "./ScoreGauge";
import { AnalyzerCard } from "./AnalyzerCard";

interface Props {
  results: AnalysisResponse;
  imageUrl: string;
  onReset: () => void;
}

function getAspectRatio(w: number, h: number): string {
  const gcd = (a: number, b: number): number => (b === 0 ? a : gcd(b, a % b));
  const divisor = gcd(w, h);
  return `${w / divisor}:${h / divisor}`;
}

export function ResultsPanel({ results, imageUrl, onReset }: Props) {
  const noFace = results.face_count === 0;
  const [dimensions, setDimensions] = useState<{ width: number; height: number } | null>(null);

  const handleImageLoad = (e: React.SyntheticEvent<HTMLImageElement>) => {
    const { naturalWidth, naturalHeight } = e.currentTarget;
    setDimensions({ width: naturalWidth, height: naturalHeight });
  };

  return (
    <div className="space-y-8">
      {/* 2-Column Grid Layout */}
      <div className="grid md:grid-cols-2 gap-8 max-w-[1100px] mx-auto items-stretch">
        
        {/* Left Column: Image Card + Specifications Card */}
        <div className="flex flex-col gap-4">
          <div className="bg-white rounded-xl overflow-hidden border border-[#BAE8FF]/60 shadow-lg">
            <img 
              src={imageUrl} 
              alt="Uploaded" 
              className="w-full object-contain max-h-[400px]" 
              onLoad={handleImageLoad}
            />
          </div>

          <div className="bg-white border border-[#BAE8FF]/60 rounded-xl p-5 space-y-4 shadow-lg flex-1">
            <h4 className="text-xs font-bold text-slate-500 uppercase tracking-wider font-mono">Image Specifications</h4>
            <div className="grid grid-cols-2 gap-4 text-xs font-mono">
              <div className="bg-[#E0F7FF]/20 p-3 rounded-lg border border-[#BAE8FF]/50">
                <div className="text-slate-500 font-semibold mb-1">ANALYSIS TYPE</div>
                <div className="text-slate-800 capitalize font-extrabold">
                  {results.image_type === "face" ? "Face Portrait" : results.image_type === "mixed" ? "Mixed Scene" : "General Object"}
                </div>
              </div>
              <div className="bg-[#E0F7FF]/20 p-3 rounded-lg border border-[#BAE8FF]/50">
                <div className="text-slate-500 font-semibold mb-1">DETECTED FACES</div>
                <div className="text-slate-800 font-extrabold">
                  {results.face_count} {results.face_count === 1 ? 'face' : 'faces'}
                </div>
              </div>
              {dimensions && (
                <>
                  <div className="bg-[#E0F7FF]/20 p-3 rounded-lg border border-[#BAE8FF]/50">
                    <div className="text-slate-500 font-semibold mb-1">DIMENSIONS</div>
                    <div className="text-slate-800 font-extrabold">{dimensions.width} × {dimensions.height}</div>
                  </div>
                  <div className="bg-[#E0F7FF]/20 p-3 rounded-lg border border-[#BAE8FF]/50">
                    <div className="text-slate-500 font-semibold mb-1">ASPECT RATIO</div>
                    <div className="text-slate-800 font-extrabold">{getAspectRatio(dimensions.width, dimensions.height)}</div>
                  </div>
                </>
              )}
            </div>
          </div>
        </div>

        {/* Right Column: Speedometer Dial Gauge Card */}
        <div className="bg-white border border-[#BAE8FF]/60 rounded-2xl p-8 flex flex-col items-center justify-center gap-8 shadow-xl">
          <ScoreGauge score={results.overall_score} verdict={results.overall_verdict} />
          
          <button
            onClick={onReset}
            className="px-6 py-2.5 rounded-xl bg-slate-100 hover:bg-slate-200 text-slate-700 text-sm font-bold transition-all border border-slate-200 w-full max-w-[200px] shadow-sm"
          >
            Analyze another
          </button>
        </div>

      </div>

      {/* No Face Detected Banner */}
      {noFace && (
        <div className="bg-amber-50 border border-amber-200 rounded-xl p-5 flex items-start gap-4 max-w-[1100px] mx-auto shadow-sm">
          <div className="flex-shrink-0 mt-0.5">
            <AlertTriangle className="w-6 h-6 text-amber-600" />
          </div>
          <div>
            <h3 className="text-amber-800 font-bold text-base">
              No Face Detected
            </h3>
            <p className="text-amber-700 text-sm mt-1 leading-relaxed">
              No human face was found in this image. DeepGuard is optimized for detecting
              facial deepfakes — results may be less accurate for non-face images.
              The forensic analyzers below still check for general signs of image manipulation
              (metadata stripping, compression artifacts, frequency anomalies, etc.).
            </p>
          </div>
        </div>
      )}

      {/* Forensic and Digital Provenance Breakdown */}
      <div className="max-w-[1100px] mx-auto space-y-4">
        <div className="flex items-center justify-between">
          <h3 className="text-lg font-extrabold text-slate-800 tracking-tight">
            Forensic & Digital Provenance Breakdown
          </h3>
          <span className="text-xs text-slate-500 font-mono font-semibold">
            {results.analyzers.length} active analyzers
          </span>
        </div>
        
        <div className="grid md:grid-cols-2 gap-4">
          {results.analyzers.map((result, idx) => (
            <AnalyzerCard key={idx} result={result} />
          ))}
        </div>
      </div>
    </div>
  );
}

