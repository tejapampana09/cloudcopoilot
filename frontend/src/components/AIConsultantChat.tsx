import React, { useState, useRef, useEffect } from 'react';
import { 
  Send, MessageSquareCode, Sparkles, Loader2,
  ShieldCheck, Cpu, Database, FileText, ArrowRight,
  TrendingDown, KeyRound
} from 'lucide-react';
import type { AnalysisResult } from '../types';
import { api } from '../services/api';

interface Message {
  role: 'user' | 'assistant';
  content: string;
  timestamp: string;
}

interface AIConsultantChatProps {
  result: AnalysisResult;
  taskId: string;
}

export const AIConsultantChat: React.FC<AIConsultantChatProps> = ({ result, taskId }) => {
  const [messages, setMessages] = useState<Message[]>([
    {
      role: 'assistant',
      content: `Hello! I am your **AI Technical Consultant**. I have audited your repository **${result.repository_owner}/${result.repository_name}**.\n\nYou can ask me details about the codebase layers, ORM configurations, estimated bottlenecks, database options, or request custom build setup commands. How can I assist you today?`,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    }
  ]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);

  const consultantActions = [
    {
      icon: <Cpu className="w-4 h-4 text-blue-500" />,
      label: 'Explain Architecture',
      query: 'Explain my repository architecture boundaries, folder structures, and overall framework setup.',
      desc: 'Codebase layers & framework overview'
    },
    {
      icon: <ShieldCheck className="w-4 h-4 text-emerald-500" />,
      label: `Why Security Score ${result.health_score}?`,
      query: `Explain why our security score is ${result.health_score} out of 100, and show potential risks.`,
      desc: 'Security score audits & breakdown'
    },
    {
      icon: <Database className="w-4 h-4 text-cyan-500" />,
      label: 'Explain Databases',
      query: 'Check what databases and ORMs are used, and identify potential scaling bottlenecks.',
      desc: 'DB client checks & configurations'
    },
    {
      icon: <FileText className="w-4 h-4 text-orange-500" />,
      label: 'Show Setup Commands',
      query: 'List the setup, build, and run commands needed to install and execute this project locally.',
      desc: 'Development execution blueprints'
    },
    {
      icon: <TrendingDown className="w-4 h-4 text-rose-500" />,
      label: 'Identify Performance Risks',
      query: 'Audits files complexity size, potential bottlenecks, and heavy dependencies configurations.',
      desc: 'Sizing & database queries scaling'
    },
    {
      icon: <KeyRound className="w-4 h-4 text-violet-500" />,
      label: 'Explain Authentication',
      query: 'Check how authentication and authorization are handled in the repository, and evaluate security.',
      desc: 'Token validations & config checks'
    }
  ];

  useEffect(() => {
    scrollRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleSend = async (textToSend: string) => {
    if (!textToSend.trim() || isLoading) return;

    const userMsg: Message = {
      role: 'user',
      content: textToSend,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    };

    setMessages((prev) => [...prev, userMsg]);
    setInput('');
    setIsLoading(true);

    try {
      const answer = await api.chatWithRepository(taskId, textToSend);
      
      const assistantMsg: Message = {
        role: 'assistant',
        content: answer,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
      };
      setMessages((prev) => [...prev, assistantMsg]);
    } catch (err: any) {
      setMessages((prev) => [
        ...prev,
        {
          role: 'assistant',
          content: `Sorry, I encountered an error querying the consultant: ${err.message || 'Unknown error'}. Please try again.`,
          timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
        }
      ]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="grid grid-cols-1 lg:grid-cols-3 gap-8 h-[650px]">
      
      {/* LEFT COLUMN: ASK CLOUDCOPILOT DIRECT ACTIONS PANEL */}
      <div className="lg:col-span-1 flex flex-col gap-4 overflow-y-auto pr-1">
        <div className="glass-panel p-5 rounded-2xl glow-blue border border-slate-200/50 space-y-4" style={{ backgroundColor: 'rgba(255, 255, 255, 0.7)' }}>
          <div className="flex items-center gap-2 border-b border-slate-200/50 pb-3">
            <Sparkles className="w-5 h-5 text-blue-500 animate-pulse" />
            <h4 className="text-sm font-extrabold text-slate-800 uppercase tracking-wider">Ask Copilot</h4>
          </div>
          <p className="text-[11px] text-slate-500 leading-relaxed">
            Select a structured query below to run automated code audits and receive explainable solutions:
          </p>
        </div>

        <div className="space-y-3">
          {consultantActions.map((action, idx) => (
            <button
              key={idx}
              onClick={() => handleSend(action.query)}
              disabled={isLoading}
              className="w-full text-left glass-card glass-card-hover p-3.5 rounded-xl flex items-center justify-between gap-3 group cursor-pointer disabled:opacity-40 disabled:cursor-not-allowed border-slate-200/50"
            >
              <div className="flex items-center gap-3 min-w-0">
                <div className="w-8 h-8 rounded-lg bg-slate-50 flex items-center justify-center border border-slate-100 shrink-0">
                  {action.icon}
                </div>
                <div className="min-w-0">
                  <span className="text-xs font-bold text-slate-700 group-hover:text-slate-900 transition-all block truncate">
                    {action.label}
                  </span>
                  <span className="text-[10px] text-slate-455 block truncate mt-0.5">{action.desc}</span>
                </div>
              </div>
              <ArrowRight size={13} className="text-slate-400 group-hover:text-blue-500 transition-all shrink-0 group-hover:translate-x-1 duration-300" />
            </button>
          ))}
        </div>
      </div>

      {/* RIGHT COLUMN: INTERACTIVE CONVERSATION FEED */}
      <div className="lg:col-span-2 glass-panel rounded-2xl flex flex-col h-full border border-slate-200/50 relative overflow-hidden" style={{ backgroundColor: 'rgba(255, 255, 255, 0.7)' }}>
        
        {/* Chat Header */}
        <div className="p-4 border-b border-slate-200/50 bg-slate-50/50 flex justify-between items-center">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-lg bg-blue-500/10 border border-blue-500/20 flex items-center justify-center text-blue-500">
              <MessageSquareCode size={18} />
            </div>
            <div>
              <h4 className="text-sm font-bold text-slate-800">AI Consultant Stream</h4>
              <p className="text-[10px] text-slate-550">Auditing codebase via LLM + Semantic RAG</p>
            </div>
          </div>
          <span className="text-[9px] bg-blue-500/10 text-blue-600 font-bold px-2 py-0.5 rounded border border-blue-500/10">
            CONTEXT CONNECTED
          </span>
        </div>

        {/* Message Feed */}
        <div className="flex-1 p-6 overflow-y-auto space-y-4 bg-white/20">
          {messages.map((msg, idx) => {
            const isUser = msg.role === 'user';
            return (
              <div key={idx} className={`flex ${isUser ? 'justify-end' : 'justify-start'}`}>
                <div className={`max-w-[85%] rounded-2xl px-4 py-3 text-xs leading-relaxed ${
                  isUser 
                    ? 'bg-blue-600 text-white rounded-tr-none shadow-md shadow-blue-600/10' 
                    : 'bg-white border border-slate-200/60 text-slate-700 rounded-tl-none shadow-sm shadow-slate-100/40 glow-blue'
                }`}>
                  {/* Parse markdown format */}
                  <div className="space-y-2">
                    {msg.content.split('\n\n').map((para, pIdx) => {
                      if (para.startsWith('### ')) {
                        return <h5 key={pIdx} className="font-extrabold text-slate-800 text-xs mt-3 border-b border-slate-100 pb-1">{para.replace('### ', '')}</h5>;
                      }
                      if (para.startsWith('- ') || para.startsWith('* ')) {
                        return (
                          <ul key={pIdx} className="list-disc pl-4 space-y-1">
                            {para.split('\n').map((li, lIdx) => (
                              <li key={lIdx}>{li.replace(/^[\-\*]\s+/, '')}</li>
                            ))}
                          </ul>
                        );
                      }
                      if (para.startsWith('```')) {
                        return (
                          <pre key={pIdx} className="bg-slate-50 p-2.5 rounded-lg border border-slate-200 text-[10px] text-blue-600 overflow-x-auto font-mono">
                            {para.replace(/```[a-z]*\n|```/g, '')}
                          </pre>
                        );
                      }
                      return <p key={pIdx}>{para}</p>;
                    })}
                  </div>
                  <span className={`text-[8px] mt-1.5 block text-right ${isUser ? 'text-blue-100' : 'text-slate-400'}`}>
                    {msg.timestamp}
                  </span>
                </div>
              </div>
            );
          })}
          {isLoading && (
            <div className="flex justify-start">
              <div className="bg-white border border-slate-200/60 text-slate-500 rounded-2xl rounded-tl-none px-4 py-3 text-xs flex items-center gap-2">
                <Loader2 className="w-3.5 h-3.5 text-blue-500 animate-spin" />
                <span>Consultant is searching code vectors database...</span>
              </div>
            </div>
          )}
          <div ref={scrollRef} />
        </div>

        {/* Input Tray */}
        <div className="p-4 border-t border-slate-200/50 bg-slate-50/50 flex gap-2">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleSend(input)}
            placeholder="Ask about database models, architectural flaws, security issues..."
            className="flex-1 px-4 py-2.5 rounded-xl bg-white border border-slate-200 text-xs text-slate-800 placeholder-slate-400 focus:outline-none focus:border-blue-500/80 focus:ring-1 focus:ring-blue-500/20 transition-all shadow-inner"
          />
          <button
            onClick={() => handleSend(input)}
            className="p-2.5 rounded-xl bg-blue-600 hover:bg-blue-500 text-white flex items-center justify-center transition-all cursor-pointer shadow-md shadow-blue-500/10"
          >
            <Send size={15} />
          </button>
        </div>
      </div>

    </div>
  );
};
