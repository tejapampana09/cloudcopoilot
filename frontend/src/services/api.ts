import type { AnalyzeRequest, AnalyzeResponse, InfrastructureResponse } from '../types';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const getHeaders = () => {
  const token = localStorage.getItem('cloudpilot_token');
  return {
    'Content-Type': 'application/json',
    ...(token ? { 'Authorization': `Bearer ${token}` } : {}),
  };
};

export const api = {
  getApiBaseUrl: () => API_BASE_URL,
  
  // Auth Helpers
  getToken: () => localStorage.getItem('cloudpilot_token'),
  setToken: (token: string) => localStorage.setItem('cloudpilot_token', token),
  clearToken: () => localStorage.removeItem('cloudpilot_token'),
  isAuthenticated: () => !!localStorage.getItem('cloudpilot_token'),

  // Auth Endpoints
  signup: async (email: string, password: string): Promise<any> => {
    const response = await fetch(`${API_BASE_URL}/api/v1/auth/signup`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password }),
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || 'Signup failed.');
    }
    return response.json();
  },

  login: async (email: string, password: string): Promise<string> => {
    const response = await fetch(`${API_BASE_URL}/api/v1/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password }),
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || 'Login failed.');
    }

    const data = await response.json();
    api.setToken(data.access_token);
    return data.access_token;
  },

  getMe: async (): Promise<any> => {
    const response = await fetch(`${API_BASE_URL}/api/v1/auth/me`, {
      method: 'GET',
      headers: getHeaders(),
    });

    if (!response.ok) {
      api.clearToken();
      throw new Error('Session expired.');
    }
    return response.json();
  },

  // Analyzer Endpoints
  analyzeRepository: async (repoUrl: string): Promise<AnalyzeResponse> => {
    const payload: AnalyzeRequest = { repository_url: repoUrl };
    const response = await fetch(`${API_BASE_URL}/api/v1/analyze`, {
      method: 'POST',
      headers: getHeaders(),
      body: JSON.stringify(payload),
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || 'Failed to submit repository for analysis.');
    }

    return response.json();
  },

  getStreamUrl: (taskId: string): string => {
    const token = api.getToken();
    return `${API_BASE_URL}/api/v1/analyze/stream/${taskId}${token ? `?token=${token}` : ''}`;
  },

  getRecentAnalyses: async (): Promise<any[]> => {
    const response = await fetch(`${API_BASE_URL}/api/v1/recent`, {
      headers: getHeaders(),
    });
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
      headers: getHeaders(),
      body: JSON.stringify(payload),
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || 'Failed to trigger infrastructure generation.');
    }

    return response.json();
  },

  getInfrastructureStreamUrl: (generationId: string): string => {
    const token = api.getToken();
    return `${API_BASE_URL}/api/v1/infrastructure/stream/${generationId}${token ? `?token=${token}` : ''}`;
  },

  getInfrastructureDownloadUrl: (generationId: string): string => {
    const token = api.getToken();
    return `${API_BASE_URL}/api/v1/infrastructure/download/${generationId}${token ? `?token=${token}` : ''}`;
  },

  chatWithRepository: async (taskId: string, message: string): Promise<string> => {
    const response = await fetch(`${API_BASE_URL}/api/v1/analyze/chat`, {
      method: 'POST',
      headers: getHeaders(),
      body: JSON.stringify({ task_id: taskId, message }),
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || 'Failed to chat with repository.');
    }

    const data = await response.json();
    return data.response;
  }
};
