import { Shield, GitPullRequest, Activity, BookOpen } from "lucide-react";
import { Link } from "react-router-dom";

export function Header() {
  return (
    <header className="bg-white/80 backdrop-blur-md border-b border-[#BAE8FF]/60 sticky top-0 z-10">
      <div className="max-w-[1400px] mx-auto px-6 py-4 flex items-center justify-between">
        {/* Brand */}
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 bg-[#0096C7] rounded-xl flex items-center justify-center">
            <Shield className="w-5 h-5 text-white" />
          </div>
          <h1 className="text-xl font-bold text-[#004e6c] tracking-tight">
            DeepGuard <span className="text-slate-500 font-normal">AI</span>
          </h1>
        </div>

        {/* Right Nav */}
        <div className="flex items-center gap-6">
          <div className="hidden sm:flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-slate-100 border border-slate-200 text-slate-600 text-xs font-semibold">
            <Activity className="w-3.5 h-3.5 text-emerald-600" />
            <span>EfficientNet-B4</span>
          </div>
          <a
            href="/docs/index.html"
            target="_blank"
            rel="noopener noreferrer"
            className="hidden sm:flex items-center gap-1.5 text-sm text-slate-600 hover:text-[#0096C7] transition-colors font-semibold"
          >
            <BookOpen className="w-4 h-4 text-[#0096C7]" />
            Docs
          </a>
          <Link to="/login" className="text-sm text-slate-600 hover:text-[#0096C7] transition-colors font-semibold">
            Sign Out
          </Link>
          <a href="#" className="text-slate-400 hover:text-[#0096C7] transition-colors">
            <GitPullRequest className="w-5 h-5" />
          </a>
        </div>
      </div>
    </header>
  );
}
