import React, { useState, useRef, useEffect } from 'react';
import { Send, MessageSquareCode, Sparkles, Loader2 } from 'lucide-react';
import type { AnalysisResult } from '../types';

interface Message {
  role: 'user' | 'assistant';
  content: string;
  timestamp: string;
}

interface AIConsultantChatProps {
  result: AnalysisResult;
}

export const AIConsultantChat: React.FC<AIConsultantChatProps> = ({ result }) => {
  const [messages, setMessages] = useState<Message[]>([
    {
      role: 'assistant',
      content: `Hello! I am your **AI Technical Consultant**. I have audited your repository **${result.repository_owner}/${result.repository_name}**.\n\nYou can ask me details about the codebase layers, ORM configurations, estimated bottlenecks, database options, or request custom Terraform setups. How can I assist you today?`,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    }
  ]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);

  const presets = [
    "Explain architecture boundaries",
    "Highlight database bottlenecks",
    "Explain environment dependencies",
    "Propose Terraform VPC structure"
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
      // For now, we simulate consultant answers based on real metadata.
      // In Phase 3, this will be connected to the backend RAG semantic engine.
      await new Promise((resolve) => setTimeout(resolve, 1500));
      
      let answer = "";
      const text = textToSend.toLowerCase();

      if (text.includes("boundary") || text.includes("architecture") || text.includes("structure")) {
        answer = `### Repository Architectural Boundaries\n\n` +
                 `Based on the analysis, this is a **${result.metadata.frontend.length > 0 && result.metadata.backend.length > 0 ? "Fullstack" : result.metadata.backend.length > 0 ? "Backend" : "Frontend"}** project structure:\n\n` +
                 `- **Frontend Layer:** ${result.metadata.frontend.join(', ') || 'None detected'}\n` +
                 `- **Backend Service Layer:** ${result.metadata.backend.join(', ') || 'None detected'}\n` +
                 `- **Databases:** ${result.metadata.databases.join(', ') || 'None configured'}\n\n` +
                 `The recommended AWS target is **${result.recommendation.target}** due to container and scaling readiness.`;
      } else if (text.includes("bottleneck") || text.includes("risk") || text.includes("issue")) {
        const has_sqlite = result.metadata.databases.includes("SQLite");
        const has_uploads = result.metadata.infrastructure_files.some(f => f.toLowerCase().includes("multer") || f.toLowerCase().includes("upload"));
        
        answer = `### Audited Repository Bottlenecks\n\n` +
                 `Here are the core concerns identified during repository static scanning:\n\n` +
                 `1. **Stateless Scale Constraints:** ${has_sqlite ? "Uses SQLite which locks writes under concurrency and blocks container scaling." : "None. PostgreSQL/MySQL allows scaling."}\n` +
                 `2. **Stateful Writes:** ${has_uploads ? "Local file upload operations detected. These will disappear when containers scale horizontally." : "Stateless file upload handlers. Recommend using Amazon S3."}\n` +
                 `3. **Environment Template:** ${result.metadata.env_variables.length > 0 ? "Has env configs. Ensure no secrets are hardcoded in the codebase." : "No env templates detected."}`;
      } else if (text.includes("terraform") || text.includes("vpc") || text.includes("blueprint")) {
        answer = `### Proposed Terraform Configuration Outline\n\n` +
                 `Here is the recommended IaC configuration setup for **${result.recommendation.target}**:\n\n` +
                 `\`\`\`hcl\n` +
                 `# vpc.tf\n` +
                 `resource "aws_vpc" "main" {\n` +
                 `  cidr_block           = "10.0.0.0/16"\n` +
                 `  enable_dns_hostnames = true\n` +
                 `}\n\n` +
                 `# compute.tf\n` +
                 `# Configures AWS ECS Fargate or App Runner resources matching: ${result.recommendation.target}\n` +
                 `\`\`\`\n\n` +
                 `You can download the full package files zip from the **Deployments** tab!`;
      } else {
        answer = `### Consultant Analysis\n\n` +
                 `I have analyzed your query: *"${textToSend}"*.\n\n` +
                 `- **Languages audited:** ${result.metadata.languages.map(l => l.name).join(', ')}\n` +
                 `- **Frameworks active:** ${result.metadata.frameworks.join(', ') || 'None'}\n` +
                 `- **Primary compute host:** ${result.recommendation.target}\n\n` +
                 `Feel free to ask details on ORM settings, cost calculations, database configs, or custom Terraform setups.`;
      }

      const assistantMsg: Message = {
        role: 'assistant',
        content: answer,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
      };
      setMessages((prev) => [...prev, assistantMsg]);
    } catch (err) {
      setMessages((prev) => [
        ...prev,
        {
          role: 'assistant',
          content: 'Sorry, I encountered an error processing your query. Please try again.',
          timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
        }
      ]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="glass-panel rounded-2xl glow-blue flex flex-col h-[600px] border border-slate-800/40 relative overflow-hidden">
      {/* Header */}
      <div className="p-4 border-b border-slate-800/40 bg-slate-900/20 flex justify-between items-center">
        <div className="flex items-center gap-2.5">
          <div className="w-8 h-8 rounded-lg bg-blue-600/10 border border-blue-500/20 flex items-center justify-center text-blue-400">
            <MessageSquareCode size={18} />
          </div>
          <div>
            <h4 className="text-sm font-bold text-white flex items-center gap-1.5">
              AI Technical Consultant
              <Sparkles size={12} className="text-violet-400" />
            </h4>
            <p className="text-[10px] text-slate-500">Auditing {result.repository_owner}/{result.repository_name}</p>
          </div>
        </div>
        <span className="text-[9px] bg-blue-500/10 text-blue-400 font-bold px-2 py-0.5 rounded border border-blue-500/10">
          RAG CONTEXT ACTIVE
        </span>
      </div>

      {/* Message Feed */}
      <div className="flex-1 p-6 overflow-y-auto space-y-4">
        {messages.map((msg, idx) => {
          const isUser = msg.role === 'user';
          return (
            <div key={idx} className={`flex ${isUser ? 'justify-end' : 'justify-start'}`}>
              <div className={`max-w-[80%] rounded-2xl px-4 py-3 text-xs leading-relaxed ${
                isUser 
                  ? 'bg-blue-600 text-white rounded-tr-none' 
                  : 'bg-slate-900/60 border border-slate-800/60 text-slate-200 rounded-tl-none'
              }`}>
                {/* Parse simple markdown format */}
                <div className="space-y-2">
                  {msg.content.split('\n\n').map((para, pIdx) => {
                    if (para.startsWith('### ')) {
                      return <h5 key={pIdx} className="font-bold text-white text-xs mt-2">{para.replace('### ', '')}</h5>;
                    }
                    if (para.startsWith('- ')) {
                      return (
                        <ul key={pIdx} className="list-disc pl-4 space-y-1">
                          {para.split('\n').map((li, lIdx) => (
                            <li key={lIdx}>{li.replace('- ', '')}</li>
                          ))}
                        </ul>
                      );
                    }
                    if (para.startsWith('```')) {
                      return (
                        <pre key={pIdx} className="bg-slate-950 p-2.5 rounded-lg border border-slate-800/50 text-[10px] text-cyan-400 overflow-x-auto font-mono">
                          {para.replace(/```[a-z]*\n|```/g, '')}
                        </pre>
                      );
                    }
                    return <p key={pIdx}>{para}</p>;
                  })}
                </div>
                <span className={`text-[8px] mt-1.5 block text-right ${isUser ? 'text-blue-200' : 'text-slate-500'}`}>
                  {msg.timestamp}
                </span>
              </div>
            </div>
          );
        })}
        {isLoading && (
          <div className="flex justify-start">
            <div className="bg-slate-900/60 border border-slate-800/60 text-slate-400 rounded-2xl rounded-tl-none px-4 py-3 text-xs flex items-center gap-2">
              <Loader2 className="w-3.5 h-3.5 text-blue-400 animate-spin" />
              <span>Consultant is analyzing codebase index...</span>
            </div>
          </div>
        )}
        <div ref={scrollRef} />
      </div>

      {/* Preset Queries */}
      <div className="px-6 py-2 flex gap-2 flex-wrap border-t border-slate-800/20 bg-slate-950/20">
        {presets.map((preset, idx) => (
          <button
            key={idx}
            onClick={() => handleSend(preset)}
            className="text-[10px] bg-slate-900/40 hover:bg-slate-800 border border-slate-800/60 hover:border-slate-700 text-slate-400 hover:text-slate-200 px-2.5 py-1 rounded-full transition-all cursor-pointer"
          >
            {preset}
          </button>
        ))}
      </div>

      {/* Input Tray */}
      <div className="p-4 border-t border-slate-800/40 bg-slate-900/20 flex gap-2">
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && handleSend(input)}
          placeholder="Ask about database models, VPC configurations, cost assumptions..."
          className="flex-1 px-4 py-2.5 rounded-xl bg-slate-950 border border-slate-800 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-blue-500/80 focus:ring-1 focus:ring-blue-500/20 transition-all"
        />
        <button
          onClick={() => handleSend(input)}
          className="p-2.5 rounded-xl bg-blue-600 hover:bg-blue-500 text-white flex items-center justify-center transition-all cursor-pointer shadow-md shadow-blue-500/10"
        >
          <Send size={15} />
        </button>
      </div>
    </div>
  );
};
