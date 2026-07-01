import React from 'react';
import { ClipboardList, CheckCircle2, AlertTriangle, XCircle } from 'lucide-react';
import type { ChecklistItem } from '../types';

interface ChecklistCardProps {
  checklist: ChecklistItem[];
}

export const ChecklistCard: React.FC<ChecklistCardProps> = ({ checklist }) => {
  const getIcon = (status: ChecklistItem['status']) => {
    switch (status) {
      case 'checked':
        return <CheckCircle2 className="w-4 h-4 text-emerald-500 fill-emerald-500/10 shrink-0" />;
      case 'warning':
        return <AlertTriangle className="w-4 h-4 text-amber-500 shrink-0" />;
      case 'error':
        return <XCircle className="w-4 h-4 text-rose-500 shrink-0" />;
    }
  };

  return (
    <div className="glass-panel p-6 rounded-2xl glow-blue flex flex-col h-full">
      {/* Header */}
      <div className="flex justify-between items-center mb-6">
        <h4 className="text-base font-bold text-white flex items-center gap-2">
          <ClipboardList className="w-5 h-5 text-blue-400" />
          Deployment Checklist
        </h4>
        <span className="text-[10px] bg-slate-900 text-slate-400 font-bold px-2 py-0.5 rounded border border-slate-800 uppercase tracking-wider">
          Verification
        </span>
      </div>

      {/* Checklist List */}
      <div className="flex-1 space-y-3">
        {checklist.map((item, idx) => (
          <div 
            key={idx}
            className="flex items-center gap-3 p-3 rounded-xl bg-slate-900/30 border border-slate-800/40 hover:border-slate-800 transition-all duration-200"
          >
            {getIcon(item.status)}
            <span className={`text-xs font-semibold ${
              item.status === 'checked'
                ? 'text-slate-300'
                : item.status === 'warning'
                ? 'text-amber-300'
                : 'text-rose-300'
            }`}>
              {item.label}
            </span>
          </div>
        ))}
        {checklist.length === 0 && (
          <div className="text-center py-8 text-xs text-slate-500">
            No items in the checklist yet.
          </div>
        )}
      </div>
    </div>
  );
};
