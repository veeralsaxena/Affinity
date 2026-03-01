"use client";

import { useEffect, useState, useCallback, useRef } from "react";
import {
  Heart, LayoutDashboard, Users, Activity, FileText, Bell,
  Settings, MessageCircle, AlertTriangle, Search, Home,
  Wifi, Send, ChevronDown, CheckSquare, Clock, Map, Sparkles, X, CloudUpload, CheckCircle, Trash2
} from "lucide-react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useAuth } from "@/context/AuthContext";
import { cn } from "@/lib/utils";
import { BarChart, Bar, XAxis, YAxis, Tooltip as RechartsTooltip, ResponsiveContainer, PieChart, Pie, Cell } from "recharts";

const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

/* ─── Mock Data for Charts ────────────────────────────────────────── */

const weeklyData = [
  { name: 'Mon', interaction: 40, health: 60 },
  { name: 'Tue', interaction: 30, health: 55 },
  { name: 'Wed', interaction: 65, health: 70 },
  { name: 'Thu', interaction: 45, health: 65 },
  { name: 'Fri', interaction: 80, health: 85 },
  { name: 'Sat', interaction: 55, health: 75 },
  { name: 'Sun', interaction: 70, health: 80 },
];

const COLORS = ['#10B981', '#F59E0B', '#F43F5E', '#8B5CF6'];

/* ─── Custom Modal & Toast logic (Light Theme) ───────────────────── */

