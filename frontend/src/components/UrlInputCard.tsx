import React, { useState } from 'react';
import { Play, CheckCircle2, Cloud, Code2, Cpu } from 'lucide-react';

interface UrlInputCardProps {
  onAnalyze: (url: string) => void;
  isLoading: boolean;
}

export const UrlInputCard: React.FC<UrlInputCardProps> = ({ onAnalyze, isLoading }) => {
  const [url, setUrl] = useState('');
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    if (!url.trim()) {
      setError('Please enter a GitHub repository URL.');
      return;
    }

    if (!url.includes('github.com')) {
      setError('Please provide a valid GitHub repository URL.');
      return;
    }

    onAnalyze(url.trim());
  };

  const handleRecentClick = (recentUrl: string) => {
    setUrl(recentUrl);
    onAnalyze(recentUrl);
  };

  const recentRepos = [
    'https://github.com/facebook/react',
    'https://github.com/fastapi/fastapi',
    'https://github.com/expressjs/express'
  ];

  return (
    <div className="glass-panel p-8 rounded-2xl glow-blue relative overflow-hidden">
      {/* Decorative gradient overlay */}
      <div className="absolute right-0 top-0 w-80 h-80 bg-blue-500/5 rounded-full blur-3xl pointer-events-none" />
      <div className="absolute left-1/3 bottom-0 w-60 h-60 bg-emerald-500/5 rounded-full blur-3xl pointer-events-none" />

      <div className="grid grid-cols-1 lg:grid-cols-5 gap-8 items-center relative z-10">
        {/* Left Column: Form & Info */}
        <div className="lg:col-span-3 space-y-6">
          <div>
            <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-blue-500/10 text-blue-400 text-[10px] font-bold uppercase tracking-wider mb-3.5 border border-blue-500/10">
              01 &middot; Deploy in Seconds
            </span>
            <h3 className="text-2xl font-extrabold text-white tracking-tight">
              Paste GitHub Repository URL
            </h3>
            <p className="text-sm text-slate-400 mt-2 leading-relaxed">
              Our AI agent architecture will clone, inspect and audit your repository to structure a secure, production-ready AWS architecture recommendation.
            </p>
          </div>

          {/* Form */}
          <form onSubmit={handleSubmit} className="space-y-3">
            <div className="relative flex items-center">
              <span className="absolute left-4 text-slate-500">
                <svg className="w-5 h-5" viewBox="0 0 24 24" fill="currentColor">
                  <path fillRule="evenodd" clipRule="evenodd" d="M12 2C6.477 2 2 6.484 2 12.017c0 4.425 2.865 8.18 6.839 9.504.5.092.682-.217.682-.483 0-.237-.008-.868-.013-1.703-2.782.605-3.369-1.343-3.369-1.343-.454-1.158-1.11-1.466-1.11-1.466-.908-.62.069-.608.069-.608 1.003.07 1.53 1.032 1.53 1.032.892 1.53 2.341 1.088 2.91.832.092-.647.35-1.088.636-1.338-2.22-.253-4.555-1.113-4.555-4.951 0-1.093.39-1.988 1.029-2.688-.103-.253-.446-1.272.098-2.65 0 0 .84-.27 2.75 1.026A9.564 9.564 0 0112 6.844c.85.004 1.705.115 2.504.337 1.909-1.296 2.747-1.027 2.747-1.027.546 1.379.202 2.398.1 2.651.64.7 1.028 1.595 1.028 2.688 0 3.848-2.339 4.695-4.566 4.943.359.309.678.92.678 1.855 0 1.338-.012 2.419-.012 2.747 0 .268.18.58.688.482A10.019 10.019 0 0022 12.017C22 6.484 17.522 2 12 2z" />
                </svg>
              </span>
              <input
                type="text"
                placeholder="https://github.com/username/awesome-project"
                value={url}
                onChange={(e) => setUrl(e.target.value)}
                disabled={isLoading}
                className="w-full pl-12 pr-40 py-3.5 rounded-xl glass-input text-sm text-slate-100 placeholder-slate-500"
              />
              <button
                type="submit"
                disabled={isLoading}
                className={`absolute right-2 px-5 py-2 rounded-lg bg-blue-600 hover:bg-blue-500 text-white font-semibold text-xs flex items-center gap-1.5 transition-all shadow-md shadow-blue-500/20 cursor-pointer ${
                  isLoading ? 'opacity-50 cursor-not-allowed' : ''
                }`}
              >
                {isLoading ? (
                  <>
                    <svg className="animate-spin h-3.5 w-3.5 text-white" fill="none" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                    </svg>
                    <span>Analyzing...</span>
                  </>
                ) : (
                  <>
                    <Play size={13} fill="currentColor" />
                    <span>Analyze Repository</span>
                  </>
                )}
              </button>
            </div>
            {error && (
              <p className="text-xs text-rose-400 font-medium pl-1">{error}</p>
            )}
          </form>

          {/* Feature Badges */}
          <div className="flex flex-wrap gap-2.5 pt-2">
            {[
              { icon: <Code2 size={12} />, label: 'Auto Code Analysis' },
              { icon: <Cpu size={12} />, label: 'Smart Infrastructure' },
              { icon: <Cloud size={12} />, label: 'One-Click Deployment' },
              { icon: <CheckCircle2 size={12} />, label: '24/7 Monitoring' }
            ].map((badge, idx) => (
              <span 
                key={idx}
                className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-slate-900/50 border border-slate-800/60 text-slate-400 text-xs font-medium hover:border-slate-700/80 transition-all"
              >
                <span className="text-emerald-500">{badge.icon}</span>
                {badge.label}
              </span>
            ))}
          </div>

          {/* Recent Repos */}
          <div className="pt-2 flex items-center gap-3">
            <span className="text-xs text-slate-500 font-semibold">Try Examples:</span>
            <div className="flex flex-wrap gap-2">
              {recentRepos.map((rUrl, idx) => {
                const name = rUrl.split('/').slice(-2).join('/');
                return (
                  <button
                    key={idx}
                    type="button"
                    onClick={() => handleRecentClick(rUrl)}
                    disabled={isLoading}
                    className="text-[11px] font-semibold text-blue-400/80 hover:text-blue-400 bg-blue-500/5 hover:bg-blue-500/10 px-2.5 py-1 rounded border border-blue-500/10 cursor-pointer"
                  >
                    {name}
                  </button>
                );
              })}
            </div>
          </div>
        </div>

        {/* Right Column: Beautiful AWS Cloud Animation Graphic */}
        <div className="lg:col-span-2 flex justify-center">
          <div className="relative w-64 h-64 flex items-center justify-center">
            {/* Animated orbital rings */}
            <div className="absolute w-56 h-56 rounded-full border border-slate-800/40 animate-[spin_20s_linear_infinite]" />
            <div className="absolute w-44 h-44 rounded-full border border-dashed border-slate-800/60 animate-[spin_15s_linear_infinite_reverse]" />
            <div className="absolute w-32 h-32 rounded-full bg-gradient-to-tr from-blue-600/5 to-cyan-500/5 blur-lg" />

            {/* Glowing connecting lines */}
            <div className="absolute w-full h-0.5 bg-gradient-to-r from-transparent via-blue-500/20 to-transparent rotate-45" />
            <div className="absolute w-full h-0.5 bg-gradient-to-r from-transparent via-emerald-500/10 to-transparent -rotate-45" />

            {/* Central Cloud Node */}
            <div className="relative w-20 h-20 rounded-2xl bg-slate-900 border border-slate-800 flex flex-col items-center justify-center shadow-2xl z-10 group hover:border-blue-500/30 transition-all duration-300">
              <div className="absolute inset-0 bg-gradient-to-tr from-blue-600/10 to-cyan-500/10 rounded-2xl opacity-0 group-hover:opacity-100 transition-all duration-300" />
              <Cloud size={32} className={`text-blue-500 ${isLoading ? 'animate-bounce' : ''}`} />
              <div className="text-[9px] font-bold text-slate-400 uppercase tracking-widest mt-1">
                Cloud
              </div>
            </div>

            {/* Floating Satellite Nodes */}
            {/* 1. Github Icon (top-left) */}
            <div className="absolute top-4 left-6 w-11 h-11 rounded-xl bg-slate-950/80 border border-slate-800/60 flex items-center justify-center shadow-lg animate-[pulse_3s_ease-in-out_infinite]">
              <svg className="w-5 h-5 text-slate-300" viewBox="0 0 24 24" fill="currentColor">
                <path fillRule="evenodd" clipRule="evenodd" d="M12 2C6.477 2 2 6.484 2 12.017c0 4.425 2.865 8.18 6.839 9.504.5.092.682-.217.682-.483 0-.237-.008-.868-.013-1.703-2.782.605-3.369-1.343-3.369-1.343-.454-1.158-1.11-1.466-1.11-1.466-.908-.62.069-.608.069-.608 1.003.07 1.53 1.032 1.53 1.032.892 1.53 2.341 1.088 2.91.832.092-.647.35-1.088.636-1.338-2.22-.253-4.555-1.113-4.555-4.951 0-1.093.39-1.988 1.029-2.688-.103-.253-.446-1.272.098-2.65 0 0 .84-.27 2.75 1.026A9.564 9.564 0 0112 6.844c.85.004 1.705.115 2.504.337 1.909-1.296 2.747-1.027 2.747-1.027.546 1.379.202 2.398.1 2.651.64.7 1.028 1.595 1.028 2.688 0 3.848-2.339 4.695-4.566 4.943.359.309.678.92.678 1.855 0 1.338-.012 2.419-.012 2.747 0 .268.18.58.688.482A10.019 10.019 0 0022 12.017C22 6.484 17.522 2 12 2z" />
              </svg>
            </div>

            {/* 2. Code Node (bottom-center) */}
            <div className="absolute bottom-4 left-24 w-11 h-11 rounded-xl bg-slate-950/80 border border-slate-800/60 flex items-center justify-center shadow-lg animate-[pulse_4s_ease-in-out_infinite_1s]">
              <Code2 size={20} className="text-emerald-500" />
            </div>

            {/* 3. AWS Node (top-right) */}
            <div className="absolute top-12 right-6 px-2.5 py-1.5 rounded-xl bg-slate-950/80 border border-slate-800/60 flex flex-col items-center justify-center shadow-lg animate-[pulse_3.5s_ease-in-out_infinite_0.5s]">
              <span className="text-[10px] font-extrabold text-aws-orange tracking-tight uppercase leading-none">
                aws
              </span>
              <span className="text-[7px] text-slate-500 font-bold uppercase mt-0.5">
                console
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
