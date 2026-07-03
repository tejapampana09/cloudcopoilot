import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip, Cell 
} from 'recharts';
import { Sidebar } from './components/Sidebar';
import { Header } from './components/Header';
import { UrlInputCard } from './components/UrlInputCard';
import { AgentActivity } from './components/AgentActivity';
import { RecentDeploymentsCard } from './components/RecentDeploymentsCard';
import { DeploymentStepsCard } from './components/DeploymentStepsCard';
import { AIConsultantChat } from './components/AIConsultantChat';
import { useAnalysisStream } from './hooks/useAnalysisStream';
import { 
  AlertCircle, Loader2, ShieldAlert, Sparkles, 
  Activity, Layers, FileCode2,
  DollarSign, Zap, Bug, BookOpen, Terminal, ChevronRight
} from 'lucide-react';
import { Login } from './components/Login';
import { api } from './services/api';

// Custom SVG Donut Component for Cost Breakdown
const CostDonut: React.FC<{ compute: number; database: number; storage: number; transfer: number }> = ({ 
  compute, database, storage, transfer 
}) => {
  const total = compute + database + storage + transfer;
  if (total === 0) return <div className="text-xs text-slate-500">No cost data available</div>;

  const data = [
    { label: 'Compute', value: compute, color: '#3b82f6' },
    { label: 'Database', value: database, color: '#f59e0b' },
    { label: 'Storage', value: storage, color: '#10b981' },
    { label: 'Transfer', value: transfer, color: '#8b5cf6' }
  ].filter(d => d.value > 0);

  let accumulatedPercent = 0;

  return (
    <div className="flex flex-col md:flex-row items-center gap-6 p-4 bg-white border border-slate-200/60 rounded-2xl shadow-sm">
      <div className="relative w-28 h-28 shrink-0">
        <svg viewBox="0 0 36 36" className="w-full h-full transform -rotate-90">
          <circle cx="18" cy="18" r="15.915" fill="none" stroke="#f1f5f9" strokeWidth="2.5" />
          {data.map((item, idx) => {
            const percent = (item.value / total) * 100;
            const strokeDasharray = `${percent} ${100 - percent}`;
            const strokeDashoffset = 100 - accumulatedPercent;
            accumulatedPercent += percent;
            return (
              <circle
                key={idx}
                cx="18"
                cy="18"
                r="15.915"
                fill="none"
                stroke={item.color}
                strokeWidth="2.8"
                strokeDasharray={strokeDasharray}
                strokeDashoffset={strokeDashoffset}
                className="transition-all duration-500"
              />
            );
          })}
        </svg>
        <div className="absolute inset-0 flex flex-col items-center justify-center">
          <span className="text-[10px] text-slate-400 font-bold uppercase tracking-wider">Total</span>
          <span className="text-sm font-extrabold text-slate-800">${total.toFixed(2)}</span>
        </div>
      </div>

      <div className="flex-1 space-y-2 w-full">
        {data.map((item, idx) => (
          <div key={idx} className="flex justify-between items-center text-[11px]">
            <div className="flex items-center gap-2">
              <div className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: item.color }} />
              <span className="text-slate-500 font-semibold">{item.label}</span>
            </div>
            <span className="font-extrabold text-slate-700">
              ${item.value.toFixed(2)} ({((item.value / total) * 100).toFixed(0)}%)
            </span>
          </div>
        ))}
      </div>
    </div>
  );
};

