import { useState } from "react";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { ImageUpload } from "./components/ImageUpload";
import { ResultsPanel } from "./components/ResultsPanel";
import { Header } from "./components/Header";
import { Documentation } from "./components/Documentation";
import Login from "./pages/Login";
import type { AnalysisResponse } from "./utils/types";
import { Eye, Brain, Zap, BarChart } from "lucide-react";

function Detector() {
  const [results, setResults] = useState<AnalysisResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);

  const handleUpload = async (file: File) => {
    setLoading(true);
    setError(null);
    setResults(null);
    setPreviewUrl(URL.createObjectURL(file));

    const form = new FormData();
    form.append("file", file);

    try {
      const res = await fetch("/api/v1/analyze", { method: "POST", body: form });
      if (!res.ok) {
        const data = await res.json().catch(() => ({ detail: "Analysis failed" }));
        throw new Error(data.detail || `HTTP ${res.status}`);
      }
      const data: AnalysisResponse = await res.json();
      setResults(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unknown error");
    } finally {
      setLoading(false);
    }
  };

  const handleReset = () => {
    setResults(null);
    setError(null);
    setPreviewUrl(null);
  };

  return (
    <div className="min-h-screen bg-gradient-to-tr from-[#E0F7FF] to-[#BAE8FF] font-sans text-slate-800">
      <Header />
      
      <main className="max-w-[1200px] mx-auto px-6 py-12">
        {/* Hero Section */}
        <div className="text-center mb-16">
          <h2 className="text-5xl font-extrabold text-slate-800 mb-6 tracking-tight leading-tight">
            Detect <span className="text-[#0096C7]">Deepfakes</span><br/>
            with Confidence
          </h2>
          <p className="text-slate-600 max-w-2xl mx-auto text-lg">
            Upload any image or video to analyze authenticity using our<br/>
            multi-layer forensic signal processing pipeline.
          </p>
        </div>

        {error && (
          <div className="max-w-2xl mx-auto mb-8 bg-red-50 border border-red-200 rounded-xl p-4 text-red-600 text-center flex items-center justify-center gap-4">
            <span>{error}</span>
            <button onClick={handleReset} className="text-sm underline hover:text-red-800 font-semibold">
              Try again
            </button>
          </div>
        )}

        {/* How it Works Banner */}
        {!results && !loading && (
          <div className="max-w-[1000px] mx-auto mb-12 border-t border-b border-[#BAE8FF] py-8">
            <h3 className="text-center text-xl font-extrabold text-slate-800 mb-8 tracking-tight">
              How it Works
            </h3>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-6 relative">
              {[
                { n: "01", title: "Upload", desc: "User submits an image file via the React frontend. It's routed to the FastAPI backend without compression." },
                { n: "02", title: "Analyzers Run", desc: "The Pipeline orchestrator runs all 12 forensic and ML analyzers concurrently, extracting local and global signals." },
                { n: "03", title: "Scores Weighted", desc: "Authenticity score above 70% is Authentic, 40% – 70% is Suspicious, and below 40% is Manipulated." },
                { n: "04", title: "JSON Report", desc: "A comprehensive report with raw scores, individual findings, and the final verdict is returned to the dashboard." },
              ].map((step) => (
                <div key={step.n} className="flex flex-col items-center text-center">
                  <div className="w-10 h-10 bg-white border border-[#0096C7] rounded-full flex items-center justify-center font-mono font-bold text-[#0096C7] mb-3 text-sm shadow-md">
                    {step.n}
                  </div>
                  <h4 className="text-slate-800 font-bold text-sm mb-1.5">{step.title}</h4>
                  <p className="text-slate-500 text-xs leading-relaxed max-w-[200px]">{step.desc}</p>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Main Content Area */}
        {!results && !loading ? (
          <div className="grid md:grid-cols-2 gap-6 mb-16 max-w-[1000px] mx-auto">
            {/* Left: Upload */}
            <ImageUpload onUpload={handleUpload} isLoading={loading} />

            {/* Right: No Results Placeholder */}
            <div className="bg-white border border-[#BAE8FF]/60 shadow-lg rounded-2xl p-6 flex flex-col items-center justify-center h-full min-h-[400px]">
              <div className="w-16 h-16 bg-[#E0F7FF]/50 rounded-2xl flex items-center justify-center mb-6 border border-[#BAE8FF]/60">
                <Eye className="w-8 h-8 text-[#0096C7]" />
              </div>
              <h3 className="text-slate-700 font-semibold mb-2">No results yet</h3>
              <p className="text-slate-500 text-sm text-center max-w-[200px]">
                Upload an image or video and click Analyze to detect deepfakes
              </p>
            </div>
          </div>
        ) : loading ? (
          <div className="grid md:grid-cols-2 gap-6 mb-16 max-w-[1000px] mx-auto">
            <ImageUpload onUpload={handleUpload} isLoading={loading} />
            <div className="bg-white border border-[#BAE8FF]/60 shadow-lg rounded-2xl p-6 flex flex-col items-center justify-center h-full min-h-[400px]">
              <div className="w-12 h-12 border-4 border-[#0096C7] border-t-transparent rounded-full animate-spin mb-4" />
              <p className="text-slate-600 font-semibold">Running forensic analysis...</p>
            </div>
          </div>
        ) : (
          <div className="mb-16">
            <ResultsPanel results={results!} imageUrl={previewUrl!} onReset={handleReset} />
          </div>
        )}

        {/* Feature Cards */}
        {!results && (
          <div className="grid md:grid-cols-3 gap-6 max-w-[1000px] mx-auto mt-24">
            <div className="bg-white border border-[#BAE8FF]/60 rounded-2xl p-6 flex flex-col items-center text-center hover:border-[#0096C7]/30 shadow-md hover:shadow-lg transition-all">
              <div className="mb-4 w-12 h-12 bg-pink-50 rounded-xl flex items-center justify-center">
                <Brain className="w-6 h-6 text-pink-500" />
              </div>
              <h4 className="text-slate-800 font-bold mb-2">Signal Processing</h4>
              <p className="text-slate-500 text-xs leading-relaxed">
                Deterministic forensic algorithms<br/>
                built on NumPy &amp; SciPy signal extraction
              </p>
            </div>
            
            <div className="bg-white border border-[#BAE8FF]/60 rounded-2xl p-6 flex flex-col items-center text-center hover:border-[#0096C7]/30 shadow-md hover:shadow-lg transition-all">
              <div className="mb-4 w-12 h-12 bg-orange-50 rounded-xl flex items-center justify-center">
                <Zap className="w-6 h-6 text-orange-500" />
              </div>
              <h4 className="text-slate-800 font-bold mb-2">Real-Time Detection</h4>
              <p className="text-slate-500 text-xs leading-relaxed">
                OpenCV Haar Cascade face tracking with<br/>
                multi-threaded frame analysis
              </p>
            </div>

            <div className="bg-white border border-[#BAE8FF]/60 rounded-2xl p-6 flex flex-col items-center text-center hover:border-[#0096C7]/30 shadow-md hover:shadow-lg transition-all">
              <div className="mb-4 w-12 h-12 bg-emerald-50 rounded-xl flex items-center justify-center">
                <BarChart className="w-6 h-6 text-emerald-600" />
              </div>
              <h4 className="text-slate-800 font-bold mb-2">Pure Explainability</h4>
              <p className="text-slate-500 text-xs leading-relaxed">
                Detailed analyzer breakdown with<br/>
                raw forensic data and score weighting
              </p>
            </div>
          </div>
        )}
      </main>
      <Documentation />
    </div>
  );
}

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route path="/" element={<Detector />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  );
}
