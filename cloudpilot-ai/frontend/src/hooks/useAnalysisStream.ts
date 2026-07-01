import { useState, useEffect, useCallback, useRef } from 'react';
import type { AgentLog, AnalysisResult } from '../types';
import { api } from '../services/api';

export const useAnalysisStream = () => {
  const [taskId, setTaskId] = useState<string | null>(null);
  const [status, setStatus] = useState<'idle' | 'analyzing' | 'completed' | 'failed'>('idle');
  const [logs, setLogs] = useState<AgentLog[]>([]);
  const [result, setResult] = useState<AnalysisResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const eventSourceRef = useRef<EventSource | null>(null);

  const cleanup = useCallback(() => {
    if (eventSourceRef.current) {
      eventSourceRef.current.close();
      eventSourceRef.current = null;
    }
  }, []);

  const startAnalysis = useCallback(async (repoUrl: string) => {
    cleanup();
    setStatus('analyzing');
    setError(null);
    setResult(null);
    setLogs([]);
    setTaskId(null);

    try {
      const response = await api.analyzeRepository(repoUrl);
      const tid = response.task_id;
      setTaskId(tid);

      // Start EventSource
      const streamUrl = api.getStreamUrl(tid);
      const es = new EventSource(streamUrl);
      eventSourceRef.current = es;

      es.addEventListener('log', (event: MessageEvent) => {
        try {
          const logData: AgentLog = JSON.parse(event.data);
          
          setLogs((prev) => {
            // Check if there is an existing log for this agent with in-progress/pending state, and update it
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
          console.error('Failed to parse stream log', err);
        }
      });

      es.addEventListener('result', (event: MessageEvent) => {
        try {
          const resultData: AnalysisResult = JSON.parse(event.data);
          if (resultData.status === 'completed') {
            setResult(resultData);
            setStatus('completed');
          } else {
            setError(resultData.error || 'Repository analysis failed.');
            setStatus('failed');
          }
          cleanup();
        } catch (err) {
          console.error('Failed to parse stream result', err);
          setError('Failed to process analysis results.');
          setStatus('failed');
          cleanup();
        }
      });

      es.onerror = (err) => {
        console.error('EventSource connection error:', err);
        // Sometimes EventSource disconnects after finishing, which is normal.
        // But if it disconnects during analysis:
        if (status === 'analyzing') {
          setError('Lost connection to analysis stream.');
          setStatus('failed');
        }
        cleanup();
      };

    } catch (err: any) {
      setError(err.message || 'An error occurred while starting analysis.');
      setStatus('failed');
      cleanup();
    }
  }, [cleanup, status]);

  useEffect(() => {
    return () => cleanup();
  }, [cleanup]);

  return {
    taskId,
    status,
    logs,
    result,
    error,
    startAnalysis,
    reset: () => {
      cleanup();
      setStatus('idle');
      setResult(null);
      setLogs([]);
      setError(null);
      setTaskId(null);
    }
  };
};
