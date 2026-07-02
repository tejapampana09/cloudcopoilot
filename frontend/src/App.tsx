import { useState, useEffect } from 'react';
import { Sidebar } from './components/Sidebar';
import { Header } from './components/Header';
import { UrlInputCard } from './components/UrlInputCard';
import { AgentActivity } from './components/AgentActivity';
import { RepoAnalysisCard } from './components/RepoAnalysisCard';
import { ArchitectureCard } from './components/ArchitectureCard';
import { CostCard } from './components/CostCard';
import { ChecklistCard } from './components/ChecklistCard';
import { SummaryCard } from './components/SummaryCard';
import { DeploymentStepsCard } from './components/DeploymentStepsCard';
import { RecentDeploymentsCard } from './components/RecentDeploymentsCard';
import { ProgressPanel } from './components/ProgressPanel';
import { InfrastructurePreview } from './components/InfrastructurePreview';
import { ValidationReportCard } from './components/ValidationReportCard';
import { AIConsultantChat } from './components/AIConsultantChat';
import { useAnalysisStream } from './hooks/useAnalysisStream';
import { useInfrastructureStream } from './hooks/useInfrastructureStream';
import { 
  AlertCircle, Loader2, ShieldAlert, Sparkles, 
  Activity, Layers, FileCode2,
  DollarSign, Zap
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
    <div className="flex flex-col md:flex-row items-center gap-6 p-4 bg-slate-950/20 border border-slate-900/60 rounded-xl">
      <div className="relative w-28 h-28 shrink-0">
        <svg viewBox="0 0 36 36" className="w-full h-full transform -rotate-90">
          <circle cx="18" cy="18" r="15.915" fill="none" stroke="#1e293b" strokeWidth="2.5" />
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
          <span className="text-[10px] text-slate-500 font-bold uppercase tracking-wider">Total</span>
          <span className="text-sm font-extrabold text-white">${total.toFixed(2)}</span>
        </div>
      </div>

      <div className="flex-1 space-y-2 w-full">
        {data.map((item, idx) => (
          <div key={idx} className="flex justify-between items-center text-[11px]">
            <div className="flex items-center gap-2">
              <div className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: item.color }} />
              <span className="text-slate-400 font-semibold">{item.label}</span>
            </div>
            <span className="font-extrabold text-slate-200">
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
    <div className="p-4 bg-slate-950/20 border border-slate-900/60 rounded-xl space-y-3">
      <div className="flex justify-between text-xs border-b border-slate-800/40 pb-2">
        <span className="font-bold text-white">Compute Options Monthly Estimations</span>
        <span className="text-slate-400 text-[10px]">Compare host pricing</span>
      </div>
      <div className="space-y-3 pt-1">
        {options.map((opt, idx) => {
          const widthPct = (opt.cost / maxCost) * 100;
          return (
            <div key={idx} className="space-y-1">
              <div className="flex justify-between items-center text-[10px]">
                <span className={`font-semibold ${opt.active ? 'text-blue-400 font-extrabold' : 'text-slate-400'}`}>
                  {opt.target} {opt.active && '(Recommended)'}
                </span>
                <span className={`font-extrabold ${opt.active ? 'text-blue-400' : 'text-slate-350'}`}>
                  ${opt.cost.toFixed(2)}/mo
                </span>
              </div>
              <div className="w-full h-2.5 bg-slate-900 rounded-full overflow-hidden">
                <div 
                  className={`h-full rounded-full transition-all duration-1000 ${
                    opt.active 
                      ? 'bg-gradient-to-r from-blue-500 to-cyan-400' 
                      : 'bg-slate-800'
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

function App() {
  const { status, logs, result, error, startAnalysis, reset, taskId } = useAnalysisStream();
  const [viewMode, setViewMode] = useState<'analyzer' | 'infrastructure'>('analyzer');
  const [activeTab, setActiveTab] = useState<string>('Dashboard');
  const [reportsSubTab, setReportsSubTab] = useState<string>('Overview');
  const infra = useInfrastructureStream();

  const [authenticated, setAuthenticated] = useState<boolean>(api.isAuthenticated());
  const [currentUser, setCurrentUser] = useState<any>(null);
  const [checkingAuth, setCheckingAuth] = useState<boolean>(api.isAuthenticated());

  // Settings states
  const [apiKey, setApiKey] = useState<string>('sk-or-v1-75189466205...');
  const [awsRegion, setAwsRegion] = useState<string>('ap-south-1');

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
    infra.reset();
    setViewMode('analyzer');
    setActiveTab('Dashboard');
  };

  if (checkingAuth) {
    return (
      <div className="min-h-screen bg-[#080C14] text-slate-100 flex items-center justify-center gap-2">
        <Loader2 className="w-6 h-6 text-blue-400 animate-spin" />
        <span className="text-sm font-semibold text-slate-400">Verifying session...</span>
      </div>
    );
  }

  if (!authenticated) {
    return <Login onLoginSuccess={handleLoginSuccess} />;
  }

  return (
    <div className="min-h-screen bg-[#080C14] text-slate-100 flex">
      {/* Sidebar Navigation */}
      <Sidebar 
        activeTab={activeTab} 
        onTabChange={setActiveTab} 
        resultLoaded={!!result} 
      />

      {/* Main Content Area */}
      <div className="flex-1 pl-64 flex flex-col min-h-screen animate-[fadeIn_0.3s_ease-out]">
        {/* Header - sync with active node status */}
        <Header 
          status={viewMode === 'infrastructure' ? (infra.status === 'generating' ? 'analyzing' : infra.status) : status} 
          userEmail={currentUser?.email}
          onLogout={handleLogout}
        />

        {/* Inner Scrollable Workspace */}
        <main className="flex-1 mt-[80px] p-8 overflow-y-auto space-y-8 max-w-7xl w-full mx-auto">
          
          {/* Error Banner */}
          {(error || infra.error) && (
            <div className="flex items-center gap-3 p-4 rounded-xl bg-rose-500/10 border border-rose-500/25 text-rose-300 text-sm">
              <AlertCircle size={18} className="shrink-0" />
              <div className="flex-1">
                <span className="font-bold">Error encountered: </span>
                {error || infra.error}
              </div>
              <button 
                onClick={handleResetAll}
                className="px-3 py-1.5 rounded-lg bg-rose-500/15 hover:bg-rose-500/25 border border-rose-500/20 text-rose-300 font-semibold text-xs transition-all cursor-pointer"
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
            <>
              {/* TAB 1: DASHBOARD (HERO + SCANNER HOME) */}
              {activeTab === 'Dashboard' && (
                <div className="space-y-8 animate-[fadeIn_0.4s_ease-out]">
                  {/* Hero Greetings Section */}
                  <div className="p-6 rounded-2xl bg-gradient-to-br from-slate-900 via-slate-950 to-slate-900 border border-slate-800/40 relative overflow-hidden flex flex-col md:flex-row justify-between items-start md:items-center gap-4 glow-blue">
                    <div className="space-y-1.5">
                      <h2 className="text-xl font-extrabold text-white flex items-center gap-2">
                        Good Morning, Srikar Reddy!
                        <Sparkles className="w-5 h-5 text-cyan-400 animate-pulse" />
                      </h2>
                      <p className="text-xs text-slate-400 leading-relaxed">
                        Cloud health status: <span className="text-emerald-400 font-bold">All Systems Operational</span> &middot; Scanning pipeline is ready.
                      </p>
                    </div>
                    <div className="flex items-center gap-2 px-3.5 py-1.5 rounded-lg bg-emerald-500/10 border border-emerald-500/15">
                      <Activity className="w-4 h-4 text-emerald-400 animate-pulse" />
                      <span className="text-[10px] text-emerald-400 font-extrabold uppercase tracking-wider">Health 100%</span>
                    </div>
                  </div>

                  {/* Scan Input Grid */}
                  <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
                    <div className="lg:col-span-2 space-y-8">
                      <UrlInputCard onAnalyze={startAnalysis} isLoading={false} />
                      <RecentDeploymentsCard />
                    </div>

                    {/* Insights Card */}
                    <div className="glass-panel p-6 rounded-2xl border border-slate-800/40 flex flex-col justify-between h-full space-y-6">
                      <div className="space-y-4">
                        <div className="flex items-center gap-2 border-b border-slate-850 pb-3">
                          <Layers className="w-4 h-4 text-blue-400" />
                          <h4 className="text-xs font-extrabold text-white uppercase tracking-wider">SaaS Insights</h4>
                        </div>
                        <div className="space-y-3.5">
                          <div className="flex justify-between items-center text-xs">
                            <span className="text-slate-400 font-semibold">Active Workspaces</span>
                            <span className="font-extrabold text-slate-200">1 (Local Sandbox)</span>
                          </div>
                          <div className="flex justify-between items-center text-xs">
                            <span className="text-slate-400 font-semibold">Recent Audits count</span>
                            <span className="font-extrabold text-slate-200">4 Completed</span>
                          </div>
                          <div className="flex justify-between items-center text-xs">
                            <span className="text-slate-400 font-semibold">Security Alerts status</span>
                            <span className="px-2 py-0.5 rounded text-[9px] bg-emerald-500/10 text-emerald-400 font-extrabold border border-emerald-500/20">CLEAN</span>
                          </div>
                        </div>
                      </div>
                      <div className="p-4 bg-blue-500/5 rounded-xl border border-blue-500/10 text-[10px] text-slate-400 leading-relaxed">
                        To view your architectural details, cost donut graphs, or download Terraform files, select the **Reports** or **AI consultant** tabs after running a repository scan.
                      </div>
                    </div>
                  </div>
                </div>
              )}

              {/* TAB 2: REPORTS (TABBED SCAN REPORTS VIEW) */}
              {activeTab === 'Reports' && result && (
                <div className="space-y-8 animate-[fadeIn_0.5s_ease-out]">
                  {/* Tooling Header */}
                  <div className="flex justify-between items-center bg-slate-900/45 p-4 rounded-xl border border-slate-800/40 flex-wrap gap-4">
                    <div className="flex items-center gap-3">
                      <div className="w-8 h-8 rounded-lg bg-blue-600/10 border border-blue-500/20 flex items-center justify-center text-blue-400">
                        <FileCode2 size={16} />
                      </div>
                      <div>
                        <h3 className="text-xs font-extrabold text-white">
                          Audits for {result.repository_owner}/{result.repository_name}
                        </h3>
                        <p className="text-[9px] text-slate-500 mt-0.5">
                          Readiness score: {result.health_score}/100 &middot; Recommending {result.recommendation.target}
                        </p>
                      </div>
                    </div>

                    <div className="flex items-center gap-3">
                      <button 
                        onClick={handleResetAll}
                        className="px-3.5 py-1.5 rounded-lg bg-slate-950 hover:bg-slate-900 border border-slate-850 hover:border-slate-800 text-[10px] font-bold text-slate-350 flex items-center gap-1.5 transition-all cursor-pointer shadow"
                      >
                        <RefreshCwIcon className="w-3 h-3" />
                        Scan Different
                      </button>
                    </div>
                  </div>

                  {/* Reports Sub-Tab Panel Selection Header */}
                  <div className="flex gap-2 flex-wrap border-b border-slate-850 pb-2">
                    {['Overview', 'Architecture', 'Security', 'Performance', 'AWS Topology', 'Cost Analyzer', 'IaC Deployment'].map((tab) => {
                      const isActive = reportsSubTab === tab;
                      return (
                        <button
                          key={tab}
                          onClick={() => setReportsSubTab(tab)}
                          className={`px-4 py-2 rounded-xl text-xs font-bold transition-all cursor-pointer ${
                            isActive
                              ? 'bg-blue-600/10 text-blue-400 border border-blue-500/20'
                              : 'text-slate-400 hover:text-slate-200 hover:bg-slate-900/40'
                          }`}
                        >
                          {tab}
                        </button>
                      );
                    })}
                  </div>

                  {/* SUB-TABS ROUTER */}
                  <div className="space-y-8">
                    {/* Sub-Tab 1: Overview */}
                    {reportsSubTab === 'Overview' && (
                      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
                        <div className="lg:col-span-1 space-y-8">
                          <RepoAnalysisCard result={result} />
                        </div>
                        <div className="lg:col-span-2 space-y-8">
                          <SummaryCard 
                            summary={result.ai_summary} 
                            isAiEnhanced={!!result.ai_summary && (result.ai_summary.includes("OpenAI") || result.ai_summary.length > 150)} 
                          />
                        </div>
                      </div>
                    )}

                    {/* Sub-Tab 2: Architecture */}
                    {reportsSubTab === 'Architecture' && (
                      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8 items-start">
                        <div className="lg:col-span-2">
                          <ArchitectureCard 
                            recommendation={result.recommendation} 
                            databases={result.metadata.databases}
                          />
                        </div>
                        <div className="glass-panel p-5 rounded-2xl border border-slate-800/40 text-xs text-slate-400 leading-relaxed space-y-3">
                          <div className="flex items-center gap-2 border-b border-slate-850 pb-2.5">
                            <Layers className="w-4 h-4 text-blue-400" />
                            <h4 className="font-extrabold text-white text-xs">Architectural Design Rules</h4>
                          </div>
                          <p>
                            We classify your repository dependencies to design decoupled containers. 
                          </p>
                          <ul className="list-disc pl-4 space-y-1.5 text-[11px] text-slate-350">
                            <li>App Runner fits standalone Docker-ready REST servers perfectly.</li>
                            <li>Multi-container Docker Compose config setups map to ECS Fargate.</li>
                          </ul>
                        </div>
                      </div>
                    )}

                    {/* Sub-Tab 3: Security */}
                    {reportsSubTab === 'Security' && (
                      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8 items-start">
                        <div className="lg:col-span-2">
                          <ChecklistCard checklist={result.checklist} />
                        </div>
                        <div className="glass-panel p-5 rounded-2xl border border-slate-800/40 text-xs text-slate-400 leading-relaxed space-y-4">
                          <div className="flex items-center gap-2 border-b border-slate-850 pb-2.5">
                            <ShieldAlert className="w-4.5 h-4.5 text-amber-500" />
                            <h4 className="font-extrabold text-white text-xs">Vulnerability Summary</h4>
                          </div>
                          <p>
                            Your security rating is calculated dynamically based on package structures.
                          </p>
                          <div className="p-3 bg-rose-500/5 border border-rose-500/10 rounded-xl space-y-2">
                            <span className="text-[10px] font-bold text-rose-300 block uppercase">Warnings Audit</span>
                            <p className="text-[11px] text-rose-200">
                              Verify that database setups map connection links configuration-driven, and local uploads are replaced with stateless Amazon S3 storage buckets.
                            </p>
                          </div>
                        </div>
                      </div>
                    )}

                    {/* Sub-Tab 4: Performance */}
                    {reportsSubTab === 'Performance' && (
                      <div className="glass-panel p-6 rounded-2xl border border-slate-800/40 space-y-6 max-w-3xl">
                        <div className="flex items-center gap-2 border-b border-slate-850 pb-3">
                          <Zap className="w-5 h-5 text-yellow-400 animate-pulse" />
                          <h4 className="text-sm font-bold text-white">Performance & Scaling Audit</h4>
                        </div>
                        <div className="space-y-4 text-xs text-slate-300 leading-relaxed">
                          <p>
                            During static repository scanning, we audited framework files and database packages to evaluate horizontally-scaling readiness.
                          </p>
                          
                          <div className="grid grid-cols-1 md:grid-cols-2 gap-6 pt-2">
                            <div className="p-4 bg-slate-950/20 border border-slate-900/60 rounded-xl space-y-2">
                              <span className="text-xs font-bold text-white block">Concurrency Bottlenecks</span>
                              <p className="text-[11px] text-slate-400">
                                {result.metadata.databases.includes('SQLite')
                                  ? "SQLite locks writes on scale. Recommend migrating databases to AWS RDS PostgreSQL or MySQL instances immediately."
                                  : "None detected. Using external relational/NoSQL clients."}
                              </p>
                            </div>
                            
                            <div className="p-4 bg-slate-950/20 border border-slate-900/60 rounded-xl space-y-2">
                              <span className="text-xs font-bold text-white block">Background Task Workers</span>
                              <p className="text-[11px] text-slate-400">
                                No heavy queue workers detected. For asynchronous/cron heavy operations, recommend adding Celery (Python) or BullMQ (Node) mapped to Amazon ElastiCache Redis.
                              </p>
                            </div>
                          </div>
                        </div>
                      </div>
                    )}

                    {/* Sub-Tab 5: AWS Topology */}
                    {reportsSubTab === 'AWS Topology' && (
                      <div className="glass-panel p-6 rounded-2xl border border-slate-800/40 space-y-6 max-w-3xl">
                        <div className="flex items-center gap-2.5 border-b border-slate-850 pb-3.5">
                          <div className="w-8 h-8 rounded-lg bg-orange-500/10 border border-orange-500/20 flex items-center justify-center text-orange-400">
                            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
                            </svg>
                          </div>
                          <div>
                            <h4 className="text-sm font-bold text-white">Recommended AWS Architecture Justification</h4>
                            <p className="text-[10px] text-slate-500">DYNAMIC WEIGHTED MATRIX RATIONALE</p>
                          </div>
                        </div>

                        <div className="space-y-4 text-xs text-slate-300 leading-relaxed">
                          <div className="p-4 bg-slate-950/30 border border-slate-850 rounded-xl">
                            <p>{result.recommendation.why}</p>
                          </div>

                          <div className="space-y-2">
                            <span className="font-bold text-white">AWS Integration Checklist:</span>
                            <ul className="list-decimal pl-5 space-y-1.5 text-[11px] text-slate-400">
                              <li>Set up Amazon VPC networking with 2 public & 2 private subnets across 2 Availability Zones.</li>
                              <li>Provision Amazon RDS {result.metadata.databases[0] || 'relational'} clusters if stateful storage is needed.</li>
                              <li>Establish AWS Secrets Manager mappings for credentials injection on load.</li>
                            </ul>
                          </div>
                        </div>
                      </div>
                    )}

                    {/* Sub-Tab 6: Cost Analyzer */}
                    {reportsSubTab === 'Cost Analyzer' && (
                      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8 items-start">
                        <div className="lg:col-span-2 space-y-8">
                          <CostCard recommendation={result.recommendation} />
                          {result.cost_analysis && (
                            <div className="glass-panel p-6 rounded-2xl border border-slate-800/40 text-xs text-slate-350 leading-relaxed">
                              <div className="space-y-3">
                                {result.cost_analysis.split('\n\n').map((para: string, pIdx: number) => {
                                  if (para.startsWith('### ')) {
                                    return <h4 key={pIdx} className="text-sm font-bold text-white mt-4">{para.replace('### ', '')}</h4>;
                                  }
                                  if (para.startsWith('#### ')) {
                                    return <h5 key={pIdx} className="font-semibold text-slate-200 text-xs mt-3">{para.replace('#### ', '')}</h5>;
                                  }
                                  if (para.startsWith('> ')) {
                                    return (
                                      <blockquote key={pIdx} className="border-l-2 border-blue-500 pl-4 text-slate-400 italic bg-blue-500/5 py-1 pr-2 rounded">
                                        {para.replace('> [!NOTE]\n> ', '').replace('> ', '')}
                                      </blockquote>
                                    );
                                  }
                                  return <p key={pIdx}>{para}</p>;
                                })}
                              </div>
                            </div>
                          )}
                        </div>

                        {/* Cost Charts column */}
                        <div className="space-y-6">
                          <div className="glass-panel p-5 rounded-2xl border border-slate-800/40 space-y-4">
                            <div className="flex items-center gap-2 border-b border-slate-850 pb-2.5">
                              <DollarSign className="w-4.5 h-4.5 text-blue-400" />
                              <h4 className="font-extrabold text-white text-xs uppercase tracking-wider">Pricing Breakdown</h4>
                            </div>
                            <CostDonut 
                              compute={result.recommendation.cost_breakdown.compute}
                              database={result.recommendation.cost_breakdown.database}
                              storage={result.recommendation.cost_breakdown.storage}
                              transfer={result.recommendation.cost_breakdown.data_transfer}
                            />
                          </div>

                          <ComputeCompareChart 
                            recommendedTarget={result.recommendation.target}
                          />
                        </div>
                      </div>
                    )}

                    {/* Sub-Tab 7: IaC Deployment */}
                    {reportsSubTab === 'IaC Deployment' && (
                      <div className="space-y-8">
                        {viewMode === 'infrastructure' ? (
                          <>
                            <ProgressPanel 
                              logs={infra.logs} 
                              progress={infra.progress} 
                              status={infra.status} 
                            />

                            {infra.status === 'completed' && (
                              <div className="grid grid-cols-1 lg:grid-cols-3 gap-8 items-start">
                                <div className="lg:col-span-2">
                                  <InfrastructurePreview 
                                    files={infra.generatedFiles} 
                                    downloadUrl={infra.downloadUrl} 
                                  />
                                </div>
                                <div>
                                  <ValidationReportCard 
                                    score={infra.validationScore} 
                                    results={infra.validationResults} 
                                  />
                                </div>
                              </div>
                            )}
                          </>
                        ) : (
                          <div className="glass-panel p-8 rounded-2xl text-center flex flex-col justify-center items-center space-y-6 max-w-xl mx-auto glow-blue">
                            <div className="w-16 h-16 rounded-2xl bg-blue-600/10 border border-blue-500/20 flex items-center justify-center text-blue-400">
                              <svg className="w-8 h-8" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 9l3 3-3 3m5 0h3M5 20h14a2 2 0 002-2V6a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
                              </svg>
                            </div>
                            <div>
                              <h3 className="text-base font-bold text-white">Generate Terraform IaC Blueprints</h3>
                              <p className="text-xs text-slate-400 mt-2 leading-relaxed">
                                Trigger the Multi-Agent packaging node to construct VPC, private network, subnet, compute, and RDS database Terraform .tf configurations for direct zip download.
                              </p>
                            </div>
                            <button 
                              onClick={() => {
                                setViewMode('infrastructure');
                                infra.startGeneration(result.repository_url);
                              }}
                              className="px-6 py-2.5 rounded-xl bg-gradient-to-r from-blue-600 to-cyan-500 hover:from-blue-500 hover:to-cyan-400 text-white font-bold text-xs flex items-center gap-1.5 transition-all cursor-pointer shadow-md shadow-blue-500/15"
                            >
                              ⚡ Generate Terraform Configs
                            </button>
                          </div>
                        )}
                      </div>
                    )}

                  </div>
                </div>
              )}

              {/* TAB 3: AI CONSULTANT */}
              {activeTab === 'AI consultant' && result && (
                <div className="space-y-8 animate-[fadeIn_0.5s_ease-out]">
                  <AIConsultantChat result={result} taskId={taskId || ''} />
                </div>
              )}

              {/* TAB 4: SETTINGS */}
              {activeTab === 'Settings' && (
                <div className="glass-panel p-6 rounded-2xl max-w-xl mx-auto border border-slate-800/40 space-y-6 animate-[fadeIn_0.4s_ease-out]">
                  <div className="border-b border-slate-800/40 pb-4">
                    <h3 className="text-base font-bold text-white">Settings & Credentials</h3>
                    <p className="text-[10px] text-slate-500 mt-1">Configure API integrations and credentials overrides.</p>
                  </div>

                  <div className="space-y-4">
                    <div className="flex flex-col gap-1.5">
                      <label className="text-xs font-semibold text-slate-400">OpenAI API Key</label>
                      <input 
                        type="password" 
                        value={apiKey} 
                        onChange={(e) => setApiKey(e.target.value)}
                        className="glass-input px-4 py-2 rounded-xl text-xs"
                      />
                    </div>

                    <div className="flex flex-col gap-1.5">
                      <label className="text-xs font-semibold text-slate-400">Default AWS Deployment Region</label>
                      <select 
                        value={awsRegion} 
                        onChange={(e) => setAwsRegion(e.target.value)}
                        className="glass-input px-4 py-2 rounded-xl text-xs bg-slate-900 border border-slate-800"
                      >
                        <option value="us-east-1">us-east-1 (N. Virginia)</option>
                        <option value="us-west-2">us-west-2 (Oregon)</option>
                        <option value="eu-west-1">eu-west-1 (Ireland)</option>
                        <option value="ap-south-1">ap-south-1 (Mumbai)</option>
                      </select>
                    </div>

                    <button className="w-full mt-4 py-2.5 rounded-xl btn-primary text-xs cursor-pointer">
                      Save Settings
                    </button>
                  </div>
                </div>
              )}
            </>
          )}

        </main>
      </div>
    </div>
  );
}

// Simple local RefreshCw SVG placeholder icon to avoid any import issues
const RefreshCwIcon = ({ className }: { className?: string }) => (
  <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 1121.21 7.89M9 11l3-3-3-3" />
  </svg>
);

export default App;
