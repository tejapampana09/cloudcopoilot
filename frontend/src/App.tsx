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
import { useAnalysisStream } from './hooks/useAnalysisStream';
import { useInfrastructureStream } from './hooks/useInfrastructureStream';
import { RefreshCw, AlertCircle, ArrowLeft, Loader2 } from 'lucide-react';
import { Login } from './components/Login';
import { api } from './services/api';

function App() {
  const { status, logs, result, error, startAnalysis, reset } = useAnalysisStream();
  const [viewMode, setViewMode] = useState<'analyzer' | 'infrastructure'>('analyzer');
  const infra = useInfrastructureStream();

  const [authenticated, setAuthenticated] = useState<boolean>(api.isAuthenticated());
  const [currentUser, setCurrentUser] = useState<any>(null);
  const [checkingAuth, setCheckingAuth] = useState<boolean>(api.isAuthenticated());

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
  };

  if (checkingAuth) {
    return (
      <div className="min-h-screen bg-[#080C14] text-slate-100 flex items-center justify-center gap-2">
        <Loader2 className="w-6 h-6 text-violet-400 animate-spin" />
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
      <Sidebar />

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

          {/* VIEW MODE 1: REPOSITORY ANALYZER */}
          {viewMode === 'analyzer' && (
            <>
              {/* IDLE STATE */}
              {status === 'idle' && (
                <div className="space-y-8 animate-[fadeIn_0.4s_ease-out]">
                  <UrlInputCard onAnalyze={startAnalysis} isLoading={false} />
                  
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                    <RecentDeploymentsCard />
                    <div className="glass-panel p-6 rounded-2xl glow-blue flex flex-col justify-center items-center text-center space-y-4">
                      <div className="w-12 h-12 rounded-xl bg-blue-600/10 border border-blue-500/20 flex items-center justify-center text-blue-400">
                        <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364.364l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
                        </svg>
                      </div>
                      <h4 className="text-sm font-bold text-white">How it works</h4>
                      <p className="text-xs text-slate-400 max-w-sm leading-relaxed">
                        Paste any public GitHub URL. Our agent checks package metadata, repository structures, and infrastructure files, generating deployment blueprints for AWS automatically.
                      </p>
                    </div>
                  </div>
                </div>
              )}

              {/* ANALYZING STATE */}
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

              {/* COMPLETED STATE */}
              {status === 'completed' && result && (
                <div className="space-y-8 animate-[fadeIn_0.5s_ease-out]">
                  {/* Toolbar Header */}
                  <div className="flex justify-between items-center bg-slate-900/40 p-4 rounded-xl border border-slate-800/40 flex-wrap gap-4">
                    <div className="flex items-center gap-3">
                      <div className="w-8 h-8 rounded-lg bg-blue-600/10 border border-blue-500/20 flex items-center justify-center text-blue-400">
                        <svg className="w-5 h-5" viewBox="0 0 24 24" fill="currentColor">
                          <path d="M12 2C6.477 2 2 6.477 2 12s4.477 10 10 10 10-4.477 10-10S17.523 2 12 2zm1 15h-2v-6h2v6zm0-8h-2V7h2v2z" />
                        </svg>
                      </div>
                      <div>
                        <h3 className="text-sm font-bold text-white">
                          Analysis for {result.repository_owner}/{result.repository_name}
                        </h3>
                        <p className="text-[10px] text-slate-400 mt-0.5">
                          Completed on {new Date(result.analysis_time).toLocaleDateString()} at {new Date(result.analysis_time).toLocaleTimeString()}
                        </p>
                      </div>
                    </div>

                    <div className="flex items-center gap-3">
                      <button 
                        onClick={reset}
                        className="px-4 py-2 rounded-lg bg-slate-900 hover:bg-slate-800 border border-slate-800 hover:border-slate-700 text-xs font-semibold text-slate-300 flex items-center gap-1.5 transition-all cursor-pointer shadow-md"
                      >
                        <RefreshCw size={13} />
                        Analyze Another
                      </button>
                      <button 
                        onClick={() => {
                          setViewMode('infrastructure');
                          infra.startGeneration(result.repository_url);
                        }}
                        className="px-4 py-2 rounded-lg bg-gradient-to-r from-blue-600 to-cyan-500 hover:from-blue-500 hover:to-cyan-400 text-white font-bold text-xs flex items-center gap-1.5 transition-all cursor-pointer shadow-md shadow-blue-500/10"
                      >
                        ⚡ Generate Infrastructure
                      </button>
                    </div>
                  </div>

                  {/* Main Analysis Grid */}
                  <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
                    <div className="space-y-8">
                      <RepoAnalysisCard result={result} />
                      <CostCard recommendation={result.recommendation} />
                    </div>

                    <div className="space-y-8">
                      <ArchitectureCard 
                        recommendation={result.recommendation} 
                        databases={result.metadata.databases}
                      />
                      <DeploymentStepsCard status={status} />
                    </div>

                    <div className="space-y-8">
                      <SummaryCard 
                        summary={result.ai_summary} 
                        isAiEnhanced={!!result.ai_summary && (result.ai_summary.includes("OpenAI") || result.ai_summary.length > 150)} 
                      />
                      <ChecklistCard checklist={result.checklist} />
                    </div>
                  </div>
                </div>
              )}
            </>
          )}

          {/* VIEW MODE 2: AI INFRASTRUCTURE GENERATOR */}
          {viewMode === 'infrastructure' && (
            <div className="space-y-8 animate-[fadeIn_0.5s_ease-out]">
              {/* Toolbar Header */}
              <div className="flex justify-between items-center bg-slate-900/40 p-4 rounded-xl border border-slate-800/40 flex-wrap gap-4">
                <div className="flex items-center gap-3.5">
                  <button
                    onClick={() => {
                      infra.reset();
                      setViewMode('analyzer');
                    }}
                    className="p-2 rounded-lg bg-slate-900 hover:bg-slate-850 border border-slate-850 text-slate-400 hover:text-white transition-all cursor-pointer"
                  >
                    <ArrowLeft size={14} />
                  </button>
                  <div>
                    <h3 className="text-sm font-bold text-white flex items-center gap-2">
                      ⚡ AI Infrastructure Generator
                    </h3>
                    <p className="text-[10px] text-slate-400 mt-0.5">
                      Target: {result?.recommendation.target || 'AWS Compute'} &middot; Detected Stack: {infra.detectedFramework || 'Auto'}
                    </p>
                  </div>
                </div>

                {infra.status === 'completed' && (
                  <button 
                    onClick={handleResetAll}
                    className="px-4 py-2 rounded-lg bg-slate-900 hover:bg-slate-850 border border-slate-800 hover:border-slate-700 text-xs font-semibold text-slate-300 flex items-center gap-1.5 transition-all cursor-pointer shadow-md"
                  >
                    <RefreshCw size={13} />
                    Reset Pipeline
                  </button>
                )}
              </div>

              {/* Progress and Live Agent Logger */}
              <ProgressPanel 
                logs={infra.logs} 
                progress={infra.progress} 
                status={infra.status} 
              />

              {/* Final Generated Explorer & Validation Auditing Code */}
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
            </div>
          )}
        </main>
      </div>
    </div>
  );
}

export default App;
