import React from 'react';
import { Loader2, CheckCircle2, Circle, HelpCircle } from 'lucide-react';
import type { AgentLog } from '../types';

interface DeploymentStepsCardProps {
  status: 'idle' | 'analyzing' | 'completed' | 'failed';
  logs?: AgentLog[];
}

export const DeploymentStepsCard: React.FC<DeploymentStepsCardProps> = ({ status, logs = [] }) => {
  // Helper to determine status of specific agents based on log streams
  const getAgentStatus = (agentName: string) => {
    if (status === 'completed') return 'completed';
    if (status === 'idle') return 'pending';
    
    // Check logs for specific agent activity
    const agentLogs = logs.filter(l => l.agent === agentName);
    if (agentLogs.length === 0) return 'pending';
    
    const isCompleted = agentLogs.some(l => l.status === 'completed');
    if (isCompleted) return 'completed';
    
    const isFailed = agentLogs.some(l => l.status === 'failed');
    if (isFailed) return 'failed';
    
    const isInProgress = agentLogs.some(l => l.status === 'in_progress');
    if (isInProgress) return 'in_progress';
    
    return 'pending';
  };

  // Map agents to friendly visual pipeline items
  const agentTimeline = [
    {
      id: 1,
      label: 'Repository Agent',
      desc: 'Clones repository & detects frameworks',
      status: getAgentStatus('Repository Analyzer')
    },
    {
      id: 2,
      label: 'Architecture Agent',
      desc: 'Parses codebase dependency boundaries',
      status: getAgentStatus('Architecture Agent')
    },
    {
      id: 3,
      label: 'Security Agent',
      desc: 'Audits credentials leaks & JWT issues',
      status: getAgentStatus('Security Agent')
    },
    {
      id: 4,
      label: 'Performance Agent',
      desc: 'Audits component sizes & repeated pings',
      status: getAgentStatus('Performance Agent')
    },
    {
      id: 5,
      label: 'Cloud Architect Agent',
      desc: 'Runs weighted bug scan checklists',
      status: getAgentStatus('Cloud Architect Agent')
    },
    {
      id: 6,
      label: 'Infrastructure Agent',
      desc: 'Generates repository code indexations',
      status: getAgentStatus('Infrastructure Agent')
    },
    {
      id: 7,
      label: 'Deploy Agent',
      desc: 'Compiles hosting guide recommendations',
      status: getAgentStatus('Deployment Agent')
    },
    {
      id: 8,
      label: 'Monitoring Agent',
      desc: 'Configures health alarms & logging metrics',
      status: getAgentStatus('Monitoring Agent')
    },
    {
      id: 9,
      label: 'Cost Agent',
      desc: 'Identifies hosting spend optimization steps',
      status: getAgentStatus('Cost Optimization Agent')
    },
    {
      id: 10,
      label: 'Executive Agent',
      desc: 'Assembles summary reports & readiness scores',
      status: getAgentStatus('Monitoring Agent')
    }
  ];

  return (
    <div className="glass-panel p-6 rounded-2xl glow-blue flex flex-col h-full" style={{ backgroundColor: 'rgba(255, 255, 255, 0.75)' }}>
      {/* Header */}
      <div className="flex justify-between items-center mb-6">
        <h4 className="text-sm font-bold text-slate-800 flex items-center gap-2">
          <svg className="w-5 h-5 text-blue-550" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
          </svg>
          Orchestration Timeline
        </h4>
        <span className="text-[9px] bg-blue-500/10 text-blue-600 font-bold px-2 py-0.5 rounded border border-blue-200/50 uppercase tracking-wider">
          Multi-Agent
        </span>
      </div>

      {/* Steps List */}
      <div className="flex-1 space-y-4 max-h-[480px] overflow-y-auto pr-1">
        {agentTimeline.map((step) => (
          <div key={step.id} className="flex items-start justify-between gap-4">
            <div className="flex items-start gap-3">
              <div className={`w-6 h-6 rounded-full flex items-center justify-center text-[10px] font-bold shrink-0 mt-0.5 border ${
                step.status === 'completed'
                  ? 'bg-emerald-50 text-emerald-600 border-emerald-200'
                  : step.status === 'in_progress'
                  ? 'bg-blue-50 text-blue-600 border-blue-200 animate-pulse'
                  : step.status === 'failed'
                  ? 'bg-rose-50 text-rose-600 border-rose-200'
                  : 'bg-slate-100 text-slate-400 border-slate-200'
              }`}>
                {step.id}
              </div>
              <div>
                <span className={`text-xs font-bold block ${
                  step.status === 'completed'
                    ? 'text-slate-700'
                    : step.status === 'in_progress'
                    ? 'text-blue-600'
                    : 'text-slate-400'
                }`}>
                  {step.label}
                </span>
                <span className="text-[10px] text-slate-500 mt-0.5 block leading-relaxed">{step.desc}</span>
              </div>
            </div>
            
            {/* Status Icon */}
            <div className="shrink-0 mt-1">
              {step.status === 'completed' && (
                <CheckCircle2 className="w-4 h-4 text-emerald-500 fill-emerald-50" />
              )}
              {step.status === 'in_progress' && (
                <Loader2 className="w-4 h-4 text-blue-500 animate-spin" />
              )}
              {step.status === 'failed' && (
                <HelpCircle className="w-4 h-4 text-rose-500" />
              )}
              {step.status === 'pending' && (
                <Circle className="w-4 h-4 text-slate-350" />
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
