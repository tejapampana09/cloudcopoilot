import React from 'react';
import { ShieldCheck, CheckCircle2, AlertTriangle, XCircle } from 'lucide-react';

interface ValidationResult {
  file: string;
  status: 'valid' | 'warning' | 'error' | string;
  message: string;
}

interface ValidationReportCardProps {
  score: number;
  results: ValidationResult[];
}

export const ValidationReportCard: React.FC<ValidationReportCardProps> = ({ score, results }) => {
  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'valid':
        return <CheckCircle2 className="w-4 h-4 text-emerald-500 fill-emerald-500/10 shrink-0" />;
      case 'warning':
        return <AlertTriangle className="w-4 h-4 text-amber-500 shrink-0" />;
      case 'error':
      default:
        return <XCircle className="w-4 h-4 text-rose-500 shrink-0" />;
    }
  };

  const getScoreColor = (s: number) => {
    if (s >= 90) return 'text-emerald-400 border-emerald-500/10 bg-emerald-500/10';
    if (s >= 75) return 'text-blue-400 border-blue-500/10 bg-blue-500/10';
    return 'text-amber-400 border-amber-500/10 bg-amber-500/10';
  };

  return (
    <div className="glass-panel p-6 rounded-2xl glow-blue flex flex-col h-full">
      {/* Header */}
      <div className="flex justify-between items-center mb-6">
        <h4 className="text-base font-bold text-white flex items-center gap-2">
          <ShieldCheck className="w-5 h-5 text-blue-400" />
          Infrastructure Audit
        </h4>
        <span className={`text-xs font-extrabold px-3 py-1 rounded border uppercase tracking-wider ${getScoreColor(score)}`}>
          Score: {score}/100
        </span>
      </div>

      {/* Audit Checklist List */}
      <div className="flex-1 space-y-3.5">
        {results.map((res, idx) => (
          <div 
            key={idx}
            className="p-3 rounded-xl bg-slate-900/30 border border-slate-800/40 flex items-start gap-3 hover:border-slate-800 transition-all"
          >
            <div className="mt-0.5">{getStatusIcon(res.status)}</div>
            <div className="min-w-0">
              <span className="text-xs font-bold text-slate-200 block">
                {res.file}
              </span>
              <p className="text-[11px] text-slate-400 mt-1 leading-relaxed">
                {res.message}
              </p>
            </div>
          </div>
        ))}
        {results.length === 0 && (
          <div className="text-center py-12 text-xs text-slate-500 font-semibold italic">
            Waiting for files to audit...
          </div>
        )}
      </div>
    </div>
  );
};
