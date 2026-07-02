import React, { useState } from 'react';
import { 
  LayoutDashboard, FileText, Sparkles, Settings,
  ChevronLeft, ChevronRight, Search, FolderGit2
} from 'lucide-react';

interface SidebarProps {
  activeTab: string;
  onTabChange: (tab: string) => void;
  resultLoaded: boolean;
  currentUser?: any;
}

export const Sidebar: React.FC<SidebarProps> = ({ activeTab, onTabChange, resultLoaded, currentUser }) => {
  const [isCollapsed, setIsCollapsed] = useState(false);
  const [currentWorkspace, setCurrentWorkspace] = useState('tejapampana09/cloudcopoilot');
  const [showWorkspaceDropdown, setShowWorkspaceDropdown] = useState(false);

  const workspaces = [
    'tejapampana09/cloudcopoilot',
    'cloudpilot-demo/staging-env'
  ];

  const menuItems = [
    { icon: <LayoutDashboard size={18} />, label: 'Dashboard', enabled: true },
    { icon: <FileText size={18} />, label: 'Reports', enabled: resultLoaded },
    { icon: <Sparkles size={18} />, label: 'AI consultant', enabled: resultLoaded, badge: 'PRO' },
    { icon: <Settings size={18} />, label: 'Settings', enabled: true }
  ];

  return (
    <aside className={`glass-panel border-r border-slate-800/50 flex flex-col h-screen fixed left-0 top-0 z-20 transition-all duration-300 ${
      isCollapsed ? 'w-20' : 'w-64'
    }`}>
      
      {/* Brand Logo Header */}
      <div className={`p-6 border-b border-slate-800/40 flex items-center justify-between gap-3 ${
        isCollapsed ? 'justify-center px-4' : ''
      }`}>
        <div className="flex items-center gap-3 min-w-0">
          <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-blue-600 via-cyan-500 to-emerald-400 flex items-center justify-center shadow-lg shadow-blue-500/20 shrink-0">
            <svg className="w-5 h-5 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 15a4 4 0 004 4h9a5 5 0 10-.1-9.999 5.002 5.002 0 10-9.78 2.096A4.001 4.001 0 003 15z" />
            </svg>
          </div>
          {!isCollapsed && (
            <div className="min-w-0">
              <h1 className="font-extrabold text-white text-sm tracking-tight leading-none bg-gradient-to-r from-white to-slate-350 bg-clip-text text-transparent truncate">
                CloudPilot AI
              </h1>
              <span className="text-[9px] text-cyan-400 font-semibold uppercase tracking-wider block mt-1">
                V2 Platform
              </span>
            </div>
          )}
        </div>
        
        {/* Sidebar Collapse Toggle Button */}
        {!isCollapsed && (
          <button 
            onClick={() => setIsCollapsed(true)}
            className="p-1 rounded-lg bg-slate-900 hover:bg-slate-800 border border-slate-800 text-slate-400 hover:text-slate-200 transition-all cursor-pointer"
          >
            <ChevronLeft size={14} />
          </button>
        )}
      </div>

      {/* Workspace Switcher Header (Compact if collapsed) */}
      {!isCollapsed ? (
        <div className="px-4 pt-4 relative">
          <button 
            onClick={() => setShowWorkspaceDropdown(!showWorkspaceDropdown)}
            className="w-full flex items-center justify-between px-3 py-2 rounded-xl bg-slate-950/65 border border-slate-850 hover:border-slate-750 text-xs font-semibold text-slate-300 transition-all cursor-pointer"
          >
            <div className="flex items-center gap-2 min-w-0">
              <FolderGit2 className="w-4 h-4 text-blue-400 shrink-0" />
              <span className="truncate">{currentWorkspace}</span>
            </div>
            <svg className="w-3 h-3 text-slate-500 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
            </svg>
          </button>

          {showWorkspaceDropdown && (
            <div className="absolute left-4 right-4 mt-1.5 bg-slate-900 border border-slate-850 rounded-xl shadow-xl z-30 p-1.5 space-y-1">
              {workspaces.map((w, idx) => (
                <button
                  key={idx}
                  onClick={() => {
                    setCurrentWorkspace(w);
                    setShowWorkspaceDropdown(false);
                  }}
                  className="w-full text-left px-3 py-2 rounded-lg text-[11px] text-slate-300 hover:text-white hover:bg-slate-800 transition-all truncate cursor-pointer block"
                >
                  {w}
                </button>
              ))}
            </div>
          )}
        </div>
      ) : (
        <div className="flex justify-center pt-4">
          <button 
            onClick={() => setIsCollapsed(false)}
            className="p-2 rounded-lg bg-slate-900 border border-slate-850 text-slate-400 hover:text-white cursor-pointer"
          >
            <ChevronRight size={14} />
          </button>
        </div>
      )}

      {/* Global Search Bar (Only shown when expanded) */}
      {!isCollapsed && (
        <div className="px-4 pt-3">
          <div className="relative">
            <Search className="absolute left-3 top-2.5 w-3.5 h-3.5 text-slate-500" />
            <input 
              type="text" 
              placeholder="Search or cmd+k" 
              className="w-full pl-9 pr-4 py-2 rounded-xl bg-slate-950/40 border border-slate-850 text-[11px] text-slate-300 placeholder-slate-500 focus:outline-none focus:border-blue-500/80 focus:ring-1 focus:ring-blue-500/20"
              disabled
            />
          </div>
        </div>
      )}

      {/* Navigation Menu */}
      <nav className={`flex-1 px-4 py-6 space-y-1.5 overflow-y-auto ${
        isCollapsed ? 'px-2 flex flex-col items-center' : ''
      }`}>
        {menuItems.map((item, idx) => {
          const isActive = activeTab === item.label;
          return (
            <button
              key={idx}
              onClick={() => item.enabled && onTabChange(item.label)}
              disabled={!item.enabled}
              className={`flex items-center rounded-lg text-sm font-medium transition-all ${
                isCollapsed 
                  ? 'p-3.5 justify-center' 
                  : 'w-full justify-between px-3.5 py-2.5'
              } ${
                isActive
                  ? 'bg-blue-600/10 text-blue-400 border border-blue-500/20 shadow-md shadow-blue-500/5'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/35 border border-transparent'
              } ${!item.enabled ? 'opacity-30 cursor-not-allowed' : 'cursor-pointer'}`}
              title={isCollapsed ? item.label : undefined}
            >
              <div className="flex items-center gap-3">
                <span className={isActive ? 'text-blue-400' : 'text-slate-400'}>
                  {item.icon}
                </span>
                {!isCollapsed && <span>{item.label}</span>}
              </div>
              {!isCollapsed && item.badge && (
                <span className="text-[8px] bg-gradient-to-r from-violet-600 to-cyan-500 text-white font-bold px-1.5 py-0.5 rounded-md leading-none tracking-wider shrink-0">
                  {item.badge}
                </span>
              )}
            </button>
          );
        })}
      </nav>

      {/* Onboarding Info Card (Hidden if collapsed) */}
      {!isCollapsed && (
        <div className="px-4 py-4 border-t border-slate-800/40">
          <div className="bg-gradient-to-br from-slate-900/60 to-slate-950/45 p-4 rounded-xl border border-slate-800/50 relative overflow-hidden group">
            <div className="absolute -right-4 -bottom-4 w-16 h-16 bg-blue-500/5 rounded-full blur-xl" />
            <div className="flex items-center gap-2 mb-1.5">
              <Sparkles size={14} className="text-cyan-400" />
              <span className="text-[10px] font-bold text-white uppercase tracking-wider">CloudPilot AI</span>
            </div>
            <p className="text-[10px] text-slate-500 leading-relaxed">
              V2 Enterprise Platform activated.
            </p>
          </div>
        </div>
      )}

      {/* User Profile */}
      <div className={`p-4 border-t border-slate-800/40 flex items-center justify-between gap-3 bg-slate-950/20 ${
        isCollapsed ? 'justify-center px-2' : ''
      }`}>
        <div className="flex items-center gap-3 min-w-0">
          <div className="w-9 h-9 rounded-full bg-gradient-to-tr from-cyan-500 to-blue-600 flex items-center justify-center text-white font-bold text-xs shadow-md shadow-cyan-500/5 border border-cyan-400/20 shrink-0">
            {currentUser?.email?.substring(0, 2).toUpperCase() || 'CP'}
          </div>
          {!isCollapsed && (
            <div className="flex flex-col min-w-0">
              <span className="text-xs font-semibold text-slate-200 truncate leading-none">
                {currentUser?.email?.split('@')[0] || 'User'}
              </span>
              <span className="text-[10px] text-slate-500 truncate mt-1">
                {currentUser?.email || 'user@example.com'}
              </span>
            </div>
          )}
        </div>
      </div>
    </aside>
  );
};
