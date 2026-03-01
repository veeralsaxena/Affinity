"use client";

import { useEffect, useRef } from "react";
import { Heart, ArrowRight, BrainCircuit, BarChart3, MessageCircle, Shield, Zap, Globe, ChevronDown, Sparkles, Users, Star, LogOut } from "lucide-react";
import { GooeyText } from "@/components/ui/gooey-text-morphing";
import Link from "next/link";
import { useAuth } from "@/context/AuthContext";

/* ─── Floating Hearts Animation ──────────────────────────────────── */

function FloatingHearts() {
  return (
    <div className="fixed inset-0 pointer-events-none overflow-hidden z-0">
      {Array.from({ length: 18 }).map((_, i) => {
        const size = 12 + Math.random() * 24;
        const left = Math.random() * 100;
        const delay = Math.random() * 15;
        const duration = 12 + Math.random() * 18;
        const opacity = 0.08 + Math.random() * 0.15;
        return (
          <div key={i} className="absolute" style={{
            left: `${left}%`,
            bottom: `-${size}px`,
            animation: `floatUp ${duration}s ease-in ${delay}s infinite`,
            opacity,
          }}>
            <svg width={size} height={size} viewBox="0 0 24 24" fill="currentColor" className="text-rose-400">
              <path d="M12 21.35l-1.45-1.32C5.4 15.36 2 12.28 2 8.5 2 5.42 4.42 3 7.5 3c1.74 0 3.41.81 4.5 2.09C13.09 3.81 14.76 3 16.5 3 19.58 3 22 5.42 22 8.5c0 3.78-3.4 6.86-8.55 11.54L12 21.35z" />
            </svg>
          </div>
        );
      })}
    </div>
  );
}

/* ─── Parallax Section Wrapper ───────────────────────────────────── */

function ParallaxSection({ children, className = "", speed = 0.3 }: { children: React.ReactNode; className?: string; speed?: number }) {
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handleScroll = () => {
      if (!ref.current) return;
      const rect = ref.current.getBoundingClientRect();
      const scrolled = window.innerHeight - rect.top;
      if (scrolled > 0) {
        ref.current.style.transform = `translateY(${scrolled * speed * -0.1}px)`;
      }
    };
    window.addEventListener("scroll", handleScroll, { passive: true });
    return () => window.removeEventListener("scroll", handleScroll);
  }, [speed]);

  return <div ref={ref} className={className}>{children}</div>;
}

/* ─── Animated Counter ───────────────────────────────────────────── */

function AnimatedStat({ value, label, suffix = "" }: { value: string; label: string; suffix?: string }) {
  return (
    <div className="text-center group">
      <div className="text-4xl md:text-5xl font-black text-rose-600 group-hover:scale-110 transition-transform duration-500">{value}<span className="text-rose-400 text-2xl">{suffix}</span></div>
      <p className="text-sm text-rose-900/40 mt-1 font-medium">{label}</p>
    </div>
  );
}

/* ─── Session-Aware Navbar ────────────────────────────────────────── */

