import React from 'react';
import { Loader2, CheckCircle2, Circle } from 'lucide-react';

interface DeploymentStepsCardProps {
  status: 'idle' | 'analyzing' | 'completed' | 'failed';
}

export const DeploymentStepsCard: React.FC<DeploymentStepsCardProps> = ({ status }) => {
  const steps = [
    {
      id: 1,
      label: 'Analyze Repository',
      status: status === 'completed' ? 'completed' : status === 'analyzing' ? 'in_progress' : 'pending'
    },
    {
      id: 2,
      label: 'Build & Push Docker Image',
      status: status === 'completed' ? 'completed' : 'pending'
    },
    {
      id: 3,
      label: 'Provision Infrastructure',
      status: status === 'completed' ? 'in_progress' : 'pending'
    },
    {
      id: 4,
      label: 'Deploy Application',
      status: 'pending'
    },
    {
      id: 5,
      label: 'Setup Monitoring',
      status: 'pending'
    }
  ];

  return (
    <div className="glass-panel p-6 rounded-2xl glow-blue flex flex-col h-full">
      {/* Header */}
      <div className="flex justify-between items-center mb-6">
        <h4 className="text-base font-bold text-white flex items-center gap-2">
          <svg className="w-5 h-5 text-blue-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
          </svg>
          Deployment Steps
        </h4>
        <span className="text-[10px] bg-slate-900 text-slate-400 font-bold px-2 py-0.5 rounded border border-slate-800 uppercase tracking-wider">
          Roadmap
        </span>
      </div>

      {/* Steps List */}
      <div className="flex-1 space-y-4">
        {steps.map((step) => (
          <div key={step.id} className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className={`w-6 h-6 rounded-full flex items-center justify-center text-[10px] font-bold ${
                step.status === 'completed'
                  ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20'
                  : step.status === 'in_progress'
                  ? 'bg-blue-600/10 text-blue-400 border border-blue-500/20 animate-pulse'
                  : 'bg-slate-900 text-slate-500 border border-slate-800'
              }`}>
                {step.id}
              </div>
              <span className={`text-xs font-semibold ${
                step.status === 'completed'
                  ? 'text-slate-300'
                  : step.status === 'in_progress'
                  ? 'text-blue-400'
                  : 'text-slate-500'
              }`}>
                {step.label}
              </span>
            </div>
            
            {/* Status Icon */}
            <div>
              {step.status === 'completed' && (
                <CheckCircle2 className="w-4 h-4 text-emerald-500 fill-emerald-500/10" />
              )}
              {step.status === 'in_progress' && (
                <Loader2 className="w-4 h-4 text-blue-400 animate-spin" />
              )}
              {step.status === 'pending' && (
                <Circle className="w-4 h-4 text-slate-700" />
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
