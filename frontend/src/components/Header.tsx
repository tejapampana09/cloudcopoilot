import React from 'react';
import { Bell, Sun, Moon } from 'lucide-react';

interface HeaderProps {
  status: 'idle' | 'analyzing' | 'completed' | 'failed';
  userEmail?: string;
  onLogout?: () => void;
  darkMode?: boolean;
  onToggleDark?: () => void;
}

export const Header: React.FC<HeaderProps> = ({ status, userEmail, onLogout, darkMode, onToggleDark }) => {
  const getInitials = (email: string) => {
    return email.split('@')[0].substring(0, 2).toUpperCase();
  };

  const getName = (email: string) => {
    const name = email.split('@')[0];
    return name.charAt(0).toUpperCase() + name.slice(1);
  };

  return (
    <header className="flex justify-between items-center py-5 px-8 border-b border-slate-200/60 fixed top-0 right-0 left-64 z-10 glass-panel">
      {/* Greetings */}
      <div>
        <h2 className="text-xl font-bold text-slate-800 flex items-center gap-2">
          Welcome back, {userEmail ? getName(userEmail) : 'Developer'}! 👋
        </h2>
        <p className="text-xs text-slate-500 mt-1">
          Review your repository analytics and fixes.
        </p>
      </div>

      {/* Action Controls */}
      <div className="flex items-center gap-4">
        {/* Agent Operational Status */}
        <div className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-white border border-slate-200 text-xs">
          <span className="relative flex h-2 w-2">
            <span className={`animate-ping absolute inline-flex h-full w-full rounded-full opacity-75 ${
              status === 'analyzing' ? 'bg-amber-400' : 'bg-emerald-400'
            }`} />
            <span className={`relative inline-flex rounded-full h-2 w-2 ${
              status === 'analyzing' ? 'bg-amber-500' : 'bg-emerald-500'
            }`} />
          </span>
          <span className="text-slate-600 font-medium flex items-center gap-1.5">
            AI Agent Status:
            <span className={status === 'analyzing' ? 'text-amber-600 font-bold' : 'text-emerald-600 font-bold'}>
              {status === 'analyzing' ? 'Analyzing Repository...' : 'All Systems Operational'}
            </span>
          </span>
        </div>

        {/* Notifications */}
        <button className="relative p-2 rounded-lg bg-white hover:bg-slate-50 border border-slate-200 text-slate-500 hover:text-slate-800 transition-all cursor-pointer">
          <Bell size={16} />
          <span className="absolute top-1 right-1 w-2 h-2 bg-rose-500 rounded-full" />
        </button>

        {/* Theme Toggle */}
        <button 
          onClick={onToggleDark}
          className="p-2 rounded-lg bg-white hover:bg-slate-50 border border-slate-200 text-slate-500 hover:text-slate-800 transition-all cursor-pointer"
          title="Toggle Dark Mode"
        >
          {darkMode ? <Sun size={16} /> : <Moon size={16} />}
        </button>

        {/* Logout Button */}
        {userEmail && onLogout && (
          <button 
            onClick={onLogout}
            className="px-3 py-1.5 rounded-lg bg-rose-500/10 hover:bg-rose-500/20 border border-rose-500/20 text-rose-600 font-semibold text-xs transition-all cursor-pointer"
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
