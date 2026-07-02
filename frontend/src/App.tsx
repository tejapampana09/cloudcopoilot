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
import { AlertCircle, Loader2, ShieldAlert, Cpu, Sparkles } from 'lucide-react';
import { Login } from './components/Login';
import { api } from './services/api';

function App() {
  const { status, logs, result, error, startAnalysis, reset } = useAnalysisStream();
  const [viewMode, setViewMode] = useState<'analyzer' | 'infrastructure'>('analyzer');
  const [activeTab, setActiveTab] = useState<string>('Dashboard');
  const infra = useInfrastructureStream();

  const [authenticated, setAuthenticated] = useState<boolean>(api.isAuthenticated());
  const [currentUser, setCurrentUser] = useState<any>(null);
  const [checkingAuth, setCheckingAuth] = useState<boolean>(api.isAuthenticated());

  // Settings tab form states
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

  // Sync activeTab when new scan completes
  useEffect(() => {
    if (status === 'completed' && result) {
      setActiveTab('Dashboard');
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
      <div className="flex-1 pl-64 flex flex-col min-h-screen">
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

          {/* ACTIVE ANALYZING / LOG STREAMING TIMELINE */}
          {status === 'analyzing' && (
            <div className="space-y-8 animate-[fadeIn_0.3s_ease-out]">
              <UrlInputCard onAnalyze={startAnalysis} isLoading={true} />
              <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
                <div className="lg:col-span-2">
                  <AgentActivity logs={logs} status={status} />
                </div>
                <div>
                  <DeploymentStepsCard status={status} />
                </div>
              </div>
            </div>
          )}

          {/* PAGE ROUTER (IDLE / COMPLETED PHASES) */}
          {status !== 'analyzing' && (
            <>
              {/* TAB 1: DASHBOARD */}
              {activeTab === 'Dashboard' && (
                <>
                  {!result ? (
                    <div className="space-y-8 animate-[fadeIn_0.4s_ease-out]">
                      <UrlInputCard onAnalyze={startAnalysis} isLoading={false} />
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                        <RecentDeploymentsCard />
                        <div className="glass-panel p-6 rounded-2xl glow-blue flex flex-col justify-center items-center text-center space-y-4">
                          <div className="w-12 h-12 rounded-xl bg-blue-600/10 border border-blue-500/20 flex items-center justify-center text-blue-400">
                            <Cpu className="w-6 h-6" />
                          </div>
                          <h4 className="text-sm font-bold text-white">CloudPilot Architect</h4>
                          <p className="text-xs text-slate-400 max-w-sm leading-relaxed">
                            Paste any GitHub Repository URL. The evaluation engine runs a 10-point weighted decision matrix and builds detailed Terraform configurations.
                          </p>
                        </div>
                      </div>
                    </div>
                  ) : (
                    <div className="space-y-8 animate-[fadeIn_0.5s_ease-out]">
                      {/* Metric Summary Cards Bar */}
                      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                        <div className="glass-panel p-5 rounded-2xl flex items-center gap-4 glow-emerald">
                          <div className="relative w-14 h-14 flex items-center justify-center rounded-full border-2 border-emerald-500/20">
                            <span className="text-base font-extrabold text-emerald-400">{result.health_score}</span>
                            <div className="absolute inset-0 rounded-full border border-emerald-500 animate-pulse pointer-events-none" />
                          </div>
                          <div>
                            <span className="text-[10px] text-slate-500 font-bold uppercase tracking-wider block">Readiness Score</span>
                            <span className="text-sm font-bold text-slate-100 mt-0.5 block">Cloud-ready Setup</span>
                          </div>
                        </div>

                        <div className="glass-panel p-5 rounded-2xl flex items-center gap-4 glow-blue">
                          <div className="w-12 h-12 rounded-xl bg-blue-500/10 border border-blue-500/20 flex items-center justify-center text-blue-400">
                            <Cpu className="w-6 h-6" />
                          </div>
                          <div>
                            <span className="text-[10px] text-slate-500 font-bold uppercase tracking-wider block">Compute Target</span>
                            <span className="text-sm font-bold text-slate-100 mt-0.5 block">{result.recommendation.target}</span>
                          </div>
                        </div>

                        <div className="glass-panel p-5 rounded-2xl flex items-center gap-4 glow-cyan">
                          <div className="w-12 h-12 rounded-xl bg-cyan-500/10 border border-cyan-500/20 flex items-center justify-center text-cyan-400">
                            <Sparkles className="w-6 h-6 animate-pulse" />
                          </div>
                          <div>
                            <span className="text-[10px] text-slate-500 font-bold uppercase tracking-wider block">Decision Confidence</span>
                            <span className="text-sm font-bold text-slate-100 mt-0.5 block">{result.recommendation.confidence_score}%</span>
                          </div>
                        </div>
                      </div>

                      {/* Main Dashboard Cards */}
                      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
                        <div className="space-y-8">
                          <RepoAnalysisCard result={result} />
                          <ArchitectureCard 
                            recommendation={result.recommendation} 
                            databases={result.metadata.databases}
                          />
                        </div>
                        <div className="lg:col-span-2 space-y-8">
                          <SummaryCard 
                            summary={result.ai_summary} 
                            isAiEnhanced={!!result.ai_summary && (result.ai_summary.includes("OpenAI") || result.ai_summary.length > 150)} 
                          />
                          <RecentDeploymentsCard />
                        </div>
                      </div>
                    </div>
                  )}
                </>
              )}

              {/* TAB 2: NEW DEPLOYMENT */}
              {activeTab === 'New Deployment' && (
                <div className="space-y-8 animate-[fadeIn_0.4s_ease-out]">
                  <UrlInputCard onAnalyze={startAnalysis} isLoading={false} />
                  <RecentDeploymentsCard />
                </div>
              )}

              {/* TAB 3: DEPLOYMENTS (TERRAFORM CODE & BLUEPRINTS) */}
              {activeTab === 'Deployments' && result && (
                <div className="space-y-8 animate-[fadeIn_0.5s_ease-out]">
                  {viewMode === 'infrastructure' ? (
                    <>
                      {/* Live code preview explorer */}
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
                          Offload the configuration to our Multi-Agent builder. It compiles VPC, subnet, compute, databases, IAM profiles, and ALB routes directly from your repository's tech profile.
                        </p>
                      </div>
                      <button 
                        onClick={() => {
                          setViewMode('infrastructure');
                          infra.startGeneration(result.repository_url);
                        }}
                        className="px-6 py-2.5 rounded-xl bg-gradient-to-r from-blue-600 to-cyan-500 hover:from-blue-500 hover:to-cyan-400 text-white font-bold text-xs flex items-center gap-1.5 transition-all cursor-pointer shadow-md shadow-blue-500/15"
                      >
                        ⚡ Generate Infrastructure Code
                      </button>
                    </div>
                  )}
                </div>
              )}

              {/* TAB 4: AI CONSULTANT */}
              {activeTab === 'AI consultant' && result && (
                <div className="space-y-8 animate-[fadeIn_0.5s_ease-out]">
                  <AIConsultantChat result={result} />
                </div>
              )}

              {/* TAB 5: COST ANALYZER */}
              {activeTab === 'Cost Analyzer' && result && (
                <div className="space-y-8 animate-[fadeIn_0.5s_ease-out] max-w-4xl mx-auto">
                  <CostCard recommendation={result.recommendation} />
                  
                  {/* Detailed cost assumptions panel */}
                  {result.cost_analysis && (
                    <div className="glass-panel p-6 rounded-2xl border border-slate-800/40 text-xs text-slate-300 leading-relaxed">
                      {/* Cost assumptions text block */}
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
                          if (para.startsWith('- ') || para.startsWith('   - ')) {
                            return (
                              <ul key={pIdx} className="list-disc pl-5 space-y-1">
                                {para.split('\n').map((li: string, lIdx: number) => (
                                  <li key={lIdx}>{li.trim().replace('- ', '')}</li>
                                ))}
                              </ul>
                            );
                          }
                          return <p key={pIdx}>{para}</p>;
                        })}
                      </div>
                    </div>
                  )}
                </div>
              )}

              {/* TAB 6: SECURITY SCANNER */}
              {activeTab === 'Security Scanner' && result && (
                <div className="grid grid-cols-1 lg:grid-cols-3 gap-8 items-start animate-[fadeIn_0.5s_ease-out]">
                  <div className="lg:col-span-2">
                    <ChecklistCard checklist={result.checklist} />
                  </div>
                  <div className="space-y-6">
                    <div className="glass-panel p-6 rounded-2xl border border-slate-800/40 glow-orange">
                      <div className="flex items-center gap-2 mb-4">
                        <ShieldAlert className="text-amber-500 w-5 h-5" />
                        <h4 className="text-sm font-bold text-white">Security Vulnerability Review</h4>
                      </div>
                      <p className="text-xs text-slate-400 leading-relaxed mb-4">
                        We scan environment key mappings and repository files. Ensure all database client setups run inside isolated subnets, and credentials are configuration-driven.
                      </p>
                      <ul className="text-[11px] text-slate-300 space-y-2 pl-4 list-disc">
                        <li>VPC subnets configuration is recommended.</li>
                        <li>AWS Secrets Manager mapping suggested.</li>
                        <li>No hardcoded tokens committed.</li>
                      </ul>
                    </div>
                  </div>
                </div>
              )}

              {/* TAB 7: SETTINGS */}
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

export default App;
