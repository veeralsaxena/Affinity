"use client";

import { useState, useEffect } from "react";
import { Heart, Eye, EyeOff, ArrowRight } from "lucide-react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useAuth } from "@/context/AuthContext";

export default function LoginPage() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPass, setShowPass] = useState(false);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const { login, isAuthenticated, isLoading } = useAuth();
  const router = useRouter();

  // Redirect if already authenticated
  useEffect(() => {
    if (!isLoading && isAuthenticated) router.push("/dashboard");
  }, [isAuthenticated, isLoading, router]);

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError("");
    try {
      await login(email, password);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  if (isLoading) return <div className="min-h-screen bg-gradient-to-br from-[#fff5f5] via-[#fff0f3] to-[#ffeef2] flex items-center justify-center"><div className="loader" /></div>;

  return (
    <div className="min-h-screen bg-gradient-to-br from-[#fff5f5] via-[#fff0f3] to-[#ffeef2] flex items-center justify-center px-4 relative overflow-hidden">
      {/* Blobs */}
      <div className="absolute top-[-80px] right-[-80px] w-[300px] h-[300px] rounded-full bg-rose-200/40 blur-[60px]" />
      <div className="absolute bottom-[-60px] left-[-60px] w-[250px] h-[250px] rounded-full bg-pink-200/30 blur-[50px]" />

      {/* Floating hearts */}
      <div className="fixed inset-0 pointer-events-none overflow-hidden z-0">
        {Array.from({ length: 8 }).map((_, i) => {
          const size = 12 + Math.random() * 20;
          const left = Math.random() * 100;
          const delay = Math.random() * 15;
          const duration = 14 + Math.random() * 16;
          return (
            <div key={i} className="absolute" style={{
              left: `${left}%`, bottom: `-${size}px`,
              animation: `floatUp ${duration}s ease-in ${delay}s infinite`,
              opacity: 0.06 + Math.random() * 0.08,
            }}>
              <svg width={size} height={size} viewBox="0 0 24 24" fill="currentColor" className="text-rose-300">
                <path d="M12 21.35l-1.45-1.32C5.4 15.36 2 12.28 2 8.5 2 5.42 4.42 3 7.5 3c1.74 0 3.41.81 4.5 2.09C13.09 3.81 14.76 3 16.5 3 19.58 3 22 5.42 22 8.5c0 3.78-3.4 6.86-8.55 11.54L12 21.35z" />
              </svg>
            </div>
          );
        })}
      </div>

      <div className="w-full max-w-md space-y-8 relative z-10">
        {/* Logo */}
        <div className="text-center">
          <Link href="/" className="inline-flex items-center gap-3">
            <div className="w-12 h-12 rounded-2xl bg-gradient-to-br from-rose-400 via-pink-400 to-red-400 flex items-center justify-center shadow-lg shadow-rose-300/40">
              <Heart className="w-6 h-6 text-white fill-white" />
            </div>
            <span className="text-2xl font-extrabold text-rose-800">
              Rel<span className="text-transparent bg-clip-text bg-gradient-to-r from-rose-500 to-pink-500">AI</span>tion
            </span>
          </Link>
        </div>

        {/* Card */}
        <div className="bg-white/70 backdrop-blur-xl border border-rose-100 rounded-2xl p-8 shadow-xl shadow-rose-100/30">
          <h2 className="text-2xl font-extrabold text-rose-900 mb-1">Welcome back 💕</h2>
          <p className="text-sm text-rose-400/50 mb-6">Log in to your relationship intelligence dashboard</p>

          {error && (
            <div className="bg-rose-50 border border-rose-200 text-rose-600 text-sm px-4 py-3 rounded-xl mb-4">
              {error}
            </div>
          )}

          <form onSubmit={handleLogin} className="space-y-5">
            <div>
              <label className="text-xs font-bold text-rose-500/60 uppercase tracking-wider mb-2 block">Email</label>
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="you@example.com"
                className="w-full px-4 py-3 rounded-xl bg-rose-50/50 border border-rose-100 text-rose-900 placeholder-rose-300 text-sm focus:outline-none focus:border-rose-400 focus:ring-2 focus:ring-rose-200 transition-all"
                required
              />
            </div>

            <div>
              <label className="text-xs font-bold text-rose-500/60 uppercase tracking-wider mb-2 block">Password</label>
              <div className="relative">
                <input
                  type={showPass ? "text" : "password"}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="••••••••"
                  className="w-full px-4 py-3 rounded-xl bg-rose-50/50 border border-rose-100 text-rose-900 placeholder-rose-300 text-sm focus:outline-none focus:border-rose-400 focus:ring-2 focus:ring-rose-200 transition-all pr-12"
                  required
                />
                <button type="button" onClick={() => setShowPass(!showPass)}
                  className="absolute right-4 top-1/2 -translate-y-1/2 text-rose-300 hover:text-rose-500 transition-colors">
                  {showPass ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                </button>
              </div>
            </div>

            <button type="submit" disabled={loading}
              className="w-full py-3.5 rounded-xl bg-gradient-to-r from-rose-500 via-pink-500 to-red-400 text-white font-bold text-sm shadow-lg shadow-rose-300/40 hover:shadow-rose-400/60 hover:scale-[1.02] transition-all flex items-center justify-center gap-2 disabled:opacity-60">
              {loading ? "Logging in..." : "Log In"}
              {!loading && <ArrowRight className="w-4 h-4" />}
            </button>
          </form>

          <p className="text-center text-sm text-rose-400/40 mt-5">
            Don&apos;t have an account?{" "}
            <Link href="/signup" className="text-rose-500 font-semibold hover:text-rose-600 transition-colors">
              Sign up
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
}
