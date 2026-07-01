import React from 'react';
import { Bell, Sun } from 'lucide-react';

interface HeaderProps {
  status: 'idle' | 'analyzing' | 'completed' | 'failed';
  userEmail?: string;
  onLogout?: () => void;
}

export const Header: React.FC<HeaderProps> = ({ status, userEmail, onLogout }) => {
  const getInitials = (email: string) => {
    return email.split('@')[0].substring(0, 2).toUpperCase();
  };

  const getName = (email: string) => {
    const name = email.split('@')[0];
    return name.charAt(0).toUpperCase() + name.slice(1);
  };

  return (
    <header className="flex justify-between items-center py-5 px-8 border-b border-slate-800/30 fixed top-0 right-0 left-64 z-10 glass-panel bg-slate-950/40">
      {/* Greetings */}
      <div>
        <h2 className="text-xl font-bold text-white flex items-center gap-2">
          Welcome back, {userEmail ? getName(userEmail) : 'Guest'}! 👋
        </h2>
        <p className="text-xs text-slate-400 mt-1">
          Let's build something amazing today.
        </p>
      </div>

      {/* Action Controls */}
      <div className="flex items-center gap-4">
        {/* Agent Operational Status */}
        <div className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-slate-900/80 border border-slate-800/40 text-xs">
          <span className="relative flex h-2 w-2">
            <span className={`animate-ping absolute inline-flex h-full w-full rounded-full opacity-75 ${
              status === 'analyzing' ? 'bg-amber-400' : 'bg-emerald-400'
            }`} />
            <span className={`relative inline-flex rounded-full h-2 w-2 ${
              status === 'analyzing' ? 'bg-amber-500' : 'bg-emerald-500'
            }`} />
          </span>
          <span className="text-slate-300 font-medium flex items-center gap-1.5">
            AI Agent Status:
            <span className={status === 'analyzing' ? 'text-amber-400' : 'text-emerald-400'}>
              {status === 'analyzing' ? 'Analyzing Repository...' : 'All Systems Operational'}
            </span>
          </span>
        </div>

        {/* Notifications */}
        <button className="relative p-2 rounded-lg bg-slate-900/60 hover:bg-slate-900 border border-slate-800/40 text-slate-400 hover:text-white transition-all cursor-pointer">
          <Bell size={16} />
          <span className="absolute top-1 right-1 w-2 h-2 bg-rose-500 rounded-full" />
        </button>

        {/* Theme Toggle */}
        <button className="p-2 rounded-lg bg-slate-900/60 hover:bg-slate-900 border border-slate-800/40 text-slate-400 hover:text-white transition-all cursor-pointer">
          <Sun size={16} />
        </button>

        {/* Logout Button */}
        {userEmail && onLogout && (
          <button 
            onClick={onLogout}
            className="px-3 py-1.5 rounded-lg bg-rose-500/10 hover:bg-rose-500/25 border border-rose-500/20 text-rose-300 font-semibold text-xs transition-all cursor-pointer"
          >
            Logout
          </button>
        )}

        {/* User bubble */}
        <div className="w-8 h-8 rounded-lg bg-gradient-to-tr from-blue-600 to-cyan-500 flex items-center justify-center text-white font-bold text-xs shadow-md border border-blue-400/20">
          {userEmail ? getInitials(userEmail) : 'GS'}
        </div>
      </div>
    </header>
  );
};
