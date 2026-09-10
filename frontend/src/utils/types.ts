export interface Finding {
  name: string;
  value: string | number | boolean;
  suspicious: boolean;
  description: string;
}

export interface AnalyzerResult {
  analyzer: string;
  score: number;
  verdict: "authentic" | "suspicious" | "likely_fake" | "inconclusive";
  findings: Finding[];
}

export interface AnalysisResponse {
  overall_score: number;
  overall_verdict: "authentic" | "suspicious" | "likely_fake" | "inconclusive";
  analyzers: AnalyzerResult[];
  image_type: "face" | "object" | "mixed";
  face_count: number;
}
