import type { AnalyzeRequest, AnalyzeResponse, InfrastructureResponse } from '../types';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export const api = {
  getApiBaseUrl: () => API_BASE_URL,
  
  analyzeRepository: async (repoUrl: string): Promise<AnalyzeResponse> => {
    const payload: AnalyzeRequest = { repository_url: repoUrl };
    const response = await fetch(`${API_BASE_URL}/api/v1/analyze`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(payload),
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || 'Failed to submit repository for analysis.');
    }

    return response.json();
  },

  getStreamUrl: (taskId: string): string => {
    return `${API_BASE_URL}/api/v1/analyze/stream/${taskId}`;
  },

  getRecentAnalyses: async (): Promise<any[]> => {
    const response = await fetch(`${API_BASE_URL}/api/v1/recent`);
    if (!response.ok) {
      throw new Error('Failed to fetch recent analyses.');
    }
    return response.json();
  },

  // AI Infrastructure Generator Endpoints
  generateInfrastructure: async (repoUrl: string): Promise<InfrastructureResponse> => {
    const payload = { repository_url: repoUrl };
    const response = await fetch(`${API_BASE_URL}/api/v1/infrastructure/generate`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(payload),
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || 'Failed to trigger infrastructure generation.');
    }

    return response.json();
  },

  getInfrastructureStreamUrl: (generationId: string): string => {
    return `${API_BASE_URL}/api/v1/infrastructure/stream/${generationId}`;
  },

  getInfrastructureDownloadUrl: (generationId: string): string => {
    return `${API_BASE_URL}/api/v1/infrastructure/download/${generationId}`;
  }
};
