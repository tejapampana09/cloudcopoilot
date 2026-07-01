import React from 'react';
import { Sparkles, Terminal } from 'lucide-react';
import type { AnalysisResult } from '../types';

interface RepoAnalysisCardProps {
  result: AnalysisResult;
}

export const RepoAnalysisCard: React.FC<RepoAnalysisCardProps> = ({ result }) => {
  const metadata = result.metadata;
  
  // Format primary language
  const primaryLang = metadata.languages.length > 0 
    ? `${metadata.languages[0].name} (${metadata.languages[0].percentage}%)` 
    : 'Unknown';

  const details = [
    { label: 'Framework', value: metadata.frameworks.length > 0 ? metadata.frameworks[0] : 'None Detected' },
    { label: 'Language', value: primaryLang },
    { label: 'Package Manager', value: metadata.package_managers.length > 0 ? metadata.package_managers[0] : 'None' },
    { label: 'Database', value: metadata.databases.length > 0 ? metadata.databases[0] : 'None Detected' },
    { label: 'Docker', value: metadata.docker_readiness ? 'Detected' : 'Missing' },
    { label: 'Deployment', value: result.recommendation.target }
  ];

  return (
    <div className="glass-panel p-6 rounded-2xl glow-blue flex flex-col h-full">
      {/* Header */}
      <div className="flex justify-between items-center mb-6">
        <h4 className="text-base font-bold text-white flex items-center gap-2">
          <Terminal className="w-5 h-5 text-blue-400" />
          Repository Analysis
        </h4>
        <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider bg-emerald-500/10 text-emerald-400 border border-emerald-500/25">
          Completed
        </span>
      </div>

      {/* Details Table/Grid */}
      <div className="flex-1 space-y-4">
        {details.map((item, idx) => (
          <div key={idx} className="flex justify-between items-center text-xs pb-3 border-b border-slate-800/35 last:border-b-0 last:pb-0">
            <span className="text-slate-400 font-semibold">{item.label}</span>
            <span className="font-extrabold text-slate-100">{item.value}</span>
          </div>
        ))}
      </div>

      {/* Confidence Score Meter */}
      <div className="mt-6 space-y-2 pt-2 border-t border-slate-800/40">
        <div className="flex justify-between text-xs font-semibold">
          <span className="text-slate-400 flex items-center gap-1">
            <Sparkles size={13} className="text-cyan-400" />
            Confidence Score
          </span>
          <span className="text-cyan-400 font-extrabold">
            {result.recommendation.confidence_score}%
          </span>
        </div>
        
        {/* Progress Bar */}
        <div className="w-full h-2 bg-slate-900 rounded-full overflow-hidden">
          <div 
            className="h-full bg-gradient-to-r from-blue-500 via-cyan-400 to-emerald-400 rounded-full transition-all duration-1000"
            style={{ width: `${result.recommendation.confidence_score}%` }}
          />
        </div>
      </div>
    </div>
  );
};
