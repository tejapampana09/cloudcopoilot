import React from 'react';
import { Globe, Database, HardDrive, Cpu, Network } from 'lucide-react';
import type { DeploymentRecommendation } from '../types';

interface ArchitectureCardProps {
  recommendation: DeploymentRecommendation;
  databases: string[];
}

export const ArchitectureCard: React.FC<ArchitectureCardProps> = ({ recommendation, databases }) => {
  const target = recommendation.target;
  const dbName = databases.length > 0 ? databases[0] : 'Database';

  return (
    <div className="glass-panel p-6 rounded-2xl glow-emerald flex flex-col h-full">
      {/* Header */}
      <div className="flex justify-between items-center mb-6">
        <h4 className="text-base font-bold text-white flex items-center gap-2">
          <Network className="w-5 h-5 text-emerald-400" />
          Recommended Architecture
        </h4>
        <span className="text-[10px] bg-slate-900 text-emerald-400 font-bold px-2 py-0.5 rounded border border-emerald-500/10 uppercase tracking-wider">
          Managed Setup
        </span>
      </div>

      {/* Diagram Canvas */}
      <div className="flex-1 flex flex-col items-center justify-center py-4 bg-slate-950/20 rounded-xl border border-slate-800/40 relative min-h-[250px]">
        {/* Animated Background Gradients */}
        <div className="absolute inset-0 bg-gradient-to-b from-blue-500/0 via-emerald-500/1 to-transparent pointer-events-none" />

        {/* Node 1: Internet */}
        <div className="flex flex-col items-center z-10">
          <div className="w-10 h-10 rounded-xl bg-slate-900 border border-slate-800 flex items-center justify-center text-slate-300 shadow-md">
            <Globe className="w-5 h-5" />
          </div>
          <span className="text-[10px] font-bold text-slate-400 uppercase tracking-widest mt-1">
            Internet
          </span>
        </div>

        {/* Connector 1 */}
        <div className="h-8 w-0.5 bg-gradient-to-b from-blue-500 to-cyan-500 relative my-1">
          <div className="absolute top-0 left-1/2 -translate-x-1/2 w-1.5 h-1.5 bg-cyan-400 rounded-full animate-[bounce_1.5s_infinite]" />
        </div>

        {/* Node 2: Central AWS Compute Target */}
        <div className="flex flex-col items-center z-10">
          <div className="px-5 py-3 rounded-xl bg-gradient-to-tr from-slate-900 to-slate-950 border border-aws-orange/40 flex flex-col items-center shadow-xl min-w-[150px] relative">
            {/* Glowing border effect */}
            <div className="absolute inset-0 rounded-xl border border-aws-orange/20 animate-pulse pointer-events-none" />
            <Cpu className="w-6 h-6 text-aws-orange mb-1" />
            <span className="text-xs font-bold text-white tracking-wide">
              {target}
            </span>
            <span className="text-[8px] text-slate-500 font-extrabold uppercase tracking-widest">
              Compute Service
            </span>
          </div>
        </div>

        {/* Connector 2: Forking Paths */}
        {target === "AWS Amplify" ? (
          <>
            <div className="h-8 w-0.5 bg-gradient-to-b from-cyan-500 to-emerald-500 relative my-1">
              <div className="absolute top-0 left-1/2 -translate-x-1/2 w-1.5 h-1.5 bg-emerald-400 rounded-full animate-[bounce_2s_infinite]" />
            </div>
            {/* S3 Storage Node */}
            <div className="flex flex-col items-center z-10">
              <div className="px-4 py-2.5 rounded-xl bg-slate-900 border border-slate-800 flex items-center gap-2.5 shadow-md">
                <HardDrive className="w-4 h-4 text-emerald-400" />
                <div className="flex flex-col">
                  <span className="text-xs font-bold text-slate-200">Amazon S3</span>
                  <span className="text-[8px] text-slate-500 font-bold uppercase tracking-widest leading-none mt-0.5">Static Hosting</span>
                </div>
              </div>
            </div>
          </>
        ) : (
          <div className="w-full max-w-[280px] flex flex-col items-center mt-1">
            {/* Horizontal Split Line */}
            <div className="h-0.5 w-[140px] bg-slate-800 relative">
              <div className="absolute left-0 w-0.5 h-6 bg-slate-800" />
              <div className="absolute right-0 w-0.5 h-6 bg-slate-800" />
            </div>

            {/* Bottom Nodes Row */}
            <div className="flex justify-between w-full mt-2.5 px-4">
              {/* Left: Amazon S3 (Static assets) */}
              <div className="flex flex-col items-center">
                <div className="px-3.5 py-2 rounded-xl bg-slate-900 border border-slate-800 flex items-center gap-2 shadow-md">
                  <HardDrive className="w-3.5 h-3.5 text-emerald-400" />
                  <div className="flex flex-col text-left">
                    <span className="text-[11px] font-bold text-slate-300">Amazon S3</span>
                    <span className="text-[7px] text-slate-500 font-extrabold uppercase mt-0.5">Static Assets</span>
                  </div>
                </div>
              </div>

              {/* Right: Database RDS */}
              <div className="flex flex-col items-center">
                <div className="px-3.5 py-2 rounded-xl bg-slate-900 border border-slate-800 flex items-center gap-2 shadow-md">
                  <Database className="w-3.5 h-3.5 text-blue-400" />
                  <div className="flex flex-col text-left">
                    <span className="text-[11px] font-bold text-slate-300">{dbName}</span>
                    <span className="text-[7px] text-slate-500 font-extrabold uppercase mt-0.5">AWS RDS Database</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Footer link */}
      <button className="w-full mt-5 py-2.5 rounded-xl bg-slate-900/60 hover:bg-slate-900 border border-slate-800/40 hover:border-slate-800 text-xs font-semibold text-blue-400 flex items-center justify-center gap-1 transition-all cursor-not-allowed">
        View Full Architecture &rarr;
      </button>
    </div>
  );
};