function NavBar() {
  const { user, isAuthenticated, logout, isLoading } = useAuth();
  const initials = user?.full_name
    ? user.full_name.split(" ").map(w => w[0]).join("").toUpperCase().slice(0, 2)
    : user?.username?.slice(0, 2).toUpperCase() || "U";

  return (
    <nav className="sticky top-0 z-50 backdrop-blur-xl bg-white/70 border-b border-rose-100/80">
      <div className="max-w-7xl mx-auto flex items-center justify-between px-6 md:px-10 py-3.5">
        <div className="flex items-center gap-2.5">
          <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-rose-400 via-pink-400 to-red-400 flex items-center justify-center shadow-md shadow-rose-300/40">
            <Heart className="w-4.5 h-4.5 text-white fill-white" />
          </div>
          <span className="text-lg font-extrabold text-rose-800">
            Rel<span className="text-transparent bg-clip-text bg-gradient-to-r from-rose-500 to-pink-500">AI</span>tion
          </span>
        </div>

        <div className="hidden md:flex items-center gap-1">
          {["Features", "How It Works", "Tech"].map((item) => (
            <a key={item} href={`#${item.toLowerCase().replace(/ /g, "-")}`}
              className="px-4 py-2 rounded-full text-sm font-medium text-rose-700/60 hover:text-rose-700 hover:bg-rose-50 transition-all">
              {item}
            </a>
          ))}
          <Link href="/dashboard" className="px-4 py-2 rounded-full text-sm font-medium text-rose-700/60 hover:text-rose-700 hover:bg-rose-50 transition-all">
            Dashboard
          </Link>
        </div>

        <div className="flex items-center gap-2.5">
          {isLoading ? (
            <div className="w-8 h-8 rounded-full bg-rose-100 animate-pulse" />
          ) : isAuthenticated ? (
            <>
              <Link href="/dashboard"
                className="flex items-center gap-2 px-4 py-2 rounded-full text-sm font-semibold text-rose-600 hover:bg-rose-50 transition-all">
                <div className="w-8 h-8 rounded-full bg-gradient-to-br from-rose-400 to-pink-400 flex items-center justify-center text-white text-xs font-bold">
                  {initials}
                </div>
                <span className="hidden sm:inline">{user?.full_name || user?.username}</span>
              </Link>
              <button onClick={logout}
                className="text-sm font-medium text-rose-400 hover:text-rose-600 px-3 py-2 transition-colors flex items-center gap-1.5">
                <LogOut className="w-3.5 h-3.5" />
                <span className="hidden sm:inline">Log out</span>
              </button>
            </>
          ) : (
            <>
              <Link href="/login">
                <button className="text-sm font-semibold text-rose-600 hover:text-rose-800 px-4 py-2 transition-colors">Log in</button>
              </Link>
              <Link href="/signup">
                <button className="text-sm font-bold px-5 py-2.5 rounded-full bg-gradient-to-r from-rose-500 to-pink-500 text-white shadow-lg shadow-rose-300/40 hover:shadow-rose-400/60 hover:scale-105 transition-all">
                  Get Started 💕
                </button>
              </Link>
            </>
          )}
        </div>
      </div>
    </nav>
  );
}

/* ════════════════════════════════════════════════════════════════════
   MAIN LANDING PAGE
   ════════════════════════════════════════════════════════════════════ */

