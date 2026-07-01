import React from 'react';
import { Loader2, CheckCircle2, Circle, AlertCircle } from 'lucide-react';
import type { AgentLog } from '../types';

interface ProgressPanelProps {
  logs: AgentLog[];
  progress: number;
  status: 'idle' | 'generating' | 'completed' | 'failed';
}

export const ProgressPanel: React.FC<ProgressPanelProps> = ({ logs, progress, status }) => {
  const steps = [
    { label: 'Planner Agent', agent: 'Planner Agent' },
    { label: 'Docker Agent', agent: 'Docker Agent' },
    { label: 'Compose Agent', agent: 'Compose Agent' },
    { label: 'Environment Agent', agent: 'Environment Agent' },
    { label: 'Terraform Agent', agent: 'Terraform Agent' },
    { label: 'GitHub Actions Agent', agent: 'GitHub Actions Agent' },
    { label: 'Validation Agent', agent: 'Validation Agent' },
    { label: 'Packaging Agent', agent: 'Packaging Agent' }
  ];

  const getStepStatus = (agentName: string) => {
    const log = logs.find(l => l.agent === agentName);
    if (log) return log.status;
    return 'pending';
  };

  const getStepMessage = (agentName: string) => {
    const log = logs.find(l => l.agent === agentName);
    if (log) return log.message;
    return 'Waiting...';
  };

  return (
    <div className="glass-panel p-6 rounded-2xl glow-blue space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h4 className="text-base font-bold text-white flex items-center gap-2">
            <Loader2 className={`w-5 h-5 text-blue-400 ${status === 'generating' ? 'animate-spin' : ''}`} />
            Infrastructure Generation Progress
          </h4>
          <p className="text-xs text-slate-400 mt-1">
            Observe our AI agents write and audit deployment scripts in real time.
          </p>
        </div>
        <span className="text-lg font-black text-blue-400">{progress}%</span>
      </div>

      {/* Progress Bar */}
      <div className="w-full h-2 bg-slate-900 rounded-full overflow-hidden border border-slate-800/40">
        <div 
          className="h-full bg-gradient-to-r from-blue-600 via-cyan-400 to-emerald-400 rounded-full transition-all duration-500"
          style={{ width: `${progress}%` }}
        />
      </div>

      {/* Steps Timeline Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {steps.map((step, idx) => {
          const stepStatus = getStepStatus(step.agent);
          const stepMsg = getStepMessage(step.agent);

          return (
            <div 
              key={idx}
              className={`p-3 rounded-xl border flex items-start gap-3.5 transition-all ${
                stepStatus === 'in_progress'
                  ? 'bg-blue-600/5 border-blue-500/20 shadow-md shadow-blue-500/5'
                  : stepStatus === 'completed'
                  ? 'bg-emerald-500/2 border-emerald-500/10'
                  : stepStatus === 'failed'
                  ? 'bg-rose-500/5 border-rose-500/20'
                  : 'bg-slate-950/20 border-slate-800/30 opacity-60'
              }`}
            >
              {/* Check Circle */}
              <div className="mt-0.5 shrink-0">
                {stepStatus === 'completed' && (
                  <CheckCircle2 className="w-4.5 h-4.5 text-emerald-500" />
                )}
                {stepStatus === 'in_progress' && (
                  <Loader2 className="w-4.5 h-4.5 text-blue-400 animate-spin" />
                )}
                {stepStatus === 'failed' && (
                  <AlertCircle className="w-4.5 h-4.5 text-rose-500" />
                )}
                {stepStatus === 'pending' && (
                  <Circle className="w-4.5 h-4.5 text-slate-700" />
                )}
              </div>

              <div className="min-w-0">
                <span className={`text-xs font-bold block ${
                  stepStatus === 'in_progress' ? 'text-blue-400' : 'text-slate-300'
                }`}>
                  {step.label}
                </span>
                <p className="text-[11px] text-slate-500 mt-1 truncate max-w-[280px]">
                  {stepMsg}
                </p>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
