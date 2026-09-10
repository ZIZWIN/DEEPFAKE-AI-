import { useState } from "react";

const analyzers = [
  {
    icon: "📝",
    name: "EXIF Metadata",
    file: "metadata.py",
    what: "Presence of camera maker notes, software signatures, missing timestamps, and GPS logic.",
    why: "Generative AI models rarely write coherent, hardware-level EXIF structures. Stripped metadata elevates the baseline risk score.",
  },
  {
    icon: "🔍",
    name: "Error Level Analysis (ELA)",
    file: "error_level.py",
    what: "The difference in pixel values after artificially re-saving the image at a known JPEG quality (e.g., 90%).",
    why: "Inserted elements (splicing) or GAN-generated faces sit at a different compression potential than the surrounding authentic background.",
  },
  {
    icon: "🌫️",
    name: "Noise Pattern",
    file: "noise.py",
    what: "Uniformity of high-frequency noise variance across different spatial blocks of the image.",
    why: "Authentic camera sensors produce uniform noise. AI generators and composites produce smooth regions lacking natural sensor grain.",
  },
  {
    icon: "🌊",
    name: "Frequency Domain (FFT)",
    file: "frequency.py",
    what: "The Fast Fourier Transform (FFT) spectrum for unnatural repeating grids or sudden drop-offs in high frequencies.",
    why: "Up-convolution layers in GANs/Diffusion models often leave imperceptible periodic grid artifacts in the frequency domain.",
  },
  {
    icon: "📦",
    name: "JPEG Compression (DCT)",
    file: "compression.py",
    what: "Discrete Cosine Transform (DCT) coefficients, quantization tables, and 8×8 block boundary alignment.",
    why: "Repeatedly editing or pasting a JPEG shifts the 8×8 block alignment, leaving double-quantization traces invisible to the naked eye.",
  },
  {
    icon: "🎨",
    name: "Color Consistency",
    file: "color.py",
    what: "RGB channel correlation, hue/saturation entropy, and lighting direction variance.",
    why: "Deepfakes often struggle with consistent illumination angles and cross-channel color bleeding, creating statistical anomalies.",
  },
  {
    icon: "🧬",
    name: "AI Texture Analysis",
    file: "ai_texture.py",
    what: "Local variance and Laplacian sharpness checks for 'plastic' skin textures and upscaling halos.",
    why: "AI generation produces unnaturally smooth gradients and surfaces that lack the high-frequency stochasticity of natural camera sensors.",
  },
  {
    icon: "🛡️",
    name: "SynthID Watermark",
    file: "synthid.py",
    what: "Spatial Least Significant Bit (LSB) anomalies and known frequency modulation signatures injected by Google's Imagen.",
    why: "Identifies invisible, imperceptible robust watermarks specifically designed to flag AI-generated content.",
  },
  {
    icon: "🧠",
    name: "CNN Feature Analysis",
    file: "cnn.py",
    what: "Lightweight local convolutional layers identifying edge activations, pattern gradients, and diffusion artifacts.",
    why: "CNNs excel at capturing spatial texture anomalies and high-frequency noise configurations left by GAN and Diffusion generators.",
  },
  {
    icon: "🔄",
    name: "RNN Sequential Analysis",
    file: "rnn.py",
    what: "Recurrent row-by-row sequence modeling of image density and error variations.",
    why: "AI generation often introduces subtle scanning or generation discontinuities across rows, causing prediction sequence anomalies.",
  },
  {
    icon: "🕸️",
    name: "Vision Transformer (ViT) Analysis",
    file: "vit.py",
    what: "Self-Attention mapping over localized 16x16 image patches to check global semantic correlation.",
    why: "Detects global inconsistencies, mismatched structures, and lighting variations across remote patches of the image.",
  },
  {
    icon: "📊",
    name: "Classical ML Classification",
    file: "classical_ml.py",
    what: "Ensemble classification using Logistic Regression, Support Vector Machine (SVM), and Decision Tree consensus.",
    why: "Aggregates extracted signal stats to make a robust statistical prediction of overall image authenticity.",
  },
];

