import React, { useState, useEffect } from 'react';
import { ExternalLink, Loader2 } from 'lucide-react';
import { api } from '../services/api';

interface AnalysisItem {
  task_id: string;
  name: string;
  owner: string;
  url: string;
  time: string;
  status: string;
  target: string;
}

export const RecentDeploymentsCard: React.FC = () => {
  const [analyses, setAnalyses] = useState<AnalysisItem[]>([]);
  const [loading, setLoading] = useState<boolean>(true);

  useEffect(() => {
    const fetchRecent = async () => {
      try {
        const data = await api.getRecentAnalyses();
        setAnalyses(data);
      } catch (err) {
        console.error('Failed to load recent analyses', err);
      } finally {
        setLoading(false);
      }
    };
    fetchRecent();
  }, []);

  const getStatusClass = (status: string) => {
    if (status === 'Completed') {
      return 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20';
    }
    return 'bg-rose-500/10 text-rose-400 border border-rose-500/20';
  };

  const getFormattedTime = (isoString: string) => {
    try {
      const date = new Date(isoString);
      return date.toLocaleDateString() + ' ' + date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    } catch {
      return 'Just now';
    }
  };

  return (
    <div className="glass-panel p-6 rounded-2xl glow-blue flex flex-col h-full">
      {/* Header */}
      <div className="flex justify-between items-center mb-6">
        <h4 className="text-base font-bold text-white flex items-center gap-2">
          <svg className="w-5 h-5 text-blue-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          Recent Analyses
        </h4>
        <span className="text-[10px] text-slate-500 font-bold uppercase tracking-wider">
          History
        </span>
      </div>

      {/* List */}
      <div className="flex-1 space-y-4 max-h-[220px] overflow-y-auto pr-1">
        {loading ? (
          <div className="flex justify-center items-center py-12 text-slate-500 text-xs gap-1.5 font-semibold">
            <Loader2 className="w-4 h-4 text-blue-400 animate-spin" />
            Loading history...
          </div>
        ) : analyses.length > 0 ? (
          analyses.map((item) => (
            <div key={item.task_id} className="flex items-center justify-between p-2.5 rounded-xl bg-slate-900/20 border border-slate-800/40 hover:border-slate-800 transition-all duration-200">
              <div className="flex items-center gap-3">
                <span className="text-slate-400">
                  <svg className="w-5 h-5 text-slate-500" viewBox="0 0 24 24" fill="currentColor">
                    <path fillRule="evenodd" clipRule="evenodd" d="M12 2C6.477 2 2 6.484 2 12.017c0 4.425 2.865 8.18 6.839 9.504.5.092.682-.217.682-.483 0-.237-.008-.868-.013-1.703-2.782.605-3.369-1.343-3.369-1.343-.454-1.158-1.11-1.466-1.11-1.466-.908-.62.069-.608.069-.608 1.003.07 1.53 1.032 1.53 1.032.892 1.53 2.341 1.088 2.91.832.092-.647.35-1.088.636-1.338-2.22-.253-4.555-1.113-4.555-4.951 0-1.093.39-1.988 1.029-2.688-.103-.253-.446-1.272.098-2.65 0 0 .84-.27 2.75 1.026A9.564 9.564 0 0112 6.844c.85.004 1.705.115 2.504.337 1.909-1.296 2.747-1.027 2.747-1.027.546 1.379.202 2.398.1 2.651.64.7 1.028 1.595 1.028 2.688 0 3.848-2.339 4.695-4.566 4.943.359.309.678.92.678 1.855 0 1.338-.012 2.419-.012 2.747 0 .268.18.58.688.482A10.019 10.019 0 0022 12.017C22 6.484 17.522 2 12 2z" />
                  </svg>
                </span>
                <div className="flex flex-col min-w-0 max-w-[200px]">
                  <span className="text-xs font-bold text-slate-200 truncate">
                    {item.owner}/{item.name}
                  </span>
                  <span className="text-[10px] text-slate-500 font-semibold mt-0.5">
                    {getFormattedTime(item.time)}
                  </span>
                </div>
              </div>

              <div className="flex items-center gap-3">
                <span className={`text-[9px] font-extrabold uppercase px-2 py-0.5 rounded ${getStatusClass(item.status)}`}>
                  {item.status}
                </span>
                <a 
                  href={item.url} 
                  target="_blank" 
                  rel="noopener noreferrer" 
                  className="text-slate-500 hover:text-slate-300 transition-colors"
                >
                  <ExternalLink size={13} />
                </a>
              </div>
            </div>
          ))
        ) : (
          <div className="text-center py-12 text-slate-500 text-xs italic font-semibold">
            No analysis history found.
          </div>
        )}
      </div>
    </div>
  );
};