// Custom SVG Bar Chart comparing AWS Compute Options costs
const ComputeCompareChart: React.FC<{ recommendedTarget: string }> = ({ 
  recommendedTarget 
}) => {
  const options = [
    { target: 'AWS Lambda', cost: 5.20, active: recommendedTarget === 'AWS Lambda' },
    { target: 'AWS Amplify', cost: 3.50, active: recommendedTarget === 'AWS Amplify' },
    { target: 'AWS App Runner', cost: 35.86, active: recommendedTarget === 'AWS App Runner' },
    { target: 'AWS ECS Fargate', cost: 84.12, active: recommendedTarget === 'AWS ECS on Fargate' || recommendedTarget === 'AWS ECS' }
  ];

  const maxCost = Math.max(...options.map(o => o.cost));

  return (
    <div className="p-4 bg-white border border-slate-200/60 rounded-2xl space-y-3 shadow-sm">
      <div className="flex justify-between text-xs border-b border-slate-100 pb-2">
        <span className="font-bold text-slate-800">Compute Hosting Monthly Estimations</span>
        <span className="text-slate-400 text-[10px]">AWS Estimates</span>
      </div>
      <div className="space-y-3 pt-1">
        {options.map((opt, idx) => {
          const widthPct = (opt.cost / maxCost) * 100;
          return (
            <div key={idx} className="space-y-1">
              <div className="flex justify-between items-center text-[10px]">
                <span className={`font-semibold ${opt.active ? 'text-blue-600 font-extrabold' : 'text-slate-650'}`}>
                  {opt.target} {opt.active && '(Recommended)'}
                </span>
                <span className={`font-extrabold ${opt.active ? 'text-blue-600' : 'text-slate-500'}`}>
                  ${opt.cost.toFixed(2)}/mo
                </span>
              </div>
              <div className="w-full h-2.5 bg-slate-100 rounded-full overflow-hidden">
                <div 
                  className={`h-full rounded-full transition-all duration-1000 ${
                    opt.active 
                      ? 'bg-gradient-to-r from-blue-500 to-cyan-400' 
                      : 'bg-slate-250'
                  }`}
                  style={{ width: `${widthPct}%` }}
                />
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};

// Premium Interactive Diff & Patch Viewer Component
const PatchDiffViewer: React.FC<{ patch: string }> = ({ patch }) => {
  if (!patch) return null;
  
  const isDiff = patch.includes('\n-') || patch.includes('\n+') || patch.startsWith('---') || patch.startsWith('diff');
  
  if (isDiff) {
    const lines = patch.split('\n');
    return (
      <div className="border border-slate-200 rounded-xl overflow-hidden font-mono text-[10px] leading-relaxed shadow-inner bg-slate-50">
        <div className="bg-slate-100 px-4 py-2 text-[9px] font-extrabold text-slate-500 uppercase tracking-wider border-b border-slate-200">
          Git Patch Diff View
        </div>
        <div className="p-4 overflow-x-auto max-h-96">
          {lines.map((line, idx) => {
            let className = "text-slate-600 block";
            if (line.startsWith('+') && !line.startsWith('+++')) {
              className = "bg-emerald-50 text-emerald-700 px-1.5 border-l-2 border-emerald-500 block";
            } else if (line.startsWith('-') && !line.startsWith('---')) {
              className = "bg-rose-50 text-rose-700 px-1.5 border-l-2 border-rose-500 block line-through";
            }
            return <div key={idx} className={className}>{line}</div>;
          })}
        </div>
      </div>
    );
  }
  
  return (
    <div className="border border-slate-200 rounded-xl overflow-hidden font-mono text-[10px] leading-relaxed shadow-inner bg-slate-50">
      <div className="bg-slate-100 px-4 py-2 text-[9px] font-extrabold text-slate-500 uppercase tracking-wider border-b border-slate-200 flex justify-between items-center">
        <span>Suggested Code Solution</span>
      </div>
      <pre className="p-4 overflow-x-auto max-h-96 text-blue-600">
        <code>{patch}</code>
      </pre>
    </div>
  );
};

function App() {
  const { status, logs, result, error, startAnalysis, reset, taskId } = useAnalysisStream();
  const [activeTab, setActiveTab] = useState<string>('Dashboard');
  const [reportsSubTab, setReportsSubTab] = useState<string>('Overview');
  const [docSubTab, setDocSubTab] = useState<string>('readme');

  const [authenticated, setAuthenticated] = useState<boolean>(api.isAuthenticated());
  const [currentUser, setCurrentUser] = useState<any>(null);
  const [checkingAuth, setCheckingAuth] = useState<boolean>(api.isAuthenticated());

  // Settings states
  const [apiKey, setApiKey] = useState<string>(() => localStorage.getItem('cloudpilot_openai_key') || '');
  const [backendHealthy, setBackendHealthy] = useState<boolean | null>(null);

  // Theme states
  const [darkMode, setDarkMode] = useState<boolean>(() => {
    const cached = localStorage.getItem('cloudpilot_dark_mode');
    return cached === 'true';
  });

  useEffect(() => {
    const root = window.document.documentElement;
    if (darkMode) {
      root.classList.add('dark');
    } else {
      root.classList.remove('dark');
    }
    localStorage.setItem('cloudpilot_dark_mode', String(darkMode));
  }, [darkMode]);

  const handleToggleDark = () => {
    setDarkMode(!darkMode);
  };

  // New selected bug state
  const [selectedBugIndex, setSelectedBugIndex] = useState<number>(0);

  // Get time-aware greeting
  const getGreeting = () => {
    const hour = new Date().getHours();
    if (hour < 12) return 'Good Morning';
    if (hour < 18) return 'Good Afternoon';
    return 'Good Evening';
  };

  // Fetch backend health status
  const fetchHealth = async () => {
    try {
      const res = await fetch(`${api.getApiBaseUrl()}/health`);
      const data = await res.json();
      setBackendHealthy(data.status === 'healthy');
    } catch {
      setBackendHealthy(false);
    }
  };

  useEffect(() => {
    if (authenticated) {
      fetchHealth();
    }
  }, [authenticated]);

  useEffect(() => {
    const checkUser = async () => {
      if (api.isAuthenticated()) {
        try {
          const user = await api.getMe();
          setCurrentUser(user);
          setAuthenticated(true);
        } catch (err) {
          setAuthenticated(false);
          api.clearToken();
        } finally {
          setCheckingAuth(false);
        }
      } else {
        setCheckingAuth(false);
      }
    };
    checkUser();
  }, [authenticated]);

  // Reset page tabs when reset triggers
  useEffect(() => {
    if (status === 'completed' && result) {
      setActiveTab('Reports');
      setReportsSubTab('Overview');
      setSelectedBugIndex(0);
    }
  }, [status, result]);

  const handleLoginSuccess = () => {
    setAuthenticated(true);
  };

  const handleLogout = () => {
    api.clearToken();
    setAuthenticated(false);
    setCurrentUser(null);
    handleResetAll();
  };

  const handleResetAll = () => {
    reset();
    setActiveTab('Dashboard');
  };

  const handleSaveSettings = () => {
    localStorage.setItem('cloudpilot_openai_key', apiKey);
    alert('Settings saved successfully!');
  };

  if (checkingAuth) {
    return (
      <div className="min-h-screen bg-slate-50 text-slate-700 flex items-center justify-center gap-2">
        <Loader2 className="w-6 h-6 text-blue-500 animate-spin" />
        <span className="text-sm font-semibold text-slate-500">Verifying session...</span>
      </div>
    );
  }

  if (!authenticated) {
    return <Login onLoginSuccess={handleLoginSuccess} />;
  }

  // Calculate severity stats for Recharts
  const getSeverityChartData = () => {
    if (!result) return [];
    const bugs = result.bugs || [];
    const sec = result.security_issues || [];
    const perf = result.performance_issues || [];

    const stats = { Critical: 0, High: 0, Medium: 0, Low: 0 };

    bugs.forEach(() => {
      // Heuristic map bug confidence/score to severity
      stats.High += 1;
    });

    sec.forEach((s: any) => {
      const sev = s.severity as keyof typeof stats;
      if (stats[sev] !== undefined) stats[sev] += 1;
      else stats.High += 1;
    });

    perf.forEach((p: any) => {
      const sev = p.severity as keyof typeof stats;
      if (stats[sev] !== undefined) stats[sev] += 1;
      else stats.Medium += 1;
    });

    return [
      { name: 'Critical', value: stats.Critical, fill: '#ef4444' },
      { name: 'High', value: stats.High, fill: '#f97316' },
      { name: 'Medium', value: stats.Medium, fill: '#eab308' },
      { name: 'Low', value: stats.Low, fill: '#3b82f6' }
    ].filter(d => d.value > 0);
  };

  const severityData = getSeverityChartData();

  return (
    <div className="min-h-screen bg-[#f8fafc] text-slate-800 flex relative overflow-hidden">
      
      {/* Background Gradient splashes */}
      <div className="absolute top-1/4 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[550px] h-[550px] bg-gradient-to-tr from-blue-300/10 via-cyan-200/10 to-purple-300/10 rounded-full blur-3xl pointer-events-none" />
      <div className="absolute bottom-10 left-10 w-[300px] h-[300px] bg-emerald-500/5 rounded-full blur-3xl pointer-events-none" />

      {/* Sidebar Navigation */}
      <Sidebar 
        activeTab={activeTab} 
        onTabChange={setActiveTab} 
        resultLoaded={!!result} 
        currentUser={currentUser}
      />

      <div className="flex-1 flex flex-col pl-64 relative z-10">
        {/* Header - sync with active node status */}
        <Header 
          status={status} 
          userEmail={currentUser?.email}
          onLogout={handleLogout}
          darkMode={darkMode}
          onToggleDark={handleToggleDark}
        />

        {/* Inner Scrollable Workspace */}
        <main className="flex-1 mt-[80px] p-8 overflow-y-auto space-y-8 max-w-7xl w-full mx-auto">
          
          {/* Error Banner */}
          {error && (
            <div className="flex items-center gap-3 p-4 rounded-2xl bg-rose-50 border border-rose-200/60 text-rose-800 text-sm">
              <AlertCircle size={18} className="shrink-0 text-rose-600" />
              <div className="flex-1">
                <span className="font-bold">Error encountered: </span>
                {error}
              </div>
              <button 
                onClick={handleResetAll}
                className="px-3 py-1.5 rounded-xl bg-rose-100 hover:bg-rose-200 border border-rose-200 text-rose-800 font-semibold text-xs transition-all cursor-pointer shadow-sm"
              >
                Clear & Reset
              </button>
            </div>
          )}

          {/* ACTIVE ANALYZING / LOG TIMELINE */}
          {status === 'analyzing' && (
            <div className="space-y-8 animate-[fadeIn_0.3s_ease-out]">
              <UrlInputCard onAnalyze={startAnalysis} isLoading={true} />
              <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
                <div className="lg:col-span-2">
                  <AgentActivity logs={logs} status={status} />
                </div>
                <div>
                  <DeploymentStepsCard status={status} logs={logs} />
                </div>
              </div>
            </div>
          )}

          {/* PAGES ROUTER (IDLE / COMPLETED PHASES) */}
          {status !== 'analyzing' && (
            <AnimatePresence mode="wait">
              {/* TAB 1: DASHBOARD (HERO + SCANNER HOME) */}
              {activeTab === 'Dashboard' && (
                <motion.div 
                  initial={{ opacity: 0, y: 15 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -15 }}
                  transition={{ duration: 0.3 }}
                  className="space-y-8"
                >
                  {/* Hero Greetings Section */}
                  <div className="p-6 rounded-3xl bg-white border border-slate-200/60 relative overflow-hidden flex flex-col md:flex-row justify-between items-start md:items-center gap-4 shadow-sm">
                    <div className="absolute -right-4 -bottom-4 w-40 h-40 bg-gradient-to-tr from-blue-500/5 to-cyan-500/5 rounded-full blur-2xl pointer-events-none" />
                    <div className="space-y-1.5">
                      <h2 className="text-xl font-extrabold text-slate-800 flex items-center gap-2">
                        {getGreeting()}, {currentUser?.email?.split('@')[0] || 'Developer'}!
                        <Sparkles className="w-5 h-5 text-blue-500 animate-pulse" />
                      </h2>
                      <p className="text-xs text-slate-500 leading-relaxed">
                        System health status:{' '}
                        {backendHealthy === null
                          ? <span className="text-slate-450 font-bold">Checking...</span>
                          : backendHealthy
                          ? <span className="text-emerald-600 font-bold">All Systems Operational</span>
                          : <span className="text-rose-600 font-bold">Backend Offline</span>
                        }{' '}· Ready to index your next repository.
                      </p>
                    </div>
                    <div className={`flex items-center gap-2 px-3.5 py-1.5 rounded-xl border ${
                      backendHealthy === false
                        ? 'bg-rose-50 border-rose-200 text-rose-700'
                        : 'bg-emerald-50 border-emerald-200 text-emerald-700'
                    }`}>
                      <Activity className={`w-4 h-4 ${backendHealthy === false ? 'text-rose-600' : 'text-emerald-600 animate-pulse'}`} />
                      <span className="text-[10px] font-extrabold uppercase tracking-wider">
                        {backendHealthy === false ? 'Offline' : 'Connected'}
                      </span>
                    </div>
                  </div>

                  {/* Scan Input Grid */}
                  <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
                    <div className="lg:col-span-2 space-y-8">
                      <UrlInputCard onAnalyze={startAnalysis} isLoading={false} />
                      <RecentDeploymentsCard />
                    </div>

                    {/* Insights Card */}
                    <div className="glass-panel p-6 rounded-3xl border border-slate-200/60 flex flex-col justify-between h-full space-y-6" style={{ backgroundColor: 'rgba(255, 255, 255, 0.75)' }}>
                      <div className="space-y-4">
                        <div className="flex items-center gap-2 border-b border-slate-200/50 pb-3">
                          <Layers className="w-4 h-4 text-blue-500" />
                          <h4 className="text-xs font-extrabold text-slate-800 uppercase tracking-wider">Platform Analytics</h4>
                        </div>
                        <div className="space-y-3.5">
                          <div className="flex justify-between items-center text-xs">
                            <span className="text-slate-500 font-semibold">Active workspace</span>
                            <span className="font-extrabold text-slate-700">1 (Local Sandbox)</span>
                          </div>
                          <div className="flex justify-between items-center text-xs">
                            <span className="text-slate-500 font-semibold">V2 RAG indexes</span>
                            <span className="font-extrabold text-slate-700">Enabled</span>
                          </div>
                          <div className="flex justify-between items-center text-xs">
                            <span className="text-slate-500 font-semibold">Security checks tier</span>
                            <span className="px-2 py-0.5 rounded text-[9px] font-extrabold bg-blue-50 text-blue-600 border border-blue-200 uppercase tracking-wider">ENTERPRISE</span>
                          </div>
                        </div>
                      </div>
                      <div className="p-4 bg-blue-500/5 rounded-2xl border border-blue-100/60 text-[10px] text-slate-500 leading-relaxed">
                        To view your architectural details, bug diagnostics, security scanner, performance charts, and auto-generated deployment guides, input your repository URL above to execute the 12-agent pipeline.
                      </div>
                    </div>
                  </div>
                </motion.div>
              )}

              {/* TAB 2: REPORTS (TABBED SCAN REPORTS VIEW) */}
              {activeTab === 'Reports' && !result && (
                <div className="flex flex-col items-center justify-center py-24 space-y-4 text-center animate-[fadeIn_0.4s_ease-out]">
                  <div className="w-16 h-16 rounded-full bg-white border border-slate-200 flex items-center justify-center shadow-sm">
                    <FileCode2 className="w-8 h-8 text-slate-400" />
                  </div>
                  <h3 className="text-base font-bold text-slate-700">No Analysis Yet</h3>
                  <p className="text-xs text-slate-500 max-w-sm leading-relaxed">
                    Run a repository scan from the Dashboard tab first. Reports will appear here once the 12-agent AI pipeline completes.
                  </p>
                  <button
                    onClick={() => setActiveTab('Dashboard')}
                    className="px-5 py-2 rounded-xl bg-blue-600 hover:bg-blue-500 text-white text-xs font-bold cursor-pointer transition-all shadow-sm"
                  >
                    Go to Dashboard
                  </button>
                </div>
              )}

              {activeTab === 'Reports' && result && (
                <motion.div 
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  exit={{ opacity: 0 }}
                  transition={{ duration: 0.3 }}
                  className="space-y-8"
                >
                  {/* Tooling Header */}
                  <div className="flex justify-between items-center bg-white p-4 rounded-2xl border border-slate-200/60 flex-wrap gap-4 shadow-sm">
                    <div className="flex items-center gap-3">
                      <div className="w-8 h-8 rounded-lg bg-blue-500/10 border border-blue-200/50 flex items-center justify-center text-blue-500">
                        <FileCode2 size={16} />
                      </div>
                      <div>
                        <h3 className="text-xs font-extrabold text-slate-800">
                          Audited {result.repository_owner}/{result.repository_name}
                        </h3>
                        <p className="text-[9px] text-slate-450 mt-0.5">
                          Quality score: {result.health_score}/100 &middot; Recommending {result.recommendation?.target || 'AWS App Runner'}
                        </p>
                      </div>
                    </div>

                    <div className="flex items-center gap-2 flex-wrap">
                      <a 
                        href={`${api.getApiBaseUrl()}/analyze/export/pdf/${taskId}?token=${api.getToken() || localStorage.getItem('cloudpilot_jwt_token')}`}
                        target="_blank"
                        rel="noreferrer"
                        className="px-3 py-1.5 rounded-xl bg-blue-600 hover:bg-blue-500 text-white text-[10px] font-bold transition-all shadow-sm"
                      >
                        Export PDF
                      </a>
                      <a 
                        href={`${api.getApiBaseUrl()}/analyze/export/markdown/${taskId}?token=${api.getToken() || localStorage.getItem('cloudpilot_jwt_token')}`}
                        target="_blank"
                        rel="noreferrer"
                        className="px-3 py-1.5 rounded-xl bg-slate-100 hover:bg-slate-200 border border-slate-200 text-slate-700 text-[10px] font-bold transition-all shadow-sm"
                      >
                        Export Markdown
                      </a>
                      <a 
                        href={`${api.getApiBaseUrl()}/analyze/export/json/${taskId}?token=${api.getToken() || localStorage.getItem('cloudpilot_jwt_token')}`}
                        target="_blank"
                        rel="noreferrer"
                        className="px-3 py-1.5 rounded-xl bg-slate-100 hover:bg-slate-200 border border-slate-200 text-slate-700 text-[10px] font-bold transition-all shadow-sm"
                      >
                        Export JSON
                      </a>
                      <button 
                        onClick={handleResetAll}
                        className="px-3 py-1.5 rounded-xl bg-slate-50 hover:bg-slate-100 border border-slate-200 text-[10px] font-bold text-slate-600 flex items-center gap-1 transition-all cursor-pointer shadow-sm ml-2"
                      >
                        <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 1121.21 7.89M9 11l3-3-3-3" />
                        </svg>
                        Scan Different Repo
                      </button>
                    </div>
                  </div>

                  {/* Reports Sub-Tab Panel Selection Header */}
                  <div className="flex gap-1.5 flex-wrap border-b border-slate-200/80 pb-2">
                    {[
                      { id: 'Overview', label: 'Overview', icon: <Layers size={14} /> },
                      { id: 'Bugs', label: 'Bugs & Fixes', icon: <Bug size={14} /> },
                      { id: 'Security', label: 'Security Scanner', icon: <ShieldAlert size={14} /> },
                      { id: 'Performance', label: 'Performance Audit', icon: <Zap size={14} /> },
                      { id: 'Documentation', label: 'Documentation', icon: <BookOpen size={14} /> },
                      { id: 'DeploymentGuide', label: 'Deployment Guide', icon: <Terminal size={14} /> },
                      { id: 'Cost', label: 'Cost Analyzer', icon: <DollarSign size={14} /> }
                    ].map((tab) => {
                      const isActive = reportsSubTab === tab.id;
                      return (
                        <button
                          key={tab.id}
                          onClick={() => setReportsSubTab(tab.id)}
                          className={`px-4 py-2 rounded-xl text-xs font-bold transition-all cursor-pointer flex items-center gap-1.5 ${
                            isActive
                              ? 'bg-blue-600 text-white border border-blue-500 shadow-sm shadow-blue-500/10'
                              : 'text-slate-500 hover:text-slate-800 hover:bg-slate-100/50'
                          }`}
                        >
                          {tab.icon}
                          {tab.label}
                        </button>
                      );
                    })}
                  </div>

                  {/* SUB-TABS ROUTER */}
                  <div className="space-y-8">
                    
                    {/* Sub-Tab 1: Overview */}
                    {reportsSubTab === 'Overview' && (
                      <div className="space-y-8 animate-[fadeIn_0.3s_ease-out]">
                        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
                          
                          {/* Left stats cards */}
                          <div className="lg:col-span-1 space-y-6">
                            <div className="glass-panel p-6 rounded-2xl border border-slate-200/60 flex flex-col justify-center items-center shadow-sm text-center bg-white">
                              <span className="text-[10px] text-slate-400 font-bold uppercase tracking-wider">Repository Quality Score</span>
                              
                              {/* circular ring SVG health display */}
                              <div className="relative w-36 h-36 mt-4 flex items-center justify-center">
                                <svg viewBox="0 0 36 36" className="w-full h-full transform -rotate-90">
                                  <circle cx="18" cy="18" r="15.915" fill="none" stroke="#f1f5f9" strokeWidth="3" />
                                  <circle 
                                    cx="18" 
                                    cy="18" 
                                    r="15.915" 
                                    fill="none" 
                                    stroke="#3b82f6" 
                                    strokeWidth="3.2" 
                                    strokeDasharray={`${result.health_score} ${100 - result.health_score}`}
                                    strokeDashoffset="0"
                                    className="transition-all duration-1000"
                                    strokeLinecap="round"
                                  />
                                </svg>
                                <div className="absolute inset-0 flex flex-col items-center justify-center">
                                  <span className="text-3xl font-extrabold text-slate-800">{result.health_score}</span>
                                  <span className="text-[9px] text-slate-400 font-bold uppercase tracking-widest mt-0.5">/ 100</span>
                                </div>
                              </div>

                              <p className="text-[11px] text-slate-500 leading-relaxed mt-4">
                                Score calculated across bugs checklist, security vulnerability scanners, and performance benchmarks.
                              </p>
                            </div>

                            <div className="p-5 bg-white border border-slate-200/60 rounded-2xl space-y-4 shadow-sm">
                              <h4 className="text-xs font-extrabold text-slate-800 uppercase tracking-wider">Scan Profile</h4>
                              <div className="space-y-2.5 text-xs text-slate-600">
                                <div className="flex justify-between">
                                  <span>Framework:</span>
                                  <span className="font-bold text-slate-800">{result.deployment_guide?.framework_detected || result.metadata.frameworks[0] || 'Unknown'}</span>
                                </div>
                                <div className="flex justify-between">
                                  <span>Languages:</span>
                                  <span className="font-bold text-slate-800">{result.metadata.languages.map(l => l.name).slice(0, 2).join(', ')}</span>
                                </div>
                                <div className="flex justify-between">
                                  <span>Complexity:</span>
                                  <span className="font-bold text-slate-800">{result.metadata.complexity_index || 'Medium'}</span>
                                </div>
                                <div className="flex justify-between">
                                  <span>Technical Debt:</span>
                                  <span className="font-bold text-blue-600">{result.metadata.technical_debt_score || 40}/100</span>
                                </div>
                              </div>
                            </div>
                          </div>

                          {/* Right summary panel */}
                          <div className="lg:col-span-2 space-y-6">
                            <div className="p-6 bg-white border border-slate-200/60 rounded-2xl space-y-4 shadow-sm relative overflow-hidden">
                              <div className="absolute -right-4 -bottom-4 w-32 h-32 bg-blue-500/5 rounded-full blur-2xl" />
                              <h4 className="text-xs font-extrabold text-slate-800 uppercase tracking-wider flex items-center gap-2">
                                <Sparkles className="w-4.5 h-4.5 text-blue-600" />
                                Executive AI Summary
                              </h4>
                              <p className="text-xs text-slate-600 leading-relaxed">{result.ai_summary}</p>
                              
                              <div className="grid grid-cols-2 gap-4 pt-3 border-t border-slate-100">
                                <div className="p-3 bg-slate-50 rounded-xl">
                                  <span className="text-[9px] text-slate-400 font-extrabold uppercase tracking-wider block">Found Bugs</span>
                                  <span className="text-xl font-bold text-slate-700">{result.bugs?.length || 0} issues</span>
                                </div>
                                <div className="p-3 bg-slate-50 rounded-xl">
                                  <span className="text-[9px] text-slate-400 font-extrabold uppercase tracking-wider block">Security Warnings</span>
                                  <span className="text-xl font-bold text-slate-700">{result.security_issues?.length || 0} risks</span>
                                </div>
                              </div>
                            </div>

                            {/* Issue severity chart */}
                            {severityData.length > 0 && (
                              <div className="p-6 bg-white border border-slate-200/60 rounded-2xl space-y-4 shadow-sm">
                                <h4 className="text-xs font-extrabold text-slate-800 uppercase tracking-wider">Scan Warnings Breakdown</h4>
                                <div className="h-44 w-full">
                                  <ResponsiveContainer width="100%" height="100%">
                                    <BarChart data={severityData} margin={{ top: 10, right: 10, left: -25, bottom: 0 }}>
                                      <XAxis dataKey="name" stroke="#64748b" fontSize={10} tickLine={false} />
                                      <YAxis stroke="#64748b" fontSize={10} tickLine={false} />
                                      <Tooltip cursor={{ fill: 'rgba(15,23,42,0.03)' }} />
                                      <Bar dataKey="value" radius={[6, 6, 0, 0]}>
                                        {severityData.map((entry, index) => (
                                          <Cell key={`cell-${index}`} fill={entry.fill} />
                                        ))}
                                      </Bar>
                                    </BarChart>
                                  </ResponsiveContainer>
                                </div>
                              </div>
                            )}
                          </div>
                        </div>
                      </div>
                    )}

                    {/* Sub-Tab 2: Bugs & Fix Suggestions */}
                    {reportsSubTab === 'Bugs' && (
                      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8 items-start animate-[fadeIn_0.3s_ease-out]">
                        
                        {/* Bugs Checklist List */}
                        <div className="lg:col-span-1 space-y-3">
                          <div className="p-4 bg-white border border-slate-200/60 rounded-2xl shadow-sm">
                            <span className="text-[10px] text-slate-400 font-bold uppercase tracking-wider">Bugs Scanner ({result.bugs?.length || 0})</span>
                          </div>
                          {(result.bugs || []).map((bug, index) => {
                            const isSelected = selectedBugIndex === index;
                            return (
                              <button
                                key={index}
                                onClick={() => setSelectedBugIndex(index)}
                                className={`w-full text-left p-3.5 rounded-xl border flex justify-between items-center gap-3 transition-all cursor-pointer shadow-sm ${
                                  isSelected 
                                    ? 'bg-blue-600 text-white border-blue-500' 
                                    : 'bg-white border-slate-200/60 hover:bg-slate-50 text-slate-700'
                                }`}
                              >
                                <div className="min-w-0">
                                  <span className="text-xs font-bold block truncate">{bug.problem}</span>
                                  <span className={`text-[9px] mt-1 block uppercase font-extrabold ${isSelected ? 'text-blue-200' : 'text-blue-600'}`}>
                                    Confidence: {bug.confidence_score}%
                                  </span>
                                </div>
                                <ChevronRight size={14} className={isSelected ? 'text-blue-200' : 'text-slate-400'} />
                              </button>
                            );
                          })}
                        </div>

                        {/* Selected Bug Details Panel */}
                        <div className="lg:col-span-2">
                          {result.bugs && result.bugs[selectedBugIndex] ? (
                            <div className="bg-white border border-slate-200/60 rounded-2xl p-6 space-y-5 shadow-sm">
                              <div>
                                <span className="px-2.5 py-0.5 rounded text-[9px] font-extrabold bg-rose-50 text-rose-700 border border-rose-200 uppercase tracking-wider">
                                  BUG DIAGNOSTIC
                                </span>
                                <h3 className="text-base font-extrabold text-slate-800 mt-2">{result.bugs[selectedBugIndex].problem}</h3>
                              </div>

                              <div className="space-y-3.5 text-xs">
                                <div>
                                  <span className="font-bold text-slate-850 block">Reason:</span>
                                  <p className="text-slate-500 mt-1 leading-relaxed">{result.bugs[selectedBugIndex].reason}</p>
                                </div>
                                <div>
                                  <span className="font-bold text-slate-850 block">Impact:</span>
                                  <p className="text-slate-500 mt-1 leading-relaxed">{result.bugs[selectedBugIndex].impact}</p>
                                </div>
                                <div>
                                  <span className="font-bold text-slate-850 block">Affected Files:</span>
                                  <div className="flex flex-wrap gap-1.5 mt-1.5">
                                    {result.bugs[selectedBugIndex].affected_files.map((f: string, fIdx: number) => (
                                      <span key={fIdx} className="px-2 py-0.5 rounded bg-slate-100 text-slate-600 font-mono text-[10px]">
                                        {f}
                                      </span>
                                    ))}
                                  </div>
                                </div>
                                <div>
                                  <span className="font-bold text-slate-850 block">Suggested Solution:</span>
                                  <p className="text-slate-500 mt-1 leading-relaxed">{result.bugs[selectedBugIndex].suggested_solution}</p>
                                </div>
                                {(result.bugs[selectedBugIndex].patch || result.bugs[selectedBugIndex].example_code) && (
                                  <div>
                                    <span className="font-bold text-slate-850 block mb-2">Code Fix & Patch:</span>
                                    <PatchDiffViewer patch={result.bugs[selectedBugIndex].patch || result.bugs[selectedBugIndex].example_code} />
                                  </div>
                                )}
                              </div>
                            </div>
                          ) : (
                            <div className="p-12 text-center text-xs text-slate-500 bg-white border border-slate-200 rounded-2xl shadow-sm italic">
                              No bug reports details compiled.
                            </div>
                          )}
                        </div>

                      </div>
                    )}

                    {/* Sub-Tab 3: Security Scanner */}
                    {reportsSubTab === 'Security' && (
                      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8 items-start animate-[fadeIn_0.3s_ease-out]">
                        
                        {/* Left column: Security checklist */}
                        <div className="lg:col-span-1 space-y-6">
                          <div className="p-5 bg-white border border-slate-200/60 rounded-2xl space-y-4 shadow-sm">
                            <h4 className="text-xs font-extrabold text-slate-800 uppercase tracking-wider flex items-center gap-1.5">
                              <ShieldAlert className="w-4 h-4 text-orange-500" />
                              Security Audits Checklist
                            </h4>
                            <div className="space-y-3">
                              {result.checklist.map((item, idx) => (
                                <div key={idx} className="flex justify-between items-center text-xs p-2 bg-slate-50 rounded-lg">
                                  <span className="text-slate-655 font-medium">{item.label}</span>
                                  <span className={`px-2 py-0.5 rounded text-[8px] font-extrabold uppercase border ${
                                    item.status === 'checked' 
                                      ? 'bg-emerald-50 text-emerald-700 border-emerald-200' 
                                      : item.status === 'warning' 
                                      ? 'bg-amber-50 text-amber-700 border-amber-200' 
                                      : 'bg-rose-550/10 text-rose-700 border-rose-200'
                                  }`}>
                                    {item.status === 'checked' ? 'PASS' : item.status === 'warning' ? 'WARN' : 'FAIL'}
                                  </span>
                                </div>
                              ))}
                            </div>
                          </div>
                        </div>

                        {/* Right column: vulnerabilities details */}
                        <div className="lg:col-span-2 space-y-4">
                          {(result.security_issues || []).map((issue: any, index: number) => (
                            <div key={index} className="bg-white border border-slate-200/60 rounded-2xl p-5 space-y-4 shadow-sm relative overflow-hidden">
                              <div className="flex justify-between items-start flex-wrap gap-2">
                                <div>
                                  <span className={`px-2.5 py-0.5 rounded text-[8px] font-extrabold border uppercase tracking-wider ${
                                    issue.severity === 'Critical' || issue.severity === 'High' 
                                      ? 'bg-rose-50 text-rose-700 border-rose-200'
                                      : 'bg-amber-50 text-amber-700 border-amber-200'
                                  }`}>
                                    {issue.severity} Severity
                                  </span>
                                  <h4 className="text-sm font-bold text-slate-800 mt-2">{issue.issue_type} Warning</h4>
                                </div>
                              </div>

                              <div className="space-y-3 text-xs">
                                <div>
                                  <span className="font-bold text-slate-850 block">Description:</span>
                                  <p className="text-slate-500 mt-1 leading-relaxed">{issue.description}</p>
                                </div>
                                {issue.affected_files && issue.affected_files.length > 0 && (
                                  <div>
                                    <span className="font-bold text-slate-850 block">Affected Files:</span>
                                    <div className="flex flex-wrap gap-1 mt-1">
                                      {issue.affected_files.map((f: string, fIdx: number) => (
                                        <span key={fIdx} className="px-2 py-0.5 rounded bg-slate-100 text-slate-600 font-mono text-[9px]">
                                          {f}
                                        </span>
                                      ))}
                                    </div>
                                  </div>
                                )}
                                <div>
                                  <span className="font-bold text-slate-850 block">Suggested Fix:</span>
                                  <p className="text-slate-500 mt-1 leading-relaxed bg-blue-50/20 p-2.5 rounded-lg border border-blue-100/30">{issue.suggested_fix}</p>
                                </div>
                                {issue.patch && (
                                  <div className="mt-3">
                                    <span className="font-bold text-slate-850 block mb-2">Security Fix Patch:</span>
                                    <PatchDiffViewer patch={issue.patch} />
                                  </div>
                                )}
                              </div>
                            </div>
                          ))}
                          {(!result.security_issues || result.security_issues.length === 0) && (
                            <div className="p-12 text-center text-xs text-slate-500 bg-white border border-slate-200 rounded-2xl shadow-sm italic">
                              No security issues detected. Security score: 100/100.
                            </div>
                          )}
                        </div>

                      </div>
                    )}

                    {/* Sub-Tab 4: Performance Audit */}
                    {reportsSubTab === 'Performance' && (
                      <div className="space-y-4 max-w-4xl mx-auto animate-[fadeIn_0.3s_ease-out]">
                        {(result.performance_issues || []).map((issue: any, index: number) => (
                          <div key={index} className="bg-white border border-slate-200/60 rounded-2xl p-5 space-y-4 shadow-sm">
                            <div>
                              <span className="px-2.5 py-0.5 rounded text-[8px] font-extrabold bg-amber-50 text-amber-700 border border-amber-200 uppercase tracking-wider">
                                {issue.severity} Performance Impact
                              </span>
                              <h4 className="text-sm font-bold text-slate-800 mt-2">{issue.issue_type} Bottleneck</h4>
                            </div>

                            <div className="space-y-3 text-xs">
                              <div>
                                <span className="font-bold text-slate-850 block">Description:</span>
                                <p className="text-slate-500 mt-1 leading-relaxed">{issue.description}</p>
                              </div>
                              {issue.affected_files && issue.affected_files.length > 0 && (
                                <div>
                                  <span className="font-bold text-slate-850 block">Affected Files:</span>
                                  <div className="flex flex-wrap gap-1 mt-1">
                                    {issue.affected_files.map((f: string, fIdx: number) => (
                                      <span key={fIdx} className="px-2 py-0.5 rounded bg-slate-100 text-slate-655 font-mono text-[9px]">
                                        {f}
                                      </span>
                                    ))}
                                  </div>
                                </div>
                              )}
                              <div>
                                <span className="font-bold text-slate-850 block">Suggested Fix:</span>
                                <p className="text-slate-500 mt-1 leading-relaxed bg-cyan-50/10 p-2.5 rounded-lg border border-cyan-100/30">{issue.suggested_fix}</p>
                              </div>
                              {issue.patch && (
                                <div className="mt-3">
                                  <span className="font-bold text-slate-850 block mb-2">Performance Fix Patch:</span>
                                  <PatchDiffViewer patch={issue.patch} />
                                </div>
                              )}
                            </div>
                          </div>
                        ))}
                        {(!result.performance_issues || result.performance_issues.length === 0) && (
                          <div className="p-12 text-center text-xs text-slate-500 bg-white border border-slate-200 rounded-2xl shadow-sm italic">
                            No performance bottlenecks detected. App scales smoothly.
                          </div>
                        )}
                      </div>
                    )}

                    {/* Sub-Tab 5: Documentation Generator */}
                    {reportsSubTab === 'Documentation' && result.documentation && (
                      <div className="grid grid-cols-1 lg:grid-cols-4 gap-8 items-start animate-[fadeIn_0.3s_ease-out]">
                        
                        {/* Sub menu tabs */}
                        <div className="lg:col-span-1 space-y-2 bg-white p-3 rounded-2xl border border-slate-200/60 shadow-sm">
                          {[
                            { id: 'readme', label: 'README.md' },
                            { id: 'architecture', label: 'Architecture Docs' },
                            { id: 'folder_guide', label: 'Folder Guide' },
                            { id: 'api_docs', label: 'API Reference' },
                            { id: 'developer_docs', label: 'Developer Docs' },
                            { id: 'environment_variables', label: 'Env Configs' },
                            { id: 'setup_guide', label: 'Local Setup' }
                          ].map((docTab) => (
                            <button
                              key={docTab.id}
                              onClick={() => setDocSubTab(docTab.id)}
                              className={`w-full text-left px-3 py-2.5 rounded-xl text-xs font-bold transition-all cursor-pointer ${
                                docSubTab === docTab.id 
                                  ? 'bg-blue-50 text-blue-600 border border-blue-100' 
                                  : 'text-slate-550 hover:bg-slate-50 hover:text-slate-800'
                              }`}
                            >
                              {docTab.label}
                            </button>
                          ))}
                        </div>

                        {/* Content viewer */}
                        <div className="lg:col-span-3 bg-white border border-slate-200/60 rounded-2xl p-6 shadow-sm">
                          <div className="flex justify-between items-center border-b border-slate-100 pb-3.5 mb-4">
                            <span className="text-xs font-bold text-slate-800 uppercase tracking-wider">
                              Previewing {docSubTab.toUpperCase()} Documentation
                            </span>
                          </div>
                          
                          <pre className="text-xs text-slate-600 leading-relaxed font-mono whitespace-pre-wrap max-h-[500px] overflow-y-auto pr-2 bg-slate-50/50 p-4 rounded-xl border border-slate-200/60">
                            {result.documentation[docSubTab as keyof typeof result.documentation] || 'No content generated.'}
                          </pre>
                        </div>

                      </div>
                    )}

                    {/* Sub-Tab 6: Deployment Guide */}
                    {reportsSubTab === 'DeploymentGuide' && result.deployment_guide && (
                      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8 items-start animate-[fadeIn_0.3s_ease-out]">
                        
                        {/* Hosting recommendations */}
                        <div className="lg:col-span-1 space-y-6">
                          <div className="p-5 bg-white border border-slate-200/60 rounded-2xl space-y-3.5 shadow-sm">
                            <span className="text-[10px] text-slate-400 font-bold uppercase tracking-wider block">Hosting Recommendation</span>
                            <div className="flex items-center gap-3">
                              <div className="w-10 h-10 rounded-xl bg-blue-600/10 border border-blue-500/20 flex items-center justify-center text-blue-600">
                                <Terminal size={20} />
                              </div>
                              <div>
                                <h4 className="text-xs font-extrabold text-slate-800">
                                  {result.deployment_guide.hosting_recommendation}
                                </h4>
                                <span className="text-[8px] font-bold text-emerald-600 uppercase tracking-widest mt-1 block">
                                  Framework: {result.deployment_guide.framework_detected}
                                </span>
                              </div>
                            </div>
                          </div>

                          {/* required envs & secrets */}
                          <div className="p-5 bg-white border border-slate-200/60 rounded-2xl space-y-4 shadow-sm">
                            <div>
                              <span className="text-[10px] text-slate-400 font-bold uppercase tracking-wider block">Required Environment Variables</span>
                            </div>
                            <div className="space-y-2">
                              {result.deployment_guide.environment_variables.map((env: string, idx: number) => (
                                <span key={idx} className="inline-block px-2.5 py-1 rounded bg-slate-100 text-slate-655 font-mono text-[10px] mr-1.5 mb-1.5">
                                  {env}
                                </span>
                              ))}
                            </div>

                            <div className="pt-2 border-t border-slate-100">
                              <span className="text-[10px] text-slate-400 font-bold uppercase tracking-wider block mb-2">Required Secrets</span>
                              <div className="space-y-2">
                                {result.deployment_guide.required_secrets.map((sec: string, idx: number) => (
                                  <span key={idx} className="inline-block px-2.5 py-1 rounded bg-rose-50 text-rose-700 border border-rose-100 font-mono text-[10px] mr-1.5 mb-1.5">
                                    {sec}
                                  </span>
                                ))}
                              </div>
                            </div>
                          </div>
                        </div>

                        {/* Commands and Troubleshooting */}
                        <div className="lg:col-span-2 space-y-6">
                          <div className="bg-white border border-slate-200/60 rounded-2xl p-6 space-y-4 shadow-sm">
                            <h4 className="text-xs font-extrabold text-slate-800 uppercase tracking-wider">Build and Run Commands</h4>
                            <div className="space-y-2.5 text-xs">
                              {result.deployment_guide.build_commands.map((cmd: string, idx: number) => (
                                <div key={idx} className="p-3 bg-slate-50 border border-slate-200 rounded-xl font-mono text-blue-600 flex items-center justify-between">
                                  <span>{cmd}</span>
                                  <span className="text-[8px] bg-slate-200 text-slate-500 font-extrabold px-1.5 py-0.5 rounded">BUILD</span>
                                </div>
                              ))}
                            </div>
                          </div>

                          <div className="bg-white border border-slate-200/60 rounded-2xl p-6 space-y-4 shadow-sm">
                            <h4 className="text-xs font-extrabold text-slate-800 uppercase tracking-wider">Deployment Troubleshooting Guide</h4>
                            <div className="text-xs text-slate-600 leading-relaxed whitespace-pre-wrap p-4 bg-slate-50 rounded-xl border border-slate-200/60 font-mono">
                              {result.deployment_guide.troubleshooting_guide}
                            </div>
                          </div>

                          <div className="bg-white border border-slate-200/60 rounded-2xl p-6 space-y-3 shadow-sm">
                            <h4 className="text-xs font-extrabold text-slate-800 uppercase tracking-wider">Common Deployment Errors to Avoid</h4>
                            <ul className="list-disc pl-4 space-y-1.5 text-xs text-slate-500">
                              {result.deployment_guide.common_deployment_errors.map((err: string, idx: number) => (
                                <li key={idx}>{err}</li>
                              ))}
                            </ul>
                          </div>
                        </div>

                      </div>
                    )}

                    {/* Sub-Tab 7: Cost Analyzer */}
                    {reportsSubTab === 'Cost' && (
                      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8 items-start animate-[fadeIn_0.3s_ease-out]">
                        
                        <div className="lg:col-span-2 space-y-6">
                          <div className="p-6 bg-white border border-slate-200/60 rounded-2xl space-y-4 shadow-sm">
                            <h4 className="text-xs font-extrabold text-slate-800 uppercase tracking-wider">AWS Cost Estimations Detail</h4>
                            <p className="text-xs text-slate-500 leading-relaxed">
                              Estimations are calculated dynamically based on stack complexity:
                            </p>
                            <div className="p-4 bg-slate-50 border border-slate-200/60 rounded-xl text-xs text-slate-600 leading-relaxed font-mono whitespace-pre-wrap">
                              {result.cost_analysis || 'No detailed cost assumptions provided.'}
                            </div>
                          </div>
                        </div>

                        {/* Cost breakdown charts */}
                        <div className="space-y-6">
                          <div className="p-5 bg-white border border-slate-200/60 rounded-2xl space-y-4 shadow-sm">
                            <h4 className="text-xs font-extrabold text-slate-800 uppercase tracking-wider">Monthly Spend Breakdown</h4>
                            <CostDonut 
                              compute={result.recommendation?.cost_breakdown?.compute || 0}
                              database={result.recommendation?.cost_breakdown?.database || 0}
                              storage={result.recommendation?.cost_breakdown?.storage || 0}
                              transfer={result.recommendation?.cost_breakdown?.data_transfer || 0}
                            />
                          </div>

                          <ComputeCompareChart recommendedTarget={result.recommendation?.target || 'AWS App Runner'} />
                        </div>

                      </div>
                    )}

                  </div>
                </motion.div>
              )}

              {/* TAB 3: AI CONSULTANT */}
              {activeTab === 'AI consultant' && result && (
                <motion.div 
                  initial={{ opacity: 0, y: 15 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -15 }}
                  transition={{ duration: 0.3 }}
                  className="space-y-8"
                >
                  <AIConsultantChat result={result} taskId={taskId || ''} />
                </motion.div>
              )}

              {/* TAB 4: SETTINGS */}
              {activeTab === 'Settings' && (
                <motion.div 
                  initial={{ opacity: 0, y: 15 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -15 }}
                  transition={{ duration: 0.3 }}
                  className="p-6 bg-white rounded-3xl max-w-xl mx-auto border border-slate-200/60 space-y-6 shadow-sm"
                >
                  <div className="border-b border-slate-100 pb-4">
                    <h3 className="text-base font-bold text-slate-800">Settings & Key Override</h3>
                    <p className="text-[10px] text-slate-450 mt-1">Configure integrations keys for repository indexing.</p>
                  </div>

                  <div className="space-y-4">
                    <div className="flex flex-col gap-1.5">
                      <label className="text-xs font-semibold text-slate-600">OpenAI API Key</label>
                      <input 
                        type="password" 
                        value={apiKey} 
                        onChange={(e) => setApiKey(e.target.value)}
                        className="glass-input px-4 py-2.5 rounded-xl text-xs"
                        placeholder="sk-..."
                      />
                    </div>

                    <button 
                      className="w-full mt-4 py-2.5 rounded-xl btn-primary text-xs cursor-pointer" 
                      onClick={handleSaveSettings}
                    >
                      Save Settings
                    </button>
                  </div>
                </motion.div>
              )}
            </AnimatePresence>
          )}

        </main>
      </div>
    </div>
  );
}

export default App;