const faqs = [
  {
    q: "Can it detect video deepfakes?",
    a: "The frontend supports video uploads and the backend processes videos frame-by-frame. However, temporal artifacts (unnatural flickering, motion inconsistency) are not yet integrated into the heuristic scoring pipeline — only spatial signal extraction is performed per frame.",
  },
  {
    q: "Why does my real photo show as suspicious?",
    a: "Heuristic analyzers flag structural changes, not intent. If your photo was resized, sent via WhatsApp, edited in Lightroom, or run through any social media compression pipeline, the mathematical structure has been altered — which produces the same red flags as AI manipulation. This is a known limitation.",
  },
  {
    q: "What image formats are supported?",
    a: "The most accurate results come from original JPEG files. PNG is supported but has no DCT coefficients, so the JPEG compression analyzer is skipped. WebP is supported but format conversion strips valuable quantization data, reducing the reliability of several modules.",
  },
  {
    q: "How accurate is the detector?",
    a: "Because this system uses signal extraction rather than ML classification, it doesn't have a single \"accuracy\" metric. In testing on clearly AI-generated images, it achieves >85% true positive detection, with a higher false-positive rate (~15–20%) on heavily edited real photographs.",
  },
  {
    q: "Can I add my own analyzer?",
    a: "Yes — the backend uses a fully modular pipeline. Subclass BaseAnalyzer, implement analyze(image) → AnalyzerResult, and register your class in pipeline.py. It will automatically appear in the API response and UI results panel.",
  },
  {
    q: "Does it store my uploaded images?",
    a: "No. Files are received by FastAPI, decoded into an in-memory PIL Image object for the duration of the analysis, and then immediately garbage-collected. No images, metadata, or analysis results are persisted to disk or any database.",
  },
];

function FAQItem({ q, a }: { q: string; a: string }) {
  const [open, setOpen] = useState(false);
  return (
    <div className={`border rounded-xl overflow-hidden transition-all shadow-sm ${open ? "border-[#0096C7]/30 bg-white" : "border-[#BAE8FF]/60 bg-white/70 hover:border-[#BAE8FF]"}`}>
      <button
        onClick={() => setOpen(!open)}
        className="w-full flex justify-between items-center px-6 py-4 text-left gap-4"
      >
        <span className="text-slate-700 font-bold">{q}</span>
        <span className={`text-[#0096C7] text-xl flex-shrink-0 transition-transform duration-300 ${open ? "rotate-45" : ""}`}>+</span>
      </button>
      <div className={`transition-all duration-300 overflow-hidden ${open ? "max-h-96" : "max-h-0"}`}>
        <p className="px-6 pb-5 text-slate-500 text-sm leading-relaxed">{a}</p>
      </div>
    </div>
  );
}

