import { useState, type FormEvent } from "react";
import { useNavigate } from "react-router-dom";
import { Shield, ShieldCheck, Mail, Lock, Cpu } from "lucide-react";

export default function Login() {
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState("");

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setError("");
    setIsLoading(true);

    if (!email || !password) {
      setError("Please fill in all fields");
      setIsLoading(false);
      return;
    }

    setTimeout(() => {
      setIsLoading(false);
      // Simulate a successful login and redirect to the detector
      navigate("/");
    }, 1000);
  };

  return (
    <div className="min-h-screen flex flex-col items-center justify-center p-4 bg-gradient-to-tr from-[#E0F7FF] to-[#BAE8FF] font-sans">
      <div className="w-full max-w-[400px] relative">
        
        {/* Header */}
        <div className="flex flex-col items-center mb-8">
          <div className="flex items-center gap-2 mb-6">
            <div className="w-9 h-9 bg-[#0096C7] rounded-xl flex items-center justify-center shadow-md">
              <Shield className="w-5 h-5 text-white" />
            </div>
            <span className="text-xl font-bold text-[#004e6c] tracking-tight">DeepGuard AI</span>
          </div>
          
          <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-[#E0F7FF] text-[#0096C7] text-xs font-semibold mb-6 border border-[#0096C7]/20 shadow-sm">
            <span className="text-sm leading-none">⚡</span>
            <span>FORENSIC SIGNAL ANALYSIS</span>
          </div>
          
          <h1 className="text-3xl font-extrabold text-slate-800 mb-2">Welcome back</h1>
          <p className="text-slate-500 text-sm">Sign in to your DeepGuard account</p>
        </div>

        {/* Card */}
        <div className="rounded-2xl p-8 shadow-xl border border-[#BAE8FF]/60 bg-white">
          <form onSubmit={handleSubmit} className="space-y-5">
            {error && (
              <div className="text-red-600 text-sm text-center bg-red-50 py-2 rounded-lg border border-red-200">
                {error}
              </div>
            )}

            <div className="space-y-4">
              <div className="relative flex items-center">
                <Mail className="absolute left-3.5 w-5 h-5 text-[#0096C7]" />
                <input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="Email address"
                  className="w-full pl-11 pr-4 py-3 bg-[#2b303c] border border-gray-700/80 rounded-xl text-white placeholder-gray-400 focus:outline-none focus:ring-1 focus:ring-[#0096C7] focus:border-[#0096C7] transition-all"
                />
              </div>

              <div className="relative flex items-center">
                <Lock className="absolute left-3.5 w-5 h-5 text-[#0096C7]" />
                <input
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="Password"
                  className="w-full pl-11 pr-4 py-3 bg-[#2b303c] border border-gray-700/80 rounded-xl text-white placeholder-gray-400 focus:outline-none focus:ring-1 focus:ring-[#0096C7] focus:border-[#0096C7] transition-all"
                />
              </div>
            </div>

            <div className="flex items-center justify-between pt-1">
              <label className="flex items-center gap-2 cursor-pointer group">
                <input 
                  type="checkbox" 
                  className="w-4 h-4 rounded border-slate-300 bg-white focus:ring-[#0096C7] text-[#0096C7] accent-[#0096C7]" 
                />
                <span className="text-sm text-slate-600 group-hover:text-slate-800 transition-colors">Remember me</span>
              </label>
              <button type="button" className="text-sm font-semibold hover:underline transition-all text-[#0096C7]">
                Forgot password?
              </button>
            </div>

            <button
              type="submit"
              disabled={isLoading}
              className="w-full flex items-center justify-center gap-2 py-3 px-4 text-white font-semibold rounded-xl transition-all hover:bg-[#007ea7] disabled:opacity-50 mt-2 bg-[#0096C7] shadow-[0_4px_12px_rgba(0,150,199,0.25)]"
            >
              {isLoading ? (
                <span className="flex items-center justify-center gap-2">
                  <svg className="animate-spin w-5 h-5 text-white" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                  </svg>
                  Signing in...
                </span>
              ) : (
                <>
                  <ShieldCheck className="w-5 h-5" />
                  Sign in to DeepGuard
                </>
              )}
            </button>
          </form>

          <div className="mt-7 relative flex items-center justify-center">
            <div className="absolute inset-0 flex items-center">
              <div className="w-full border-t border-slate-200"></div>
            </div>
            <div className="relative flex justify-center text-xs">
              <span className="px-3 text-slate-400 bg-white">or continue with</span>
            </div>
          </div>

          <div className="mt-6">
            <button className="w-full flex items-center justify-center gap-3 py-2.5 px-4 bg-white border border-slate-200 hover:bg-slate-50 hover:border-slate-300 text-slate-700 font-semibold rounded-xl transition-all shadow-sm">
              <svg className="w-5 h-5" viewBox="0 0 24 24">
                <path d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" fill="#4285F4" />
                <path d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" fill="#34A853" />
                <path d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z" fill="#FBBC05" />
                <path d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" fill="#EA4335" />
                <path d="M1 1h22v22H1z" fill="none" />
              </svg>
              Google
            </button>
          </div>
        </div>

        {/* Footer */}
        <div className="mt-8 text-center">
          <p className="text-slate-500 text-sm">
            Don't have an account?{" "}
            <button className="font-semibold hover:underline transition-all text-[#0096C7]">
              Request access
            </button>
          </p>
        </div>

        {/* Bottom Tag */}
        <div className="mt-12 flex justify-center pb-8">
          <div className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-white/60 border border-[#BAE8FF] text-slate-500 text-xs font-semibold shadow-sm">
            <Cpu className="w-3.5 h-3.5 text-[#0096C7]" />
            <span>Forensic-Signal-V2</span>
          </div>
        </div>
        
      </div>
    </div>
  );
}