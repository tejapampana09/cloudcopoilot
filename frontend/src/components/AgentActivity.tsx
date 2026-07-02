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
    'Architecture Agent',
    'Security Agent',
    'Performance Agent',
    'Cloud Architect Agent',
    'Infrastructure Agent',
    'Deployment Agent',
    'Monitoring Agent',
    'Cost Agent',
    'DevOps Agent',
    'Cost Optimization Agent'
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
    <div className="glass-panel p-6 rounded-2xl glow-cyan flex flex-col h-full" style={{ backgroundColor: 'rgba(255, 255, 255, 0.75)' }}>
      {/* Card Header */}
      <div className="flex justify-between items-center mb-6">
        <h4 className="text-base font-bold text-slate-800 flex items-center gap-2">
          <svg className="w-5 h-5 text-blue-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
          </svg>
          AI Agent Activity
        </h4>
        <span className={`inline-flex items-center gap-1 px-2.5 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider border ${
          status === 'analyzing'
            ? 'bg-blue-50 text-blue-600 border-blue-200 animate-pulse'
            : status === 'completed'
            ? 'bg-emerald-50 text-emerald-600 border-emerald-200'
            : status === 'failed'
            ? 'bg-rose-50 text-rose-600 border-rose-200'
            : 'bg-slate-100 text-slate-500 border-slate-200'
        }`}>
          {status === 'analyzing' ? 'Live' : status === 'completed' ? 'Done' : status === 'failed' ? 'Failed' : 'Offline'}
        </span>
      </div>

      {/* Agents List */}
      <div className="flex-1 space-y-3 max-h-[480px] overflow-y-auto pr-1">
        {agentNames.map((name, idx) => {
          const agentState = getAgentState(name);
          
          return (
            <div 
              key={idx} 
              className={`p-3 rounded-xl border flex items-start gap-4 transition-all duration-300 shadow-sm ${
                agentState.status === 'in_progress'
                  ? 'bg-blue-50/50 border-blue-300'
                  : agentState.status === 'completed'
                  ? 'bg-emerald-50/20 border-emerald-100/60'
                  : agentState.status === 'failed'
                  ? 'bg-rose-50/30 border-rose-200'
                  : 'bg-slate-50/30 border-slate-200/50 opacity-60'
              }`}
            >
              {/* Status Icon Indicator */}
              <div className="mt-0.5">
                {agentState.status === 'in_progress' && (
                  <Loader2 className="w-4.5 h-4.5 text-blue-500 animate-spin" />
                )}
                {agentState.status === 'completed' && (
                  <CheckCircle2 className="w-4.5 h-4.5 text-emerald-500 fill-emerald-50" />
                )}
                {agentState.status === 'failed' && (
                  <AlertCircle className="w-4.5 h-4.5 text-rose-500" />
                )}
                {agentState.status === 'pending' && (
                  <Circle className="w-4.5 h-4.5 text-slate-300" />
                )}
              </div>

              {/* Agent Log Details */}
              <div className="flex-1 min-w-0">
                <div className="flex justify-between items-baseline">
                  <span className={`text-xs font-bold ${
                    agentState.status === 'in_progress'
                      ? 'text-blue-600'
                      : agentState.status === 'completed'
                      ? 'text-slate-700'
                      : 'text-slate-400'
                  }`}>
                    {name}
                  </span>
                  {agentState.timestamp && (
                    <span className="text-[9px] text-slate-400 font-semibold uppercase">
                      {agentState.timestamp}
                    </span>
                  )}
                </div>
                <p className={`text-xs mt-1 truncate ${
                  agentState.status === 'in_progress'
                    ? 'text-blue-500 font-medium'
                    : agentState.status === 'failed'
                    ? 'text-rose-500 font-medium'
                    : 'text-slate-500'
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
