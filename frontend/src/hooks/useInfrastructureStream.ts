import { useState, useEffect, useCallback, useRef } from 'react';
import type { AgentLog } from '../types';
import { api } from '../services/api';

export const useInfrastructureStream = () => {
  const [generationId, setGenerationId] = useState<string | null>(null);
  const [status, setStatus] = useState<'idle' | 'generating' | 'completed' | 'failed'>('idle');
  const [progress, setProgress] = useState<number>(0);
  const [logs, setLogs] = useState<AgentLog[]>([]);
  const [generatedFiles, setGeneratedFiles] = useState<{ [path: string]: string }>({});
  const [validationScore, setValidationScore] = useState<number>(0);
  const [validationResults, setValidationResults] = useState<any[]>([]);
  const [detectedFramework, setDetectedFramework] = useState<string>('');
  const [error, setError] = useState<string | null>(null);
  const eventSourceRef = useRef<EventSource | null>(null);
  const statusRef = useRef(status);
  statusRef.current = status;

  const cleanup = useCallback(() => {
    if (eventSourceRef.current) {
      eventSourceRef.current.close();
      eventSourceRef.current = null;
    }
  }, []);

  const startGeneration = useCallback(async (repoUrl: string) => {
    cleanup();
    setStatus('generating');
    setProgress(0);
    setError(null);
    setLogs([]);
    setGeneratedFiles({});
    setValidationScore(0);
    setValidationResults([]);
    setGenerationId(null);

    try {
      const initResponse = await api.generateInfrastructure(repoUrl);
      const gid = initResponse.generation_id;
      setGenerationId(gid);
      setDetectedFramework(initResponse.detected_framework);

      const streamUrl = api.getInfrastructureStreamUrl(gid);
      const es = new EventSource(streamUrl);
      eventSourceRef.current = es;

      es.addEventListener('log', (event: MessageEvent) => {
        try {
          const logData: AgentLog = JSON.parse(event.data);
          
          setLogs((prev) => {
            const existingIdx = prev.findIndex(
              (l) => l.agent === logData.agent && (l.status === 'in_progress' || l.status === 'pending')
            );
            
            if (existingIdx !== -1) {
              const updated = [...prev];
              updated[existingIdx] = logData;
              return updated;
            }
            
            return [...prev, logData];
          });
        } catch (err) {
          console.error('Failed to parse infra stream log', err);
        }
      });

      es.addEventListener('result', (event: MessageEvent) => {
        try {
          const resultData = JSON.parse(event.data);
          if (resultData.status === 'completed') {
            setGeneratedFiles(resultData.generated_files || {});
            setValidationScore(resultData.validation_score || 0);
            setValidationResults(resultData.validation_report?.results || []);
            setProgress(100);
            setStatus('completed');
          } else {
            setError(resultData.error || 'Infrastructure generation failed.');
            setStatus('failed');
          }
          cleanup();
        } catch (err) {
          console.error('Failed to parse infra stream result', err);
          setError('Failed to process generated configurations.');
          setStatus('failed');
          cleanup();
        }
      });

      es.onerror = () => {
        if (statusRef.current === 'generating') {
          setError('Lost connection to infrastructure stream.');
          setStatus('failed');
        }
        cleanup();
      };

    } catch (err: any) {
      setError(err.message || 'Failed to initialize infrastructure generation.');
      setStatus('failed');
      cleanup();
    }
  }, [cleanup]);

  // Handle progress updates based on active logs
  useEffect(() => {
    if (status !== 'generating') return;
    
    // Smooth progress simulation based on completed agent tasks
    const completedCount = logs.filter(l => l.status === 'completed').length;
    const nextProgress = Math.min(10 + completedCount * 12, 95);
    setProgress(nextProgress);
  }, [logs, status]);

  useEffect(() => {
    return () => cleanup();
  }, [cleanup]);

  return {
    generationId,
    status,
    progress,
    logs,
    generatedFiles,
    validationScore,
    validationResults,
    detectedFramework,
    error,
    startGeneration,
    downloadUrl: generationId ? api.getInfrastructureDownloadUrl(generationId) : null,
    reset: () => {
      cleanup();
      setStatus('idle');
      setProgress(0);
      setLogs([]);
      setGeneratedFiles({});
      setValidationScore(0);
      setValidationResults([]);
      setError(null);
      setGenerationId(null);
    }
  };
};
