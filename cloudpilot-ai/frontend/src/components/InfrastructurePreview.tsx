import React, { useState, useEffect } from 'react';
import { FolderOpen, FileCode2, Copy, Check, Download } from 'lucide-react';

interface InfrastructurePreviewProps {
  files: { [path: string]: string };
  downloadUrl: string | null;
}

export const InfrastructurePreview: React.FC<InfrastructurePreviewProps> = ({ files, downloadUrl }) => {
  const filePaths = Object.keys(files);
  const [selectedFile, setSelectedFile] = useState<string>('');
  const [copied, setCopied] = useState<boolean>(false);

  // Automatically select the first file initially
  useEffect(() => {
    if (filePaths.length > 0 && !selectedFile) {
      // Prefer Dockerfile or docker-compose as default selections
      const df = filePaths.find(p => p === 'Dockerfile');
      setSelectedFile(df || filePaths[0]);
    }
  }, [files, filePaths, selectedFile]);

  const handleCopy = () => {
    if (!selectedFile) return;
    navigator.clipboard.writeText(files[selectedFile]);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const fileContent = selectedFile ? files[selectedFile] : '';
  
  // Render line numbers for code editor preview
  const lines = fileContent.split('\n');

  return (
    <div className="glass-panel rounded-2xl glow-cyan overflow-hidden border border-slate-800/40">
      {/* Top Banner Control Bar */}
      <div className="p-4 border-b border-slate-800/40 bg-slate-950/40 flex flex-wrap justify-between items-center gap-4">
        <div className="flex items-center gap-2">
          <FolderOpen size={16} className="text-cyan-400" />
          <span className="text-xs font-bold text-white uppercase tracking-wider">
            Generated Infrastructure Files
          </span>
        </div>
        
        {/* Download ZIP button */}
        {downloadUrl && (
          <a
            href={downloadUrl}
            download
            className="px-4 py-1.5 rounded-lg bg-blue-600 hover:bg-blue-500 text-white font-bold text-xs flex items-center gap-1.5 transition-all shadow-md shadow-blue-500/20 cursor-pointer"
          >
            <Download size={13} />
            Download Deploy ZIP
          </a>
        )}
      </div>

      <div className="grid grid-cols-1 md:grid-cols-4 min-h-[450px]">
        {/* Left Side: Staging Explorer File Tree */}
        <div className="md:col-span-1 border-r border-slate-800/45 p-4 space-y-2 bg-slate-950/20 max-h-[500px] overflow-y-auto">
          {filePaths.map((path) => {
            const isSelected = path === selectedFile;
            
            // Extract basename
            const parts = path.split('/');
            const name = parts[parts.length - 1];
            const folder = parts.length > 1 ? parts.slice(0, -1).join('/') + '/' : '';

            return (
              <button
                key={path}
                onClick={() => setSelectedFile(path)}
                className={`w-full flex items-center gap-2.5 px-3 py-2 rounded-lg text-left text-xs transition-all cursor-pointer ${
                  isSelected 
                    ? 'bg-blue-600/10 text-blue-400 border border-blue-500/20 font-bold' 
                    : 'text-slate-400 hover:text-slate-200 hover:bg-slate-900/40 border border-transparent'
                }`}
              >
                <FileCode2 size={13} className={isSelected ? 'text-blue-400' : 'text-slate-500'} />
                <div className="truncate">
                  {folder && <span className="text-slate-600 block text-[9px] font-semibold leading-none">{folder}</span>}
                  <span className="truncate">{name}</span>
                </div>
              </button>
            );
          })}
          {filePaths.length === 0 && (
            <div className="text-center py-8 text-xs text-slate-500 font-semibold">
              No files generated yet.
            </div>
          )}
        </div>

        {/* Right Side: Code Preview Frame */}
        <div className="md:col-span-3 flex flex-col bg-slate-950/60 font-mono text-xs max-h-[500px] overflow-hidden">
          {selectedFile ? (
            <>
              {/* Code viewer header */}
              <div className="px-5 py-2.5 bg-slate-900/40 border-b border-slate-800/40 flex justify-between items-center">
                <span className="text-[11px] text-slate-400 font-bold tracking-tight">
                  {selectedFile}
                </span>
                <button
                  onClick={handleCopy}
                  className="flex items-center gap-1 text-[10px] font-semibold text-slate-400 hover:text-white px-2.5 py-1 rounded bg-slate-800/50 hover:bg-slate-800 border border-slate-800 hover:border-slate-700 transition-all cursor-pointer"
                >
                  {copied ? (
                    <>
                      <Check size={11} className="text-emerald-400" />
                      <span className="text-emerald-400 font-bold">Copied</span>
                    </>
                  ) : (
                    <>
                      <Copy size={11} />
                      <span>Copy Code</span>
                    </>
                  )}
                </button>
              </div>

              {/* Code text scroll layout */}
              <div className="flex-1 overflow-auto p-4 flex items-start gap-4 select-text leading-relaxed">
                {/* Line numbers column */}
                <div className="text-slate-600 text-right select-none pr-1.5 border-r border-slate-800/50 flex flex-col">
                  {lines.map((_, i) => (
                    <span key={i} className="leading-5">{i + 1}</span>
                  ))}
                </div>
                {/* Code body */}
                <pre className="text-slate-300 overflow-x-auto flex-1 leading-5 pr-2 whitespace-pre">
                  <code>{fileContent}</code>
                </pre>
              </div>
            </>
          ) : (
            <div className="flex-1 flex items-center justify-center text-slate-500 font-semibold italic text-xs py-12">
              Select a file to preview code.
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
