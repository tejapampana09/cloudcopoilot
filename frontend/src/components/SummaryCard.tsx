import React from 'react';
import { Cpu, BrainCircuit } from 'lucide-react';

interface SummaryCardProps {
  summary: string;
  isAiEnhanced: boolean;
  productionPrompt?: string;
}

export const SummaryCard: React.FC<SummaryCardProps> = ({ summary, isAiEnhanced, productionPrompt }) => {
  return (
    <div className="glass-panel p-6 rounded-2xl glow-cyan flex flex-col h-full">
      {/* Header */}
      <div className="flex justify-between items-center mb-4">
        <h4 className="text-base font-bold text-white flex items-center gap-2">
          <BrainCircuit className="w-5 h-5 text-cyan-400" />
          AI Summary
        </h4>
        <span className={`text-[9px] font-bold px-2 py-0.5 rounded border uppercase tracking-wider ${
          isAiEnhanced 
            ? 'bg-cyan-500/10 text-cyan-400 border-cyan-500/10' 
            : 'bg-slate-900 text-slate-500 border-slate-800'
        }`}>
          {isAiEnhanced ? 'OpenAI GPT-4o-mini' : 'Heuristic Engine'}
        </span>
      </div>

      {/* Summary Content */}
      <div className="flex-1 bg-slate-950/20 p-4.5 rounded-xl border border-slate-800/40 relative overflow-hidden">
        {/* Background glow node */}
        <div className="absolute right-0 bottom-0 w-24 h-24 bg-cyan-500/2 rounded-full blur-xl pointer-events-none" />
        
        <p className="text-xs text-slate-300 leading-relaxed font-medium">
          "{summary}"
        </p>
      </div>

      {productionPrompt && (
        <div className="mt-4 rounded-xl border border-cyan-500/20 bg-cyan-500/10 p-3">
          <div className="text-[10px] font-bold uppercase tracking-wider text-cyan-300">Production-ready prompt</div>
          <p className="mt-2 text-[11px] leading-relaxed text-slate-300 whitespace-pre-wrap">{productionPrompt}</p>
        </div>
      )}

      {/* Small suggestion footer */}
      <div className="mt-4 text-[10px] text-slate-500 flex items-center gap-1.5 font-semibold">
        <Cpu size={12} className="text-slate-600" />
        <span>Deployments can be customized via Infrastructure-as-Code exports.</span>
      </div>
    </div>
  );
};