export default function LandingPage() {
  return (
    <div className="relative min-h-screen bg-gradient-to-b from-[#fff5f5] via-[#fff0f3] to-[#ffeef2] text-rose-950 overflow-hidden font-sans">

      <FloatingHearts />

      {/* ── Decorative blobs ── */}
      <div className="absolute top-[-100px] right-[-100px] w-[400px] h-[400px] rounded-full bg-rose-200/40 blur-[80px] pointer-events-none" />
      <div className="absolute top-[40%] left-[-150px] w-[350px] h-[350px] rounded-full bg-pink-200/30 blur-[60px] pointer-events-none" />
      <div className="absolute bottom-[-80px] right-[20%] w-[300px] h-[300px] rounded-full bg-amber-100/40 blur-[70px] pointer-events-none" />

      {/* ════════ NAVBAR ════════ */}
      <NavBar />

      {/* ════════ HERO ════════ */}
      <section className="relative max-w-6xl mx-auto px-6 md:px-10 pt-20 md:pt-28 pb-16 text-center">
        <ParallaxSection speed={0.5}>
          {/* Badge */}
          <div className="inline-flex items-center gap-2 bg-white/60 border border-rose-200 rounded-full px-4 py-1.5 mb-8 shadow-sm backdrop-blur-sm animate-fadeDown">
            <span className="w-2 h-2 rounded-full bg-rose-400 animate-pulse" />
            <span className="text-[11px] text-rose-600 font-bold uppercase tracking-wider">Paradigm 1.0 Hackathon</span>
            <Heart className="w-3 h-3 text-rose-400 fill-rose-400" />
          </div>

          {/* Main Heading with Morphic Text */}
          <div className="mb-6 animate-fadeUp">
            <div className="min-h-[70px] md:min-h-[90px] w-full flex justify-center items-center overflow-visible">
              <GooeyText
                texts={["Your Relationships", "Your Friendships", "Your Connections"]}
                morphTime={1.4}
                cooldownTime={1.5}
                textClassName="text-rose-900 text-5xl md:text-7xl font-extrabold text-center"
              />
            </div>
            <h1 className="text-5xl md:text-7xl font-extrabold leading-[1.1]">
              <span className="text-transparent bg-clip-text bg-gradient-to-r from-rose-500 via-pink-500 to-red-400">Deserve AI That Cares</span>
              <span className="inline-block ml-2 animate-heartbeat">💗</span>
            </h1>
          </div>

          <p className="text-lg md:text-xl text-rose-800/50 max-w-2xl mx-auto leading-relaxed mb-10 animate-fadeUp" style={{ animationDelay: "0.2s" }}>
            Upload your WhatsApp or Instagram chats. Our AI detects when bonds are 
            <span className="text-rose-500 font-semibold"> drifting apart</span>, spots 
            <span className="text-pink-500 font-semibold"> unresolved tension</span>, and crafts the 
            <span className="text-red-400 font-semibold"> perfect message</span> to bring you closer.
          </p>

          {/* CTAs */}
          <div className="flex items-center justify-center gap-4 mb-16 animate-fadeUp" style={{ animationDelay: "0.4s" }}>
            <Link href="/signup">
              <button className="group flex items-center gap-2 text-base font-bold px-8 py-4 rounded-full bg-gradient-to-r from-rose-500 via-pink-500 to-red-400 text-white shadow-xl shadow-rose-300/50 hover:shadow-rose-400/70 hover:scale-105 transition-all">
                Start Analyzing
                <ArrowRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
              </button>
            </Link>
            <a href="#how-it-works">
              <button className="flex items-center gap-2 text-sm font-semibold px-6 py-4 rounded-full border-2 border-rose-200 text-rose-600 hover:bg-rose-50 hover:border-rose-300 transition-all">
                See How It Works
                <ChevronDown className="w-4 h-4 animate-bounce" />
              </button>
            </a>
          </div>
        </ParallaxSection>

        {/* ── Dashboard Preview Card ── */}
        <div className="relative group animate-fadeUp" style={{ animationDelay: "0.6s" }}>
          <div className="absolute -inset-3 bg-gradient-to-r from-rose-300/30 via-pink-300/30 to-red-300/30 rounded-[2rem] blur-2xl group-hover:blur-3xl transition-all opacity-60" />
          <div className="relative bg-white/80 backdrop-blur-xl border border-rose-100 rounded-2xl p-6 shadow-2xl shadow-rose-200/30 overflow-hidden">
            {/* Mini dashboard preview */}
            <div className="grid grid-cols-4 gap-3">
              {[
                { label: "Health Score", value: "76", color: "text-emerald-500", bg: "bg-emerald-50", emoji: "💚" },
                { label: "At Risk", value: "3", color: "text-rose-500", bg: "bg-rose-50", emoji: "💔" },
                { label: "Strong Bonds", value: "5", color: "text-pink-500", bg: "bg-pink-50", emoji: "💕" },
                { label: "Follow-ups", value: "2", color: "text-amber-500", bg: "bg-amber-50", emoji: "💌" },
              ].map((m, i) => (
                <div key={i} className={`${m.bg} border border-rose-100/50 rounded-xl p-4 text-center group/card hover:scale-105 transition-transform`}>
                  <p className="text-[10px] text-rose-400 uppercase tracking-widest font-bold mb-1">{m.label}</p>
                  <div className="flex items-center justify-center gap-1.5">
                    <span className={`text-3xl font-black ${m.color}`}>{m.value}</span>
                    <span className="text-lg">{m.emoji}</span>
                  </div>
                </div>
              ))}
            </div>
            {/* Progress bar */}
            <div className="mt-4 h-2 rounded-full bg-rose-100 overflow-hidden">
              <div className="h-full rounded-full bg-gradient-to-r from-rose-400 via-pink-400 to-red-400 animate-progressBar" style={{ width: "76%" }} />
            </div>
            <p className="text-[11px] text-rose-400 mt-2 text-center font-medium">Overall Relationship Health: 76/100 — Good 💗</p>
          </div>
        </div>
      </section>

      {/* ════════ STATS ════════ */}
      <section className="max-w-4xl mx-auto px-6 py-14">
        <ParallaxSection speed={0.2} className="grid grid-cols-3 gap-8">
          <AnimatedStat value="3" suffix="L" label="Scoring Layers" />
          <AnimatedStat value="4" label="AI Agents" />
          <AnimatedStat value="100" suffix="%" label="Deterministic" />
        </ParallaxSection>
      </section>

      {/* ════════ FEATURES ════════ */}
      <section id="features" className="max-w-6xl mx-auto px-6 md:px-10 py-20">
        <ParallaxSection speed={0.3}>
          <div className="text-center mb-14">
            <span className="inline-block text-xs font-bold uppercase tracking-[0.3em] text-rose-400 mb-3 bg-rose-50 px-4 py-1.5 rounded-full border border-rose-100">Features ✨</span>
            <h2 className="text-3xl md:text-5xl font-extrabold text-rose-900">
              Not a chatbot.<br/><span className="text-transparent bg-clip-text bg-gradient-to-r from-rose-500 to-pink-500">A love language engine.</span>
            </h2>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
            {[
              { icon: BrainCircuit, title: "Multi-Agent AI", desc: "4 specialized agents on a LangGraph state machine — not a chatbot, a deterministic pipeline.", color: "from-rose-400 to-pink-500", bg: "bg-rose-50", emoji: "🧠" },
              { icon: BarChart3, title: "Hybrid Scoring", desc: "VADER + Frequency Analysis + LLM structured output. 3 layers for reproducible, explainable scores.", color: "from-amber-400 to-orange-400", bg: "bg-amber-50", emoji: "📊" },
              { icon: MessageCircle, title: "Multi-Source Ingestion", desc: "WhatsApp exports, Instagram DMs, call recordings — upload or connect live via QR.", color: "from-emerald-400 to-teal-400", bg: "bg-emerald-50", emoji: "💬" },
              { icon: Shield, title: "Ghost Writer", desc: "AI-drafted nudge messages to de-escalate conflict or re-engage dormant bonds.", color: "from-indigo-400 to-blue-400", bg: "bg-indigo-50", emoji: "✍️" },
              { icon: Zap, title: "Real-Time Bridge", desc: "whatsapp-web.js streams live messages to the scoring pipeline — no manual exports.", color: "from-pink-400 to-rose-400", bg: "bg-pink-50", emoji: "⚡" },
              { icon: Globe, title: "Social Map", desc: "See your entire relationship network. Color-coded nodes show who's thriving and who's fading.", color: "from-cyan-400 to-blue-400", bg: "bg-cyan-50", emoji: "🗺️" },
            ].map((f, i) => (
              <div key={i}
                className={`group relative ${f.bg} border border-rose-100/60 rounded-2xl p-6 hover:shadow-xl hover:shadow-rose-200/30 hover:-translate-y-1 transition-all duration-300 cursor-default overflow-hidden`}>
                {/* Hover glow */}
                <div className="absolute inset-0 bg-gradient-to-br from-white/0 to-white/50 opacity-0 group-hover:opacity-100 transition-opacity rounded-2xl" />
                <div className="relative">
                  <div className="flex items-center gap-3 mb-3">
                    <div className={`w-10 h-10 rounded-xl bg-gradient-to-br ${f.color} flex items-center justify-center shadow-md`}>
                      <f.icon className="w-5 h-5 text-white" />
                    </div>
                    <span className="text-xl">{f.emoji}</span>
                  </div>
                  <h3 className="text-[15px] font-bold text-rose-900 mb-1.5">{f.title}</h3>
                  <p className="text-[13px] text-rose-800/40 leading-relaxed">{f.desc}</p>
                </div>
              </div>
            ))}
          </div>
        </ParallaxSection>
      </section>

      {/* ════════ HOW IT WORKS ════════ */}
      <section id="how-it-works" className="relative py-20 overflow-hidden">
        {/* Wave separator */}
        <div className="absolute top-0 left-0 right-0 h-20 bg-gradient-to-b from-transparent to-white/40" />

        <div className="max-w-4xl mx-auto px-6 md:px-10 relative">
          <ParallaxSection speed={0.2}>
            <div className="text-center mb-14">
              <span className="inline-block text-xs font-bold uppercase tracking-[0.3em] text-pink-400 mb-3 bg-pink-50 px-4 py-1.5 rounded-full border border-pink-100">How It Works 💡</span>
              <h2 className="text-3xl md:text-5xl font-extrabold text-rose-900">The Pipeline of Love</h2>
            </div>

            <div className="relative">
              {/* Vertical line — behind icon column */}
              <div className="absolute left-8 top-4 bottom-4 w-px bg-gradient-to-b from-rose-200 via-pink-300 to-red-200 hidden md:block z-0" />

              <div className="space-y-6">
                {[
                  { step: "01", title: "Upload Your Chats", desc: "Drop your WhatsApp .txt, Instagram .json, or audio files. Or scan a QR code for live WhatsApp streaming.", emoji: "📱", color: "bg-rose-100 text-rose-600 border-rose-200" },
                  { step: "02", title: "AI Scores Every Thread", desc: "VADER catches negativity. Frequency analysis spots one-word replies. Gemini gives structured emotional judgment.", emoji: "🔬", color: "bg-pink-100 text-pink-600 border-pink-200" },
                  { step: "03", title: "Smart Routing", desc: "Python logic (not LLM) routes: Heat ≥ 6 → Conflict Resolver. Decay ≥ 6 → Re-Engager. Both low → Memory Logger.", emoji: "🛤️", color: "bg-orange-100 text-orange-600 border-orange-200" },
                  { step: "04", title: "Ghost Writer Drafts", desc: "The AI crafts 3 warm, casual messages you can send to de-escalate or reconnect. Personalized to your tone.", emoji: "✍️", color: "bg-amber-100 text-amber-600 border-amber-200" },
                  { step: "05", title: "Dashboard Shows Everything", desc: "Scores, sparklines, priority list, social map, and AI insights — all in one beautiful view.", emoji: "📊", color: "bg-emerald-100 text-emerald-600 border-emerald-200" },
                ].map((s, i) => (
                  <div key={i} className="flex gap-5 items-start group">
                    <div className={`relative z-10 w-16 h-16 rounded-2xl ${s.color} border flex-shrink-0 flex flex-col items-center justify-center shadow-sm group-hover:scale-110 transition-transform bg-white`}>
                      <span className="text-xl">{s.emoji}</span>
                      <span className="text-[9px] font-black mt-0.5">{s.step}</span>
                    </div>
                    <div className="bg-white/70 backdrop-blur-sm border border-rose-100/60 rounded-2xl p-5 flex-1 group-hover:shadow-lg group-hover:shadow-rose-100/40 transition-all">
                      <h3 className="text-base font-bold text-rose-900 mb-1">{s.title}</h3>
                      <p className="text-sm text-rose-700/40 leading-relaxed">{s.desc}</p>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </ParallaxSection>
        </div>
      </section>

      {/* ════════ TECH STACK ════════ */}
      <section id="tech" className="max-w-4xl mx-auto px-6 py-20">
        <ParallaxSection speed={0.15}>
          <div className="text-center mb-10">
            <span className="inline-block text-xs font-bold uppercase tracking-[0.3em] text-red-400 mb-3 bg-red-50 px-4 py-1.5 rounded-full border border-red-100">Built With 🛠️</span>
            <h2 className="text-3xl md:text-4xl font-extrabold text-rose-900">The Tech Behind the Love</h2>
          </div>
          <div className="flex flex-wrap justify-center gap-3">
            {[
              { label: "LangGraph", emoji: "🧠" },
              { label: "VADER NLP", emoji: "📈" },
              { label: "GPT-4o", emoji: "🤖" },
              { label: "FastAPI", emoji: "⚡" },
              { label: "PostgreSQL", emoji: "🗄️" },
              { label: "Next.js", emoji: "▲" },
              { label: "Tailwind CSS", emoji: "🎨" },
              { label: "whatsapp-web.js", emoji: "💬" },
              { label: "Whisper", emoji: "🎙️" },
              { label: "Docker", emoji: "🐳" },
              { label: "JWT Auth", emoji: "🔐" },
              { label: "SQLAlchemy", emoji: "📦" },
            ].map((t, i) => (
              <div key={i} className="flex items-center gap-2 bg-white/70 backdrop-blur-sm border border-rose-100 px-4 py-2.5 rounded-full text-sm text-rose-700 font-medium hover:bg-rose-50 hover:scale-105 transition-all cursor-default shadow-sm">
                <span>{t.emoji}</span>
                {t.label}
              </div>
            ))}
          </div>
        </ParallaxSection>
      </section>

      {/* ════════ CTA ════════ */}
      <section className="max-w-3xl mx-auto px-6 py-20 text-center">
        <ParallaxSection speed={0.2}>
          <div className="bg-gradient-to-br from-rose-50 to-pink-50 border border-rose-100 rounded-3xl p-12 relative overflow-hidden shadow-xl shadow-rose-100/40">
            <div className="absolute top-4 right-6 text-4xl opacity-20 animate-heartbeat">💗</div>
            <div className="absolute bottom-4 left-6 text-3xl opacity-15 animate-float">💕</div>
            
            <h2 className="text-3xl md:text-4xl font-extrabold text-rose-900 mb-4">
              Stop losing the people<br/>who matter most.
            </h2>
            <p className="text-base text-rose-600/50 mb-8">Upload a chat. See what your AI agents find. It takes 30 seconds.</p>
            <Link href="/signup">
              <button className="group inline-flex items-center gap-2 text-base font-bold px-10 py-4 rounded-full bg-gradient-to-r from-rose-500 via-pink-500 to-red-400 text-white shadow-xl shadow-rose-300/50 hover:shadow-rose-400/70 hover:scale-105 transition-all">
                Get Started Free
                <Heart className="w-4 h-4 fill-white group-hover:scale-125 transition-transform" />
              </button>
            </Link>
          </div>
        </ParallaxSection>
      </section>

      {/* ════════ FOOTER ════════ */}
      <footer className="border-t border-rose-100 bg-white/50 backdrop-blur-sm">
        <div className="max-w-6xl mx-auto px-6 md:px-10 py-6 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Heart className="w-4 h-4 text-rose-400 fill-rose-400" />
            <span className="text-xs text-rose-400 font-medium">© 2024 RelAItion — Built with love for Paradigm 1.0</span>
          </div>
          <div className="flex items-center gap-4">
            <Link href="/dashboard" className="text-xs text-rose-400 hover:text-rose-600 font-medium transition-colors">Dashboard</Link>
            <Link href="/login" className="text-xs text-rose-400 hover:text-rose-600 font-medium transition-colors">Login</Link>
            <Link href="/signup" className="text-xs text-rose-400 hover:text-rose-600 font-medium transition-colors">Sign Up</Link>
          </div>
        </div>
      </footer>

      {/* ── Inline Animations ── */}
      <style jsx>{`
        @keyframes floatUp {
          0% { transform: translateY(0) rotate(0deg); opacity: 0; }
          10% { opacity: 1; }
          90% { opacity: 1; }
          100% { transform: translateY(-100vh) rotate(360deg); opacity: 0; }
        }
        @keyframes fadeDown {
          from { opacity: 0; transform: translateY(-20px); }
          to { opacity: 1; transform: translateY(0); }
        }
        @keyframes fadeUp {
          from { opacity: 0; transform: translateY(30px); }
          to { opacity: 1; transform: translateY(0); }
        }
        @keyframes heartbeat {
          0%, 100% { transform: scale(1); }
          25% { transform: scale(1.15); }
          50% { transform: scale(1); }
          75% { transform: scale(1.1); }
        }
        @keyframes progressBar {
          from { width: 0%; }
          to { width: 76%; }
        }
        .animate-fadeDown { animation: fadeDown 0.8s ease-out both; }
        .animate-fadeUp { animation: fadeUp 0.8s ease-out both; }
        .animate-heartbeat { animation: heartbeat 2s ease-in-out infinite; }
        .animate-progressBar { animation: progressBar 2s ease-out 1s both; }
      `}</style>
    </div>
  );
}
