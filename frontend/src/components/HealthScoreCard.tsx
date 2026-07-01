import React from 'react';
import { ShieldAlert } from 'lucide-react';
import type { HealthBreakdown } from '../types';

interface HealthScoreCardProps {
  score: number;
  breakdown: HealthBreakdown;
}

export const HealthScoreCard: React.FC<HealthScoreCardProps> = ({ score, breakdown }) => {
  // Config for circular score meter
  const radius = 38;
  const circumference = 2 * Math.PI * radius;
  const strokeDashoffset = circumference - (score / 100) * circumference;

  // Grade color configs
  const getGradeColor = (s: number) => {
    if (s >= 85) return { text: 'text-emerald-400', stroke: 'stroke-emerald-500', bg: 'bg-emerald-500/10', border: 'border-emerald-500/10', label: 'Cloud Ready' };
    if (s >= 65) return { text: 'text-blue-400', stroke: 'stroke-blue-500', bg: 'bg-blue-500/10', border: 'border-blue-500/10', label: 'Deployment Ready' };
    return { text: 'text-amber-400', stroke: 'stroke-amber-500', bg: 'bg-amber-500/10', border: 'border-amber-500/10', label: 'Needs Optimization' };
  };

  const grade = getGradeColor(score);

  const breakdownItems = [
    { label: 'Documentation', value: breakdown.documentation, max: 20, color: 'bg-blue-500' },
    { label: 'Docker Readiness', value: breakdown.docker, max: 20, color: 'bg-emerald-500' },
    { label: 'Security & Secrets', value: breakdown.security, max: 15, color: 'bg-cyan-500' },
    { label: 'Environment Config', value: breakdown.environment, max: 15, color: 'bg-orange-400' },
    { label: 'Cloud Deployment', value: breakdown.deployment, max: 15, color: 'bg-indigo-400' },
    { label: 'Code Organization', value: breakdown.organization, max: 15, color: 'bg-slate-400' }
  ];

  return (
    <div className="glass-panel p-6 rounded-2xl glow-blue flex flex-col h-full">
      {/* Header */}
      <div className="flex justify-between items-center mb-6">
        <h4 className="text-base font-bold text-white flex items-center gap-2">
          <ShieldAlert className="w-5 h-5 text-blue-400" />
          Repository Health Score
        </h4>
        <span className={`text-[10px] font-bold px-2.5 py-0.5 rounded border uppercase tracking-wider ${grade.bg} ${grade.text} ${grade.border}`}>
          {grade.label}
        </span>
      </div>

      {/* Main Score Row */}
      <div className="flex items-center gap-6 mb-6">
        {/* Radial Progress Gauge */}
        <div className="relative w-24 h-24 flex items-center justify-center">
          <svg className="w-full h-full transform -rotate-90">
            {/* Gray track background */}
            <circle
              cx="48"
              cy="48"
              r={radius}
              className="stroke-slate-800"
              strokeWidth="6.5"
              fill="transparent"
            />
            {/* Active score track */}
            <circle
              cx="48"
              cy="48"
              r={radius}
              className={`transition-all duration-1000 ease-out ${grade.stroke}`}
              strokeWidth="6.5"
              fill="transparent"
              strokeDasharray={circumference}
              strokeDashoffset={strokeDashoffset}
              strokeLinecap="round"
            />
          </svg>
          {/* Inner score label */}
          <div className="absolute flex flex-col items-center">
            <span className="text-2xl font-black text-white leading-none">
              {score}
            </span>
            <span className="text-[9px] text-slate-500 font-bold uppercase mt-1 leading-none">
              /100
            </span>
          </div>
        </div>

        {/* Short details */}
        <div className="flex-1 space-y-1">
          <h5 className="text-sm font-bold text-slate-200">Quality Assessment</h5>
          <p className="text-xs text-slate-400 leading-normal">
            Based on scanning documentation quality, Docker configurations, env file setups, security vulnerabilities, and pipeline definitions.
          </p>
        </div>
      </div>

      {/* Breakdown sliders */}
      <div className="flex-1 space-y-3.5">
        {breakdownItems.map((item, idx) => {
          const percentage = (item.value / item.max) * 100;
          return (
            <div key={idx} className="space-y-1">
              <div className="flex justify-between text-[11px] font-medium">
                <span className="text-slate-400">{item.label}</span>
                <span className="text-slate-300 font-bold">
                  {item.value}/{item.max}
                </span>
              </div>
              <div className="w-full h-1.5 bg-slate-900 rounded-full overflow-hidden">
                <div 
                  className={`h-full rounded-full transition-all duration-1000 ${item.color}`}
                  style={{ width: `${percentage}%` }}
                />
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