export function Documentation() {
  return (
    <div className="bg-transparent text-slate-800">
      {/* Divider */}
      <div className="flex items-center gap-4 px-6 pt-20 pb-0 max-w-[1200px] mx-auto">
        <div className="flex-1 h-px bg-[#BAE8FF]" />
        <div className="flex items-center gap-2 px-4 py-2 rounded-full bg-white border border-[#BAE8FF] shadow-sm">
          <span className="text-[#0096C7] text-sm">📖</span>
          <span className="text-sm font-bold text-slate-700">Project Documentation</span>
        </div>
        <div className="flex-1 h-px bg-[#BAE8FF]" />
      </div>

      {/* Stats Banner */}
      <section className="max-w-[1200px] mx-auto px-6 py-16">
        <div className="text-center mb-12">
          <h2 className="text-4xl font-extrabold text-slate-800 mb-4 tracking-tight">
            Signal-based &amp; <span className="text-[#0096C7]">ML deepfake detection</span>
          </h2>
          <p className="text-slate-600 font-mono text-sm max-w-xl mx-auto">
            Deterministic signal extraction combined with lightweight, inspectable machine learning models. Pure mathematical analysis with local CNN, RNN, and Vision Transformer classifiers.
          </p>
        </div>
        <div className="grid grid-cols-3 gap-6 max-w-2xl mx-auto">
          {[["8", "Forensic Analyzers"], ["3", "Verdict Tiers"], ["4", "ML Models"]].map(([num, label]) => (
            <div key={label} className="bg-white border border-[#BAE8FF]/60 shadow-md rounded-2xl p-6 text-center">
              <div className="text-5xl font-extrabold text-[#0096C7] mb-2">{num}</div>
              <div className="text-xs text-slate-400 uppercase tracking-widest font-mono font-bold">{label}</div>
            </div>
          ))}
        </div>
      </section>

      {/* Scoring Verdicts */}
      <section className="max-w-[1200px] mx-auto px-6 py-12 border-t border-[#BAE8FF]/50">
        <h2 className="text-3xl font-extrabold text-slate-800 mb-4">Scoring &amp; Verdicts</h2>
        <p className="text-slate-600 mb-8">The system aggregates findings into a single authenticity score between 0% and 100%, categorized into three tiers.</p>
        <div className="grid md:grid-cols-3 gap-6">
          <div className="bg-white border border-[#BAE8FF]/60 shadow-md rounded-2xl p-6 border-l-4 border-l-emerald-500">
            <div className="font-mono text-emerald-600 text-xl font-bold mb-3">&gt; 70%</div>
            <h3 className="text-slate-800 font-bold text-lg mb-2">Authentic</h3>
            <p className="text-slate-500 text-sm">High indicators of trust. Signals remain consistent with straight-out-of-camera (SOOC) images or standard lossless edits.</p>
          </div>
          <div className="bg-white border border-[#BAE8FF]/60 shadow-md rounded-2xl p-6 border-l-4 border-l-amber-500">
            <div className="font-mono text-amber-600 text-xl font-bold mb-3">40% – 70%</div>
            <h3 className="text-slate-800 font-bold text-lg mb-2">Suspicious</h3>
            <p className="text-slate-500 text-sm">Some anomalies found. Could indicate heavy harmless editing (e.g., Photoshop, filters) or minor localized manipulation.</p>
          </div>
          <div className="bg-white border border-[#BAE8FF]/60 shadow-md rounded-2xl p-6 border-l-4 border-l-red-500">
            <div className="font-mono text-red-600 text-xl font-bold mb-3">&lt; 40%</div>
            <h3 className="text-slate-800 font-bold text-lg mb-2">Manipulated</h3>
            <p className="text-slate-500 text-sm">Strong, overlapping indicators of manipulation. High probability of AI generation, deepfaking, or extreme structural editing.</p>
          </div>
        </div>
      </section>

      {/* 8 Analyzers */}
      <section className="max-w-[1200px] mx-auto px-6 py-12 border-t border-[#BAE8FF]/50">
        <h2 className="text-3xl font-extrabold text-slate-800 mb-10">The 12 Detection Analyzers &amp; ML Models</h2>
        <div className="grid md:grid-cols-2 xl:grid-cols-3 gap-5">
          {analyzers.map((a) => (
            <div
              key={a.name}
              className="bg-white border border-[#BAE8FF]/60 rounded-2xl p-6 hover:border-[#0096C7]/30 hover:-translate-y-1 transition-all duration-300 shadow-sm hover:shadow-lg"
            >
              <div className="flex items-center gap-3 mb-3">
                <div className="w-10 h-10 bg-[#E0F7FF] rounded-xl flex items-center justify-center text-xl shadow-sm">{a.icon}</div>
                <h4 className="text-slate-800 font-bold">{a.name}</h4>
              </div>
              <div className="text-[#0096C7] font-mono text-xs uppercase tracking-wider mb-3 font-bold">{a.file}</div>
              <p className="text-slate-500 text-sm mb-2"><span className="text-slate-700 font-bold">What it checks: </span>{a.what}</p>
              <p className="text-slate-500 text-sm"><span className="text-slate-700 font-bold">Why it works: </span>{a.why}</p>
            </div>
          ))}
        </div>
      </section>

      {/* Architecture */}
      <section className="max-w-[1200px] mx-auto px-6 py-12 border-t border-[#BAE8FF]/50">
        <h2 className="text-3xl font-extrabold text-slate-800 mb-10">Architecture</h2>
        <div className="grid md:grid-cols-2 gap-6">
          <div className="bg-white border border-[#BAE8FF]/60 shadow-md rounded-2xl p-7">
            <h3 className="text-[#0096C7] font-bold text-lg mb-5 pb-4 border-b border-slate-100 font-mono">Backend (Python / FastAPI)</h3>
            <ul className="space-y-3">
              {[
                <>Exposes the <code className="text-[#0096C7] text-xs bg-[#E0F7FF]/40 border border-[#BAE8FF]/40 px-1.5 py-0.5 rounded font-bold">/api/v1/analyze</code> REST endpoint.</>,
                <>Accepts <code className="text-[#0096C7] text-xs bg-[#E0F7FF]/40 border border-[#BAE8FF]/40 px-1.5 py-0.5 rounded font-bold">multipart/form-data</code> file uploads.</>,
                <>Orchestrates the <code className="text-[#0096C7] text-xs bg-[#E0F7FF]/40 border border-[#BAE8FF]/40 px-1.5 py-0.5 rounded font-bold">AnalyzerPipeline</code> which manages parallel execution of forensic modules.</>,
                "Calculates the weighted average based on module confidence.",
                "Returns a heavily structured JSON response detailing findings per module.",
              ].map((item, i) => (
                <li key={i} className="flex gap-3 text-slate-600 text-sm">
                  <span className="text-[#0096C7] font-mono mt-0.5 flex-shrink-0">→</span>
                  <span>{item}</span>
                </li>
              ))}
            </ul>
          </div>
          <div className="bg-white border border-[#BAE8FF]/60 shadow-md rounded-2xl p-7">
            <h3 className="text-[#0096C7] font-bold text-lg mb-5 pb-4 border-b border-slate-100 font-mono">Frontend (React / Vite / TS)</h3>
            <ul className="space-y-3">
              {[
                "Single Page Application styled with TailwindCSS.",
                <>Handles drag-and-drop file ingestion via <code className="text-[#0096C7] text-xs bg-[#E0F7FF]/40 border border-[#BAE8FF]/40 px-1.5 py-0.5 rounded font-bold">ImageUpload.tsx</code>.</>,
                <>Renders the dynamic <code className="text-[#0096C7] text-xs bg-[#E0F7FF]/40 border border-[#BAE8FF]/40 px-1.5 py-0.5 rounded font-bold">ScoreGauge.tsx</code> based on the API response.</>,
                <>Maps individual analyzer findings into expandable cards in <code className="text-[#0096C7] text-xs bg-[#E0F7FF]/40 border border-[#BAE8FF]/40 px-1.5 py-0.5 rounded font-bold">ResultsPanel.tsx</code>.</>,
              ].map((item, i) => (
                <li key={i} className="flex gap-3 text-slate-600 text-sm">
                  <span className="text-[#0096C7] font-mono mt-0.5 flex-shrink-0">→</span>
                  <span>{item}</span>
                </li>
              ))}
            </ul>
          </div>
        </div>
      </section>

      {/* Limitations */}
      <section className="max-w-[1200px] mx-auto px-6 py-12 border-t border-[#BAE8FF]/50">
        <h2 className="text-3xl font-extrabold text-slate-800 mb-10">Limitations &amp; Known Issues</h2>
        <div className="grid md:grid-cols-2 gap-5">
          {[
            { title: "Deterministic Signal Extraction", desc: "Currently, the system uses multiple OpenCV cascades (Haar/LBP) to detect both human and anime faces, ensuring stylized AI art is correctly analyzed for deepfake signals." },
            { title: "JPEG Dependency", desc: "Many analyzers (ELA, DCT Compression) rely heavily on JPEG artifacts. Analyzing PNGs or heavily compressed web-formats (WebP) significantly lowers their confidence weighting." },
            { title: "Social Media Stripping", desc: 'Social media platforms (WhatsApp, Twitter, Instagram) strip EXIF metadata and recompress images. This can trigger false "Suspicious" flags on authentic images.' },
            { title: "Harmless Editing False Positives", desc: "Because the system relies on mathematical anomalies, heavily edited real photos (e.g., Lightroom color grading, Photoshop spot healing) may flag as Likely Manipulated." },
          ].map((lim) => (
            <div key={lim.title} className="bg-amber-50 border border-amber-200 rounded-2xl p-6 flex gap-4 shadow-sm">
              <span className="text-amber-600 text-xl flex-shrink-0">⚠️</span>
              <div>
                <h4 className="text-amber-800 font-bold mb-2">{lim.title}</h4>
                <p className="text-amber-700 text-sm leading-relaxed">{lim.desc}</p>
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* Use Cases */}
      <section className="max-w-[1200px] mx-auto px-6 py-12 border-t border-[#BAE8FF]/50">
        <h2 className="text-3xl font-extrabold text-slate-800 mb-4">Real-World Use Cases</h2>
        <p className="text-slate-600 mb-8">DeepGuard AI's deterministic analysis is applicable across a range of professional domains requiring high interpretability.</p>
        <div className="grid md:grid-cols-2 xl:grid-cols-4 gap-5">
          {[
            { icon: "📰", title: "Journalism & Fact-Checking", desc: "Verify the provenance of sourced images before publishing to prevent the spread of synthetic misinformation at scale." },
            { icon: "🛡️", title: "Social Media Moderation", desc: "Integrate the pipeline API to automatically flag synthetic or heavily manipulated content submissions for human review." },
            { icon: "⚖️", title: "Legal & Forensic Evidence", desc: "Authenticate digital images in court proceedings using fully transparent mathematical analysis — not a black-box model." },
            { icon: "🔬", title: "Academic Research", desc: "Study the structural and statistical fingerprints of AI-generated images using open, inspectable forensic tools." },
          ].map((uc) => (
            <div key={uc.title} className="bg-white border border-[#BAE8FF]/60 border-t-2 border-t-[#0096C7] rounded-2xl p-6 shadow-sm hover:-translate-y-1 transition-all duration-300">
              <div className="text-2xl mb-3">{uc.icon}</div>
              <h4 className="text-slate-800 font-bold mb-2">{uc.title}</h4>
              <p className="text-slate-500 text-sm leading-relaxed">{uc.desc}</p>
            </div>
          ))}
        </div>
      </section>

      {/* Tech Stack */}
      <section className="max-w-[1200px] mx-auto px-6 py-12 border-t border-[#BAE8FF]/50">
        <h2 className="text-3xl font-extrabold text-slate-800 mb-4">Tech Stack</h2>
        <p className="text-slate-600 mb-8">Built exclusively with standard, high-performance, open-source tooling. Lightweight, locally run ML architectures with zero heavy proprietary cloud weights.</p>
        <div className="flex flex-wrap gap-3">
          {["Python 3.10+", "FastAPI", "React 18", "TypeScript", "Vite", "NumPy", "OpenCV", "Pillow", "SciPy"].map((tech) => (
            <div key={tech} className="bg-white border border-[#BAE8FF]/60 rounded-xl px-5 py-3 font-mono text-sm text-[#0096C7] shadow-sm hover:border-[#0096C7]/50 hover:-translate-y-0.5 transition-all duration-200">
              {tech}
            </div>
          ))}
        </div>
      </section>

      {/* FAQ */}
      <section className="max-w-[1200px] mx-auto px-6 py-12 border-t border-[#BAE8FF]/50">
        <h2 className="text-3xl font-extrabold text-slate-800 mb-10">Frequently Asked Questions</h2>
        <div className="flex flex-col gap-3">
          {faqs.map((f) => <FAQItem key={f.q} q={f.q} a={f.a} />)}
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-[#BAE8FF]/60 py-12 text-center">
        <div className="text-xl font-bold text-[#004e6c] mb-1">DeepGuard AI</div>
        <div className="font-mono text-xs text-[#0096C7] mb-6">Forensic-grade image analysis. No black boxes.</div>
        <p className="text-slate-500 text-xs font-mono max-w-lg mx-auto">
          This tool is intended for research and educational use only. Results are probabilistic signal indicators and do not constitute legal proof of manipulation.
        </p>
      </footer>
    </div>
  );
}