function UploadModal({ isOpen, onClose, token, onSuccess, selectedAnalysis = null }: { isOpen: boolean; onClose: () => void; token: string | null; onSuccess: () => void, selectedAnalysis?: any }) {
  const [tab, setTab] = useState<"whatsapp" | "instagram" | "audio" | "live">("whatsapp");
  const [file, setFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [result, setResult] = useState<any>(null);
  const [error, setError] = useState("");
  const fileRef = useRef<HTMLInputElement>(null);
  const [liveContact, setLiveContact] = useState("");
  const [toast, setToast] = useState<{msg: string, type: "success"|"error"} | null>(null);
  
  useEffect(() => {
    if (selectedAnalysis && isOpen) {
      setResult({
        ingestion: { message_count: selectedAnalysis.message_count },
        contact: { name: selectedAnalysis.contact_name, health_score: 100 - (selectedAnalysis.heat_score*5 + selectedAnalysis.decay_score*5), status: selectedAnalysis.route },
        analysis: {
          emotion: selectedAnalysis.emotion,
          gottman: selectedAnalysis.scoring_layers?.gottman,
          effort: selectedAnalysis.scoring_layers?.effort,
          mirroring: selectedAnalysis.scoring_layers?.mirroring,
          kl_drift: selectedAnalysis.scoring_layers?.kl_drift,
          nudges: typeof selectedAnalysis.nudges === "string" ? JSON.parse(selectedAnalysis.nudges) : selectedAnalysis.nudges
        }
      });
    } else if (!isOpen) {
      setResult(null);
      setFile(null);
      setLiveContact("");
    }
  }, [selectedAnalysis, isOpen]);

  if (!isOpen) return null;

  const handleUpload = async () => {
    if ((tab !== "live" && !file) || (tab === "live" && !liveContact) || !token) return;
    setUploading(true); setError(""); setResult(null);
    try {
      let res;
      if (tab === "live") {
        res = await fetch(`${API}/whatsapp/auto-ingest`, {
          method: "POST",
          headers: { Authorization: `Bearer ${token}`, "Content-Type": "application/json" },
          body: JSON.stringify({ contact_name: liveContact, limit: 50 }),
        });
      } else {
        const formData = new FormData();
        formData.append("file", file!);
        formData.append("source", tab);
        res = await fetch(`${API}/ingest-and-analyze`, { method: "POST", headers: { Authorization: `Bearer ${token}` }, body: formData });
      }

      if (!res.ok) throw new Error((await res.json()).detail || "Upload failed");
      setResult(await res.json());
      onSuccess();
    } catch (err: any) { setError(err.message); } finally { setUploading(false); }
  };

  return (
    <div className="fixed inset-0 z-[100] flex items-center justify-center bg-rose-950/40 backdrop-blur-sm" onClick={onClose}>
      <div className="bg-white/90 backdrop-blur-xl border border-white/50 rounded-2xl p-6 w-full max-w-lg shadow-2xl relative" onClick={(e) => e.stopPropagation()}>
        {toast && (
          <div className={cn("absolute -top-12 left-1/2 -translate-x-1/2 px-4 py-2 rounded-xl text-sm font-bold shadow-lg z-50 animate-in fade-in slide-in-from-top-4 flex items-center gap-2", toast.type === "success" ? "bg-emerald-50 text-emerald-700 border border-emerald-200" : "bg-rose-50 text-rose-700 border border-rose-200")}>
            {toast.type === "success" ? <CheckCircle className="w-4 h-4" /> : <AlertTriangle className="w-4 h-4" />}
            {toast.msg}
          </div>
        )}

        <button onClick={onClose} className="absolute top-4 right-4 text-rose-400 hover:text-rose-600 transition-colors"><X className="w-5 h-5" /></button>

        <h3 className="text-xl font-extrabold text-rose-950 mb-1">Analyze Connection</h3>
        <p className="text-sm text-rose-600/80 mb-5">Upload chat export or extract live natively via WhatsApp.</p>

        {!result ? (
          <>
            <div className="flex gap-2 mb-5 overflow-x-auto pb-2 custom-scrollbar">
              {(["whatsapp", "instagram", "audio", "live"] as const).map((t) => (
                <button key={t} onClick={() => { setTab(t); setFile(null); setLiveContact(""); setResult(null); setError(""); }}
                  className={cn("flex items-center gap-2 px-4 py-2.5 rounded-xl text-sm font-semibold transition-all whitespace-nowrap", tab === t ? "bg-gradient-to-r from-rose-400 to-pink-500 text-white shadow-lg shadow-rose-500/30" : "bg-rose-50 text-rose-600 hover:bg-rose-100")}>
                  {t === "live" ? <Wifi className="w-4 h-4" /> : <MessageCircle className="w-4 h-4" />}
                  <span className="capitalize">{t}</span>
                </button>
              ))}
            </div>

            {tab === "live" ? (
              <div className="bg-rose-50/50 border border-rose-100 rounded-xl p-6 text-center mb-4">
                <Wifi className="w-10 h-10 text-emerald-500 mx-auto mb-3" />
                <h4 className="text-rose-950 font-bold mb-2">Live WhatsApp Extraction</h4>
                <input type="text" placeholder="e.g. Mom, Alice, John Doe" value={liveContact} onChange={(e) => { setLiveContact(e.target.value); setError(""); }}
                  className="w-full max-w-xs px-4 py-2 rounded-lg bg-white border border-rose-200 focus:outline-none focus:border-rose-400 text-rose-950 text-sm shadow-sm" />
              </div>
            ) : (
             <div className="border-2 border-dashed border-rose-200 rounded-xl p-8 text-center cursor-pointer hover:border-rose-400 hover:bg-rose-50/50 transition-all mb-4 bg-white/50" onClick={() => fileRef.current?.click()}>
                <input ref={fileRef} type="file" className="hidden" onChange={(e) => { setFile(e.target.files?.[0] || null); setError(""); setResult(null); }} />
                <CloudUpload className="w-10 h-10 text-rose-300 mx-auto mb-3" />
                {file ? <p className="text-sm text-rose-900 font-medium">{file.name}</p> : <p className="text-sm text-rose-500">Click to upload unzipped export file</p>}
              </div>
            )}

            {error && <div className="bg-rose-50 border border-rose-200 text-rose-600 text-sm px-4 py-3 rounded-xl mb-4">{error}</div>}

            <button onClick={handleUpload} disabled={(tab !== "live" && !file) || (tab === "live" && !liveContact) || uploading}
              className="w-full py-3 rounded-xl bg-gradient-to-r from-rose-500 to-pink-500 text-white font-bold text-sm shadow-lg shadow-rose-500/30 hover:shadow-xl hover:shadow-rose-500/40 hover:scale-[1.02] transition-all disabled:opacity-50 flex items-center justify-center gap-2">
              {uploading ? "Analyzing pipeline..." : "Run Intelligence Pipeline"}
            </button>
          </>
        ) : (
          <div className="space-y-4">
            <div className="grid grid-cols-2 gap-3">
              <div className="bg-white border border-rose-100 rounded-xl p-3 shadow-sm">
                <p className="text-xs text-rose-500 font-medium uppercase tracking-wider">Contact</p>
                <p className="text-lg font-bold text-rose-950">{result.contact?.name}</p>
              </div>
              <div className="bg-white border border-rose-100 rounded-xl p-3 shadow-sm">
                <p className="text-xs text-rose-500 font-medium uppercase tracking-wider">Health Score</p>
                <p className="text-lg font-bold text-rose-950 flex items-center gap-1">
                  <span className={cn(result.contact.health_score >= 70 ? "text-emerald-500" : result.contact.health_score >= 40 ? "text-amber-500" : "text-rose-500")}>
                    {result.contact?.health_score?.toFixed(0)}
                  </span>
                  /100
                </p>
              </div>
            </div>

            {/* 8-Layer */}
            <div className="bg-rose-50 border border-rose-100 rounded-xl p-4 relative z-10">
              <p className="text-xs font-bold text-rose-800 mb-3 tracking-wide flex items-center gap-2"><Activity className="w-3 h-3"/> 8-Layer Intelligence Breakdown</p>
              <div className="grid grid-cols-2 gap-2">
                <div className="relative group cursor-help flex items-center justify-between bg-white rounded-lg px-3 py-2 border border-rose-100 hover:border-rose-300 transition-colors shadow-sm">
                  <span className="text-[11px] text-rose-600 font-medium">Gottman Ratio</span>
                  <span className="text-sm font-bold text-rose-950">{result.analysis?.gottman?.ratio ?? "—"}:1</span>
                  <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 w-48 p-2 bg-rose-950 border border-rose-800 text-rose-50 text-[10px] rounded-lg opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all z-50 text-center shadow-xl pointer-events-none font-medium">
                    Dr. John Gottman's 5:1 metric. Healthy relationships maintain at least 5 positive interactions for every 1 negative interaction.
                  </div>
                </div>
                <div className="relative group cursor-help flex items-center justify-between bg-white rounded-lg px-3 py-2 border border-rose-100 hover:border-rose-300 transition-colors shadow-sm">
                  <span className="text-[11px] text-rose-600 font-medium">Effort</span>
                  <span className="text-sm font-bold text-rose-950 capitalize">{result.analysis?.effort?.effort_balance?.replace("_", " ") ?? "—"}</span>
                   <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 w-48 p-2 bg-rose-950 border border-rose-800 text-rose-50 text-[10px] rounded-lg opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all z-50 text-center shadow-xl pointer-events-none font-medium">
                    Measures initiation ratios, question reciprocity, and text length discrepancy.
                  </div>
                </div>
                <div className="relative group cursor-help flex items-center justify-between bg-white rounded-lg px-3 py-2 border border-rose-100 hover:border-rose-300 transition-colors shadow-sm">
                  <span className="text-[11px] text-rose-600 font-medium">Mirroring</span>
                  <span className="text-sm font-bold text-rose-950">{((result.analysis?.mirroring?.mirroring_score ?? 0) * 100).toFixed(0)}%</span>
                  <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 w-48 p-2 bg-rose-950 border border-rose-800 text-rose-50 text-[10px] rounded-lg opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all z-50 text-center shadow-xl pointer-events-none font-medium">
                    Psychological mirroring alignment (emoji usage, vocab).
                  </div>
                </div>
                <div className="relative group cursor-help flex items-center justify-between bg-white rounded-lg px-3 py-2 border border-rose-100 hover:border-rose-300 transition-colors shadow-sm">
                  <span className="text-[11px] text-rose-600 font-medium">Sentiment</span>
                  <span className="text-sm font-bold text-rose-950 capitalize">{result.analysis?.kl_drift?.direction ?? "—"}</span>
                   <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 w-48 p-2 bg-rose-950 border border-rose-800 text-rose-50 text-[10px] rounded-lg opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all z-50 text-center shadow-xl pointer-events-none font-medium">
                    Kullback-Leibler Divergence tracking emotional decay.
                  </div>
                </div>
              </div>
            </div>

            {result.analysis?.nudges?.length > 0 && (
              <div className="bg-rose-50 border border-rose-100 rounded-xl p-4">
                <p className="text-xs font-bold text-rose-800 mb-3 flex items-center gap-2"><MessageCircle className="w-3 h-3"/> AI-Drafted Messages</p>
                {result.analysis.nudges.map((n: string, i: number) => (
                  <div key={i} className="flex flex-col gap-2 mb-3 bg-white p-3 rounded-lg border border-rose-100 shadow-sm">
                    <p className="text-sm text-rose-900 leading-relaxed font-medium">{n}</p>
                    <button onClick={async (e) => {
                        e.stopPropagation();
                        try {
                          const res = await fetch(`${API}/whatsapp/send`, { method: "POST", headers: { Authorization: `Bearer ${token}`, "Content-Type": "application/json" }, body: JSON.stringify({ contact_name: result.contact?.name, message: n }) });
                          const data = await res.json();
                          if (data.status === "success" || data.status === "sent") setToast({ msg: `Sent to ${result.contact?.name}!`, type: "success" });
                          else setToast({ msg: data.error || "Failed to send message", type: "error" });
                        } catch (err) { setToast({ msg: "Failed to reach backend", type: "error" }); }
                        setTimeout(() => setToast(null), 3000);
                      }}
                      className="self-end px-3 py-1.5 rounded-lg bg-emerald-50 text-emerald-600 border border-emerald-200 text-xs font-bold hover:bg-emerald-100 transition-all flex items-center gap-1 shadow-sm">
                      <Send className="w-3 h-3" /> Auto-Send
                    </button>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

/* ─── Main Page (Light Rose Glassmorphism Theme) ─────────────────── */

export default function DashboardPage() {
  const { user, token, isAuthenticated, isLoading: authLoading, logout } = useAuth();
  const router = useRouter();
  const [dashData, setDashData] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [showUpload, setShowUpload] = useState(false);
  const [selectedAnalysis, setSelectedAnalysis] = useState<any>(null);
  const [waConnected, setWaConnected] = useState(false);
  const [waLoading, setWaLoading] = useState(false);
  const [deleteConfirm, setDeleteConfirm] = useState<{ id: string, name: string } | null>(null);
  const [activeTab, setActiveTab] = useState("dashboard");

  useEffect(() => { if (!authLoading && !isAuthenticated) router.push("/login"); }, [isAuthenticated, authLoading, router]);

  const fetchDashboard = useCallback(async () => {
    if (!token) return;
    try {
      const res = await fetch(`${API}/dashboard`, { headers: { Authorization: `Bearer ${token}` } });
      if (res.ok) setDashData(await res.json());
    } catch (e) {} finally { setLoading(false); }
  }, [token]);

  useEffect(() => { if (token) fetchDashboard(); }, [token, fetchDashboard]);

  if (authLoading || loading) return <div className="min-h-screen bg-rose-50/50 flex items-center justify-center"><div className="w-8 h-8 border-4 border-rose-400 border-t-transparent rounded-full animate-spin"/></div>;

  const stats = dashData?.stats;
  const contacts = dashData?.contacts || [];
  const analyses = dashData?.recent_analyses || [];

  const handleDeleteContact = async () => {
    if (!deleteConfirm || !token) return;
    try {
      const res = await fetch(`${API}/contacts/${deleteConfirm.id}`, { method: "DELETE", headers: { Authorization: `Bearer ${token}` } });
      if (res.ok) {
        setDeleteConfirm(null);
        fetchDashboard();
      }
    } catch (e) {}
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-rose-50 to-pink-50/50 text-rose-950 font-sans flex overflow-hidden">
      
      {/* ═ LEFT SIDEBAR ═ */}
      <aside className="w-64 bg-white/60 backdrop-blur-xl border-r border-rose-100/50 p-5 flex flex-col shrink-0 shadow-[4px_0_24px_rgba(225,29,72,0.02)] z-10">
        <div className="flex items-center gap-3 mb-10 mt-2 px-2">
          <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-rose-400 to-pink-500 flex items-center justify-center shadow-lg shadow-rose-500/20">
            <Heart className="w-4 h-4 text-white" />
          </div>
          <span className="text-lg font-bold text-rose-950 tracking-wide">RelAItion</span>
        </div>

        <nav className="space-y-1.5 flex-1">
          {[
            { icon: Home, label: "Home", href: "/" },
            { id: "dashboard", icon: LayoutDashboard, label: "Dashboard" },
            { id: "contacts", icon: Users, label: `Contacts` },
            { id: "health-scores", icon: Activity, label: `Health Scores` },
            { id: "reports", icon: FileText, label: `Reports` },
            { id: "social-map", icon: Map, label: `Social Map` },
            { id: "reminders", icon: Bell, label: `Reminders` },
            { id: "insights", icon: Sparkles, label: `Insights` },
            { id: "settings", icon: Settings, label: `Settings` },
          ].map((item, i) => (
            item.href === "/" ? (
                <Link key={i} href={item.href} className={cn("w-full flex items-center gap-3 px-4 py-3 rounded-xl text-sm font-medium transition-all group text-rose-600 hover:bg-rose-50 hover:text-rose-900")}>
                  <item.icon className="w-4 h-4 text-rose-400 group-hover:text-rose-600" />
                  {item.label}
                </Link>
            ) : (
                <button key={i} onClick={() => setActiveTab(item.id!)} className={cn("w-full flex items-center gap-3 px-4 py-3 rounded-xl text-sm font-medium transition-all group", activeTab === item.id ? "bg-white text-rose-900 shadow-sm border border-rose-100/50 shadow-[inset_2px_0_0_#F43F5E]" : "text-rose-600 hover:bg-rose-50 hover:text-rose-900")}>
                  <item.icon className={cn("w-4 h-4", activeTab === item.id ? "text-rose-500" : "text-rose-400 group-hover:text-rose-600")} />
                  {item.label}
                  {item.label === "Contacts" && <span className="ml-auto bg-rose-100 text-[10px] px-2 py-0.5 rounded-full text-rose-700 font-bold">{stats?.total_contacts||0}</span>}
                </button>
            )
          ))}
        </nav>

        {/* Floating Sync Box (Light Theme) */}
        <div className="bg-white/80 border border-rose-100 rounded-2xl p-4 relative overflow-hidden group shadow-sm mt-4">
          <div className="absolute inset-0 bg-gradient-to-br from-emerald-50 to-transparent opacity-50" />
          <p className="text-rose-950 text-sm font-bold flex items-center gap-2 relative z-10 mb-3 whitespace-nowrap"><Wifi className="w-4 h-4 text-emerald-500"/> Sync Chats</p>
          <div className="flex gap-2 relative z-10 mb-3">
            <div className="w-8 h-8 rounded-full bg-emerald-50 flex items-center justify-center border border-emerald-100"><MessageCircle className="w-4 h-4 text-emerald-500"/></div>
            <div className="w-8 h-8 rounded-full bg-blue-50 flex items-center justify-center border border-blue-100 opacity-70"><Send className="w-4 h-4 text-blue-500"/></div>
          </div>
          <button onClick={async () => {
              setWaLoading(true);
              try {
                if (waConnected) await fetch(`${API}/whatsapp/disconnect`, { method: "POST", headers: { Authorization: `Bearer ${token}` } });
                else await fetch(`${API}/whatsapp/connect`, { method: "POST", headers: { Authorization: `Bearer ${token}` } });
                setWaConnected(!waConnected);
              } catch (e) {} setWaLoading(false);
            }} disabled={waLoading}
            className="w-full py-2 bg-emerald-50 hover:bg-emerald-100 border border-emerald-200 text-emerald-600 text-xs font-bold rounded-lg transition-all relative z-10 shadow-sm disabled:opacity-50">
            {waLoading ? "Connecting..." : waConnected ? "Disconnect" : "Connect WhatsApp"}
          </button>
          <p className="text-[10px] text-rose-400 mt-2 relative z-10 font-medium">Last synced: <span className="text-rose-600">Just now</span></p>
        </div>
      </aside>

      {/* ═ MAIN DASHBOARD ═ */}
      <main className="flex-1 p-8 overflow-y-auto scroll-mt-6">
        <div className="flex justify-between items-center mb-8">
          <div>
            <h1 className="text-2xl font-bold text-rose-950 flex items-center gap-2 capitalize">
              {activeTab.replace('-', ' ')}
            </h1>
            <p className="text-sm text-rose-600 mt-1">Welcome back, {dashData?.user?.full_name || dashData?.user?.username} <span className="inline-block animate-wave">👋</span></p>
          </div>
          <div className="flex items-center gap-4">
            <button onClick={() => setShowUpload(true)} className="px-5 py-2.5 rounded-full bg-rose-950 text-white font-bold text-sm shadow-xl shadow-rose-900/20 hover:shadow-rose-900/30 hover:-translate-y-0.5 transition-all flex items-center gap-2">
              <CloudUpload className="w-4 h-4" /> Analyze New Chat
            </button>
            <div className="relative">
              <Search className="w-4 h-4 text-rose-400 absolute left-3 top-1/2 -translate-y-1/2" />
              <input type="text" placeholder="Search Contacts..." className="bg-white/60 border border-rose-100 rounded-full py-2 pl-9 pr-4 text-sm text-rose-900 focus:outline-none focus:border-rose-400 transition-colors w-64 shadow-sm placeholder:text-rose-300" />
            </div>
            <button className="w-10 h-10 rounded-full bg-white/60 border border-rose-100 flex items-center justify-center text-rose-500 hover:text-rose-700 hover:bg-white transition-colors relative shadow-sm">
              <Bell className="w-4 h-4" />
              <span className="absolute top-2 right-2.5 w-2 h-2 bg-rose-500 rounded-full border-2 border-white" />
            </button>
          </div>
        </div>

        {/* 4 Top Cards (Rendered on Dashboard & Health Scores) */}
        {(activeTab === "dashboard" || activeTab === "health-scores") && (
        <div className="grid grid-cols-4 gap-4 mb-6 scroll-mt-6">
          <div className="bg-white/70 backdrop-blur-xl border border-rose-100/50 rounded-2xl p-5 flex flex-col justify-between shadow-sm">
            <p className="text-sm text-rose-500 font-semibold">Overall Health Score</p>
            <div className="flex items-center gap-4 mt-2">
              <div className="relative w-16 h-16 shrink-0 flex items-center justify-center rounded-full border-[4px] border-rose-50">
                 <svg className="absolute inset-0 w-full h-full -rotate-90">
                    <circle cx="32" cy="32" r="28" stroke="url(#roseglow)" strokeWidth="4" fill="none" strokeDasharray="175" strokeDashoffset="45" strokeLinecap="round" />
                    <defs>
                      <linearGradient id="roseglow" x1="0%" y1="0%" x2="100%" y2="100%">
                        <stop offset="0%" stopColor="#F43F5E" />
                        <stop offset="100%" stopColor="#8B5CF6" />
                      </linearGradient>
                    </defs>
                  </svg>
                  <span className="text-xl font-black text-rose-950">{stats?.average_health?.toFixed(0) || 0}</span>
              </div>
              <div>
                <span className="text-2xl font-bold text-rose-950">{stats?.average_health?.toFixed(0) || 0}</span><span className="text-rose-400 text-sm">/100</span>
                <p className="text-xs font-bold text-emerald-500 tracking-wide uppercase mt-1">Good</p>
              </div>
            </div>
          </div>
          <div className="bg-gradient-to-br from-rose-50 to-white/70 backdrop-blur-xl border border-rose-100/80 rounded-2xl p-5 shadow-sm">
            <div className="flex justify-between items-start mb-2">
              <p className="text-sm text-rose-800 font-semibold">At-Risk</p>
              <AlertTriangle className="w-4 h-4 text-rose-500" />
            </div>
            <p className="text-3xl font-bold text-rose-600">{stats?.at_risk || 0}</p>
            <p className="text-xs text-rose-500 mt-3 flex items-center gap-1 cursor-pointer hover:underline font-medium">View Details <ChevronDown className="w-3 h-3 -rotate-90" /></p>
          </div>
          <div className="bg-gradient-to-br from-emerald-50/50 to-white/70 backdrop-blur-xl border border-emerald-100/80 rounded-2xl p-5 shadow-sm">
             <div className="flex justify-between items-start mb-2">
              <p className="text-sm text-emerald-800 font-semibold">Strongest Bonds</p>
              <Heart className="w-4 h-4 text-emerald-500 fill-emerald-500/20" />
            </div>
            <div className="flex items-end gap-3">
              <p className="text-3xl font-bold text-emerald-600">{stats?.thriving || 0}</p>
              <div className="flex -space-x-2 pb-1">
                {[...Array(3)].map((_,i) => <div key={i} className="w-6 h-6 rounded-full bg-gradient-to-br from-emerald-300 to-teal-400 border-2 border-white shadow-sm" />)}
              </div>
            </div>
            <div className="w-full h-1.5 bg-emerald-100 rounded-full mt-3 overflow-hidden"><div className="w-3/4 h-full bg-emerald-400 rounded-full" /></div>
          </div>
          <div className="bg-gradient-to-br from-amber-50/50 to-white/70 backdrop-blur-xl border border-amber-100/80 rounded-2xl p-5 flex flex-col justify-between shadow-sm">
            <div className="flex justify-between items-start mb-2">
              <p className="text-sm text-amber-800 font-semibold">Pending Follow-ups</p>
              <Clock className="w-4 h-4 text-amber-500" />
            </div>
            <p className="text-3xl font-bold text-amber-500">{Math.floor(Math.random() * 5) + 1}</p>
            <p className="text-xs text-amber-600 mt-3 flex items-center gap-1 cursor-pointer hover:underline font-medium">View <ChevronDown className="w-3 h-3 -rotate-90" /></p>
          </div>
        </div>
        )}

        {/* Relationship Priority (Rendered on Dashboard & Contacts) */}
        {(activeTab === "dashboard" || activeTab === "contacts") && (
        <div className="bg-white/70 backdrop-blur-xl border border-rose-100/50 rounded-2xl p-5 mb-6 shadow-sm scroll-mt-6">
          <div className="flex justify-between items-center mb-6">
            <h2 className="text-lg font-extrabold text-rose-950">Relationship Priority</h2>
            <div className="flex items-center gap-2 bg-white border border-rose-100 px-3 py-1.5 rounded-lg shadow-sm">
              <span className="text-xs text-rose-500 font-medium">Sort by:</span>
              <span className="text-xs text-rose-900 font-bold flex items-center gap-1">Urgency <ChevronDown className="w-3 h-3" /></span>
            </div>
          </div>
          <div className="space-y-3">
            {analyses.length > 0 ? analyses.map((a: any, i: number) => (
              <div key={i} className="flex items-center justify-between bg-white border border-rose-100/50 rounded-xl p-4 hover:border-rose-200 hover:shadow-md transition-all cursor-pointer group" onClick={() => setSelectedAnalysis(a)}>
                <div className="flex items-center gap-4 w-64">
                  <div className="w-10 h-10 rounded-full bg-gradient-to-br from-rose-400 to-pink-500 flex items-center justify-center font-bold text-white shadow-md shadow-rose-200">
                    {a.contact_name.substring(0,2).toUpperCase()}
                  </div>
                  <div>
                    <h3 className="text-sm font-bold text-rose-950 group-hover:text-rose-600 transition-colors">{a.contact_name}</h3>
                    <div className="flex items-center mt-1">
                      <span className={cn("text-[10px] px-2 py-0.5 rounded-full font-bold", 
                        a.route === "conflict" ? "bg-rose-100 text-rose-600" :
                        a.route === "drifting" ? "bg-amber-100 text-amber-600" :
                        "bg-emerald-100 text-emerald-600")}>
                        {a.route === "conflict" ? "Declining ↓" : a.route === "drifting" ? "Plan Pending" : "Thriving"}
                      </span>
                    </div>
                  </div>
                </div>
                {/* Mock Sparkline (Light) */}
                <div className="hidden lg:block flex-1 max-w-[120px]">
                   <svg width="100%" height="24" viewBox="0 0 100 24" className="overflow-visible opacity-80">
                     <path d={a.route === "conflict" ? "M0,5 Q10,5 20,8 T40,15 T60,12 T80,20 T100,22" : a.route === "drifting" ? "M0,20 Q10,18 20,15 T40,15 T60,10 T80,8 T100,5" : "M0,20 Q20,15 40,8 T60,12 T80,5 T100,2"} fill="none" stroke={a.route === "conflict" ? "#E11D48" : a.route==="drifting" ? "#D97706" : "#059669"} strokeWidth="2" strokeLinecap="round" />
                   </svg>
                </div>
                <div className="hidden md:block w-32 text-center">
                  <p className="text-lg font-bold text-rose-950">{100 - (a.heat_score*5 + a.decay_score*5)}</p>
                  <div className="w-full h-1.5 bg-rose-50 rounded-full mt-1 overflow-hidden">
                     <div className={cn("h-full rounded-full", a.route === "conflict" ? "bg-rose-500 w-1/4" : a.route==="drifting" ? "bg-amber-500 w-2/4" : "bg-emerald-500 w-3/4")} />
                  </div>
                </div>
                <div className="hidden xl:block w-36 text-right">
                  <p className="text-[11px] text-rose-400 font-medium">Last msg: <span className="text-rose-600 font-bold">{a.created_at ? new Date(a.created_at).toLocaleDateString() : "Today"}</span></p>
                </div>
                <div className="flex items-center gap-2 shrink-0">
                  <button className={cn("px-4 py-2 rounded-lg text-xs font-bold transition-all shadow-sm", 
                    a.route === "conflict" ? "bg-rose-50 text-rose-600 hover:bg-rose-100 border border-rose-200" :
                    a.route === "drifting" ? "bg-emerald-50 text-emerald-600 hover:bg-emerald-100 border border-emerald-200" :
                    "bg-blue-50 text-blue-600 hover:bg-blue-100 border border-blue-200"
                    )}>
                    {a.route === "conflict" ? "Suggest Message" : a.route === "drifting" ? "Follow Up" : "Reconnect"}
                  </button>
                  <button 
                    onClick={(e) => { 
                      e.stopPropagation(); 
                      const cId = contacts?.find((c: any) => c.name === a.contact_name)?.id;
                      if (cId) setDeleteConfirm({ id: cId, name: a.contact_name });
                    }} 
                    className="p-2 rounded-lg text-rose-300 hover:text-rose-600 hover:bg-rose-50 transition-colors"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
              </div>
            )) : <div className="text-center py-10 bg-white/40 border border-dashed border-rose-200 rounded-xl">
                 <p className="text-sm text-rose-500 font-medium">No relationships analyzed yet.</p>
                 <button onClick={() => setShowUpload(true)} className="mt-3 text-sm font-bold text-rose-600 hover:text-rose-800 underline">Upload your first chat</button>
               </div>}
          </div>
        </div>
        )}

        {/* Bottom Metrics Grid (Rendered on Dashboard, Reports, Social Map) */}
        {(activeTab === "dashboard" || activeTab === "reports" || activeTab === "social-map" || activeTab === "health-scores") && (
        <div className="grid lg:grid-cols-3 gap-6 scroll-mt-6">
          <div className="bg-white/70 backdrop-blur-xl border border-rose-100/50 rounded-2xl p-5 lg:col-span-1 shadow-sm">
            <h3 className="text-xs font-bold text-rose-500 uppercase tracking-widest mb-4">Weekly Report</h3>
            <div className="h-44 w-full">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={weeklyData} margin={{ top: 0, right: 0, left: -20, bottom: 0 }}>
                  <XAxis dataKey="name" stroke="#FDA4AF" fontSize={10} tickLine={false} axisLine={false} />
                  <YAxis stroke="#FDA4AF" fontSize={10} tickLine={false} axisLine={false} />
                  <RechartsTooltip cursor={{fill: 'rgba(244,63,94,0.05)'}} contentStyle={{ backgroundColor: '#fff', borderColor: '#FFE4E6', borderRadius: '8px', fontSize: '12px', color: '#4C0519', boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)' }} />
                  <Bar dataKey="interaction" fill="#F43F5E" radius={[2, 2, 0, 0]} />
                  <Bar dataKey="health" fill="#8B5CF6" radius={[2, 2, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
            <div className="flex justify-center gap-4 mt-2">
              <div className="flex items-center gap-1"><div className="w-2 h-2 rounded-full bg-rose-500"/><span className="text-[10px] text-rose-600 font-bold">Interaction</span></div>
              <div className="flex items-center gap-1"><div className="w-2 h-2 rounded-full bg-violet-500"/><span className="text-[10px] text-rose-600 font-bold">Health</span></div>
            </div>
          </div>
          
          <div className="bg-white/70 backdrop-blur-xl border border-rose-100/50 rounded-2xl p-5 lg:col-span-1 flex flex-col shadow-sm">
            <h3 className="text-xs font-bold text-rose-500 uppercase tracking-widest mb-2">Health Distribution</h3>
            <div className="flex-1 flex items-center justify-between">
              <div className="w-32 h-32 relative drop-shadow-md">
                <ResponsiveContainer width="100%" height="100%">
                  <PieChart>
                    <Pie data={[{value:stats?.thriving||1}, {value:stats?.stable||1}, {value:stats?.at_risk||1}, {value:stats?.dormant||1}]} innerRadius={35} outerRadius={50} stroke="none" paddingAngle={5} dataKey="value">
                      {COLORS.map((c, i) => <Cell key={i} fill={c} />)}
                    </Pie>
                  </PieChart>
                </ResponsiveContainer>
              </div>
              <div className="space-y-3">
                <div className="flex items-center gap-2"><div className="w-2 h-2 rounded-full bg-[#10B981] shadow-sm"/><span className="text-xs font-bold text-rose-900">Thriving ({stats?.thriving||0})</span></div>
                <div className="flex items-center gap-2"><div className="w-2 h-2 rounded-full bg-[#F59E0B] shadow-sm"/><span className="text-xs font-bold text-rose-900">Stable ({stats?.stable||0})</span></div>
                <div className="flex items-center gap-2"><div className="w-2 h-2 rounded-full bg-[#F43F5E] shadow-sm"/><span className="text-xs font-bold text-rose-900">At Risk ({stats?.at_risk||0})</span></div>
                <div className="flex items-center gap-2"><div className="w-2 h-2 rounded-full bg-[#8B5CF6] shadow-sm"/><span className="text-xs font-bold text-rose-900">Dormant ({stats?.dormant||0})</span></div>
              </div>
            </div>
          </div>

          {(activeTab === "dashboard" || activeTab === "social-map") && (
          <div className="bg-white/70 backdrop-blur-xl border border-rose-100/50 rounded-2xl p-5 lg:col-span-1 border-t-4 border-t-rose-400 relative overflow-hidden scroll-mt-6 shadow-sm">
            <div className="absolute inset-0 opacity-10 pointer-events-none" style={{ backgroundImage: 'radial-gradient(circle at center, #F43F5E 0%, transparent 70%)' }} />
            <h3 className="text-xs font-bold text-rose-500 uppercase tracking-widest mb-4 relative z-10">Social Map</h3>
            <div className="w-full h-40 relative drop-shadow-sm">
               {/* Mock Social Map SVG (Light Version) */}
               <svg className="w-full h-full" viewBox="0 0 200 120">
                 <line x1="100" y1="60" x2="40" y2="40" stroke="#FDA4AF" strokeWidth="1.5" strokeDasharray="3 3" />
                 <line x1="100" y1="60" x2="160" y2="30" stroke="#FDA4AF" strokeWidth="1.5" />
                 <line x1="100" y1="60" x2="160" y2="90" stroke="#8B5CF6" strokeWidth="1.5" />
                 <line x1="100" y1="60" x2="60" y2="100" stroke="#06B6D4" strokeWidth="1.5" />
                 
                 {/* Nodes */}
                 <circle cx="100" cy="60" r="16" fill="#fff" stroke="#F43F5E" strokeWidth="3" />
                 <text x="100" y="64" fill="#881337" fontSize="10" fontWeight="bold" textAnchor="middle">You</text>
                 
                 <circle cx="40" cy="40" r="10" fill="#FFE4E6" stroke="#FDA4AF" strokeWidth="1" />
                 <text x="40" y="60" fill="#9F1239" fontSize="8" fontWeight="bold" textAnchor="middle">Rahul</text>

                 <circle cx="160" cy="30" r="10" fill="#FFE4E6" stroke="#FDA4AF" strokeWidth="1" />
                 <text x="160" y="50" fill="#9F1239" fontSize="8" fontWeight="bold" textAnchor="middle">Ayesha</text>

                 <circle cx="160" cy="90" r="10" fill="#EDE9FE" stroke="#C4B5FD" strokeWidth="1" />
                 <text x="160" y="112" fill="#5B21B6" fontSize="8" fontWeight="bold" textAnchor="middle">Karan</text>
                 
                 <circle cx="60" cy="100" r="10" fill="#CFFAFE" stroke="#67E8F9" strokeWidth="1" />
               </svg>
            </div>
          </div>
          )}
        </div>
        )}

        {/* Placeholder for tabs without specific content yet */}
        {(activeTab === "reminders" || activeTab === "insights" || activeTab === "settings") && (
          <div className="bg-white/70 backdrop-blur-xl border border-rose-100/50 rounded-2xl p-10 mt-6 shadow-sm text-center">
            <div className="w-16 h-16 rounded-full bg-rose-50 border-4 border-white shadow-sm flex items-center justify-center mx-auto mb-4">
              {activeTab === "settings" ? <Settings className="w-8 h-8 text-rose-400" /> :
               activeTab === "reminders" ? <Bell className="w-8 h-8 text-amber-400" /> :
               <Sparkles className="w-8 h-8 text-violet-400" />}
            </div>
            <h2 className="text-xl font-extrabold text-rose-950 mb-2 capitalize">{activeTab}</h2>
            <p className="text-rose-500 font-medium max-w-md mx-auto">This dedicated full-page view is under construction. Advanced features for this section are coming soon!</p>
          </div>
        )}

      </main>

      {/* ═ RIGHT SIDEBAR (Light Theme) ═ */}
      <aside className="w-80 bg-white/60 backdrop-blur-xl border-l border-rose-100/50 p-6 flex flex-col shrink-0 overflow-y-auto hidden lg:flex shadow-[-4px_0_24px_rgba(225,29,72,0.02)] z-10">
        <div className="flex justify-end mb-8">
           <div className="flex -space-x-3 drop-shadow-sm">
              <div className="w-10 h-10 rounded-full bg-violet-100 border-2 border-white flex items-center justify-center font-bold text-violet-700 text-sm z-20">U</div>
              <div className="w-10 h-10 rounded-full bg-emerald-100 border-2 border-white flex items-center justify-center font-bold text-emerald-700 text-sm z-10">M</div>
              <div className="w-10 h-10 rounded-full bg-rose-100 border-2 border-white flex items-center justify-center font-bold text-rose-700 text-sm">A</div>
           </div>
        </div>

        <h3 id="insights" className="text-rose-950 font-extrabold text-lg flex items-center gap-2 mb-4 scroll-mt-6">
          AI Insights <Sparkles className="w-4 h-4 text-rose-500" />
        </h3>
        
        <div className="space-y-3 mb-10">
          <div className="bg-white border border-rose-100 rounded-xl p-4 relative overflow-hidden group hover:border-violet-300 transition-colors shadow-sm">
            <div className="absolute right-0 top-0 w-1.5 h-full bg-violet-400 rounded-r-xl" />
            <p className="text-xs text-rose-600 leading-relaxed font-medium">
              Your interaction <span className="text-violet-700 font-bold">dropped 32%</span> this week with key contacts.
            </p>
          </div>
          <div className="bg-white border border-rose-100 rounded-xl p-4 relative overflow-hidden group hover:border-rose-300 transition-colors shadow-sm">
            <div className="absolute right-0 top-0 w-1.5 h-full bg-rose-500 rounded-r-xl" />
            <p className="text-xs text-rose-600 leading-relaxed font-medium">
              <span className="text-rose-700 font-bold">2 important chats</span> need follow-up immediately.
            </p>
          </div>
          <div className="bg-gradient-to-br from-amber-50 to-white/80 border border-amber-200 rounded-xl p-4 relative overflow-hidden group hover:border-amber-400 transition-colors shadow-sm">
             <div className="absolute right-0 top-0 w-1.5 h-full bg-amber-400 rounded-r-xl" />
             <p className="text-xs text-amber-800 leading-relaxed font-medium">
              Karan's birthday is in <span className="text-amber-600 font-bold">3 days!</span> 🎉
            </p>
          </div>
          <button className="w-full py-2 rounded-lg bg-rose-50 hover:bg-rose-100 text-xs font-bold text-rose-600 transition-colors border border-rose-200 shadow-sm mt-2">
            View All Insights
          </button>
        </div>

        <h3 id="reminders" className="text-rose-950 font-extrabold text-lg mb-4 scroll-mt-6">Smart Actions</h3>
        <div className="space-y-3">
          <button onClick={() => setShowUpload(true)} className="w-full flex items-center justify-between p-4 rounded-xl bg-white border border-rose-100 hover:border-rose-300 hover:shadow-md group transition-all shadow-sm">
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-lg bg-violet-50 text-violet-600 group-hover:bg-violet-100 transition-colors"><FileText className="w-4 h-4" /></div>
              <span className="text-sm text-rose-900 font-bold group-hover:text-rose-600 transition-colors">Draft Check-in Message</span>
            </div>
          </button>
          <button className="w-full flex items-center justify-between p-4 rounded-xl bg-white border border-rose-100 hover:border-rose-300 hover:shadow-md group transition-all shadow-sm">
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-lg bg-emerald-50 text-emerald-600 group-hover:bg-emerald-100 transition-colors"><Clock className="w-4 h-4" /></div>
              <span className="text-sm text-rose-900 font-bold group-hover:text-rose-600 transition-colors">Schedule Reminder</span>
            </div>
          </button>
          <button className="w-full flex items-center justify-between p-4 rounded-xl bg-white border border-rose-100 hover:border-rose-300 hover:shadow-md group transition-all shadow-sm">
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-lg bg-amber-50 text-amber-600 group-hover:bg-amber-100 transition-colors"><CheckSquare className="w-4 h-4" /></div>
              <span className="text-sm text-rose-900 font-bold group-hover:text-rose-600 transition-colors">Shared Memories</span>
            </div>
          </button>
        </div>

      </aside>

      {/* Delete Confirmation Modal */}
      {deleteConfirm && (
        <div className="fixed inset-0 z-[200] flex items-center justify-center bg-rose-950/40 backdrop-blur-sm" onClick={() => setDeleteConfirm(null)}>
          <div className="bg-white border border-rose-200 rounded-2xl p-6 w-full max-w-sm shadow-2xl relative" onClick={(e) => e.stopPropagation()}>
            <div className="w-12 h-12 rounded-full bg-rose-50 border-4 border-white shadow-sm flex items-center justify-center mb-4 mx-auto">
              <AlertTriangle className="w-6 h-6 text-rose-500" />
            </div>
            <h3 className="text-lg font-extrabold text-rose-950 text-center mb-2">Delete Connection</h3>
            <p className="text-sm text-rose-600 text-center mb-6">Are you sure you want to delete <span className="font-bold">{deleteConfirm.name}</span> and all associated historical AI pipeline data? This action cannot be undone.</p>
            <div className="flex gap-3">
              <button 
                onClick={() => setDeleteConfirm(null)} 
                className="flex-1 py-2.5 rounded-xl bg-gray-50 text-gray-600 font-bold border border-gray-200 hover:bg-gray-100 transition-all text-sm"
              >
                Cancel
              </button>
              <button 
                onClick={handleDeleteContact} 
                className="flex-1 py-2.5 rounded-xl bg-rose-500 text-white font-bold shadow-lg shadow-rose-500/30 hover:bg-rose-600 hover:shadow-rose-500/40 transition-all text-sm"
              >
                Yes, Delete
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Upload/Result Modal */}
      <UploadModal isOpen={showUpload || !!selectedAnalysis} onClose={() => { setShowUpload(false); setSelectedAnalysis(null); }} token={token} onSuccess={fetchDashboard} selectedAnalysis={selectedAnalysis} />
    </div>
  );
}
