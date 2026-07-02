import React from 'react';
import { 
  LayoutDashboard, PlusCircle, Layers, 
  PiggyBank, ShieldCheck, 
  Settings, Sparkles
} from 'lucide-react';

interface SidebarProps {
  activeTab: string;
  onTabChange: (tab: string) => void;
  resultLoaded: boolean;
}

export const Sidebar: React.FC<SidebarProps> = ({ activeTab, onTabChange, resultLoaded }) => {
  const menuItems = [
    { icon: <LayoutDashboard size={18} />, label: 'Dashboard', enabled: true },
    { icon: <PlusCircle size={18} />, label: 'New Deployment', enabled: true },
    { icon: <Layers size={18} />, label: 'Deployments', enabled: resultLoaded },
    { icon: <Sparkles size={18} />, label: 'AI consultant', enabled: resultLoaded, badge: 'PRO' },
    { icon: <PiggyBank size={18} />, label: 'Cost Analyzer', enabled: resultLoaded },
    { icon: <ShieldCheck size={18} />, label: 'Security Scanner', enabled: resultLoaded },
    { icon: <Settings size={18} />, label: 'Settings', enabled: true }
  ];

  return (
    <aside className="w-64 glass-panel border-r border-slate-800/50 flex flex-col h-screen fixed left-0 top-0 z-20">
      {/* Brand Logo */}
      <div className="p-6 border-b border-slate-800/40">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-blue-600 via-cyan-500 to-emerald-400 flex items-center justify-center shadow-lg shadow-blue-500/20">
            <svg className="w-6 h-6 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 15a4 4 0 004 4h9a5 5 0 10-.1-9.999 5.002 5.002 0 10-9.78 2.096A4.001 4.001 0 003 15z" />
            </svg>
          </div>
          <div>
            <h1 className="font-extrabold text-white text-base tracking-tight leading-none bg-gradient-to-r from-white via-slate-100 to-slate-300 bg-clip-text text-transparent">
              CloudPilot AI
            </h1>
            <span className="text-[10px] text-cyan-400 font-semibold uppercase tracking-wider block mt-1">
              Your AI Cloud Engineer
            </span>
          </div>
        </div>
      </div>

      {/* Navigation Menu */}
      <nav className="flex-1 px-4 py-6 space-y-1.5 overflow-y-auto">
        {menuItems.map((item, idx) => {
          const isActive = activeTab === item.label;
          return (
            <button
              key={idx}
              onClick={() => item.enabled && onTabChange(item.label)}
              disabled={!item.enabled}
              className={`w-full flex items-center justify-between px-3.5 py-2.5 rounded-lg text-sm font-medium transition-all ${
                isActive
                  ? 'bg-blue-600/10 text-blue-400 border border-blue-500/20 shadow-md shadow-blue-500/5'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/35 border border-transparent'
              } ${!item.enabled ? 'opacity-40 cursor-not-allowed' : 'cursor-pointer'}`}
            >
              <div className="flex items-center gap-3">
                <span className={isActive ? 'text-blue-400' : 'text-slate-400'}>
                  {item.icon}
                </span>
                <span>{item.label}</span>
              </div>
              {item.badge && (
                <span className="text-[8px] bg-gradient-to-r from-violet-600 to-cyan-500 text-white font-bold px-1.5 py-0.5 rounded-md leading-none tracking-wider">
                  {item.badge}
                </span>
              )}
            </button>
          );
        })}
      </nav>

      {/* Onboarding Info Box */}
      <div className="px-4 py-4 border-t border-slate-800/40">
        <div className="bg-gradient-to-br from-slate-900/60 to-slate-950/45 p-4 rounded-xl border border-slate-800/50 relative overflow-hidden group">
          <div className="absolute -right-4 -bottom-4 w-16 h-16 bg-blue-500/5 rounded-full blur-xl transition-all duration-300" />
          <div className="flex items-center gap-2 mb-2">
            <Sparkles size={14} className="text-cyan-400" />
            <span className="text-[11px] font-bold text-white uppercase tracking-wider">CloudPilot V2</span>
          </div>
          <p className="text-[11px] text-slate-400 leading-relaxed">
            Toggle tabs to access Decision Matrix calculations, RAG consultant chat, and cost simulator tools.
          </p>
        </div>
      </div>

      {/* User Profile */}
      <div className="p-4 border-t border-slate-800/40 flex items-center justify-between gap-3 bg-slate-950/20">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-full bg-gradient-to-tr from-cyan-500 to-blue-600 flex items-center justify-center text-white font-bold text-xs shadow-md shadow-cyan-500/5 border border-cyan-400/20">
            SR
          </div>
          <div className="flex flex-col min-w-0">
            <span className="text-xs font-semibold text-slate-200 truncate leading-none">
              Srikar Reddy
            </span>
            <span className="text-[10px] text-slate-500 truncate mt-1">
              srikar@example.com
            </span>
          </div>
        </div>
      </div>
    </aside>
  );
};
