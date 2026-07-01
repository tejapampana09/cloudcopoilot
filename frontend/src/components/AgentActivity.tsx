import React from 'react';
import { Loader2, CheckCircle2, Circle, AlertCircle } from 'lucide-react';
import type { AgentLog } from '../types';

interface AgentActivityProps {
  logs: AgentLog[];
  status: 'idle' | 'analyzing' | 'completed' | 'failed';
}

export const AgentActivity: React.FC<AgentActivityProps> = ({ logs, status }) => {
  // Predefined agents that we display in order
  const agentNames = [
    'Planner Agent',
    'Repository Analyzer',
    'Infrastructure Agent',
    'Deployment Agent',
    'Monitoring Agent'
  ] as const;

  // Helper to map log details for each agent
  const getAgentState = (agentName: typeof agentNames[number]) => {
    const log = logs.find((l) => l.agent === agentName);
    
    if (log) {
      return {
        message: log.message,
        status: log.status,
        timestamp: log.timestamp
      };
    }

    // Default waiting states
    return {
      message: 'Waiting...',
      status: 'pending' as const,
      timestamp: ''
    };
  };

  return (
    <div className="glass-panel p-6 rounded-2xl glow-cyan flex flex-col h-full">
      {/* Card Header */}
      <div className="flex justify-between items-center mb-6">
        <h4 className="text-base font-bold text-white flex items-center gap-2">
          <svg className="w-5 h-5 text-cyan-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
          </svg>
          AI Agent Activity
        </h4>
        <span className={`inline-flex items-center gap-1 px-2.5 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider ${
          status === 'analyzing'
            ? 'bg-cyan-500/10 text-cyan-400 border border-cyan-500/25 animate-pulse'
            : status === 'completed'
            ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/25'
            : status === 'failed'
            ? 'bg-rose-500/10 text-rose-400 border border-rose-500/25'
            : 'bg-slate-900/60 text-slate-500 border border-slate-800'
        }`}>
          {status === 'analyzing' ? 'Live' : status === 'completed' ? 'Done' : status === 'failed' ? 'Failed' : 'Offline'}
        </span>
      </div>

      {/* Agents List */}
      <div className="flex-1 space-y-4">
        {agentNames.map((name, idx) => {
          const agentState = getAgentState(name);
          
          return (
            <div 
              key={idx} 
              className={`p-3.5 rounded-xl border flex items-start gap-4 transition-all duration-300 ${
                agentState.status === 'in_progress'
                  ? 'bg-blue-600/5 border-blue-500/30'
                  : agentState.status === 'completed'
                  ? 'bg-emerald-500/2 border-emerald-500/10'
                  : agentState.status === 'failed'
                  ? 'bg-rose-500/5 border-rose-500/20'
                  : 'bg-slate-900/15 border-slate-800/40 opacity-70'
              }`}
            >
              {/* Status Icon Indicator */}
              <div className="mt-0.5">
                {agentState.status === 'in_progress' && (
                  <Loader2 className="w-5 h-5 text-blue-400 animate-spin" />
                )}
                {agentState.status === 'completed' && (
                  <CheckCircle2 className="w-5 h-5 text-emerald-500 fill-emerald-500/10" />
                )}
                {agentState.status === 'failed' && (
                  <AlertCircle className="w-5 h-5 text-rose-500" />
                )}
                {agentState.status === 'pending' && (
                  <Circle className="w-5 h-5 text-slate-600" />
                )}
              </div>

              {/* Agent Log Details */}
              <div className="flex-1 min-w-0">
                <div className="flex justify-between items-baseline">
                  <span className={`text-xs font-bold ${
                    agentState.status === 'in_progress'
                      ? 'text-blue-400'
                      : agentState.status === 'completed'
                      ? 'text-slate-200'
                      : 'text-slate-400'
                  }`}>
                    {name}
                  </span>
                  {agentState.timestamp && (
                    <span className="text-[9px] text-slate-500 font-semibold uppercase">
                      {agentState.timestamp}
                    </span>
                  )}
                </div>
                <p className={`text-xs mt-1 truncate ${
                  agentState.status === 'in_progress'
                    ? 'text-blue-300 font-medium'
                    : agentState.status === 'failed'
                    ? 'text-rose-400 font-medium'
                    : 'text-slate-400'
                }`}>
                  {agentState.message}
                </p>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
