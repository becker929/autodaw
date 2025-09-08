import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Types
export interface Session {
  id: string;
  name: string;
  target_frequency: number;
  population_size: number;
  current_generation: number;
  status: string;
  config?: any;
  created_at: string;
  updated_at: string;
}

export interface Solution {
  id: string;
  population_id: string;
  parameters: {
    octave: number;
    fine_tuning: number;
  };
  fitness?: number;
  rank?: number;
  audio_file_id?: string;
  bt_strength?: {
    strength: number;
    confidence_interval_lower?: number;
    confidence_interval_upper?: number;
  };
}

export interface AudioFile {
  id: string;
  filename: string;
  filepath: string;
  duration?: number;
  metadata?: any;
}

export interface Comparison {
  comparison_id: string;
  solution_a: {
    id: string;
    parameters: any;
    audio_file: AudioFile;
  };
  solution_b: {
    id: string;
    parameters: any;
    audio_file: AudioFile;
  };
}

export interface Population {
  id: string;
  session_id: string;
  generation: number;
  solution_count: number;
  created_at: string;
}

export interface PopulationWithSolutions {
  population_id: string;
  solutions: Solution[];
}

export interface Stats {
  total_comparisons: number;
  completed_comparisons: number;
  remaining_comparisons: number;
  preference_distribution: { [key: string]: number };
  average_confidence: number;
}

// API functions
export const sessionAPI = {
  create: async (data: {
    name: string;
    target_frequency?: number;
    population_size?: number;
    config?: any;
  }): Promise<{ session_id: string; session: Session }> => {
    const response = await api.post('/api/sessions', data);
    return response.data;
  },

  get: async (sessionId: string): Promise<Session> => {
    const response = await api.get(`/api/sessions/${sessionId}`);
    return response.data;
  },

  list: async (): Promise<Session[]> => {
    const response = await api.get('/api/sessions');
    return response.data;
  },

  getPopulations: async (sessionId: string): Promise<Population[]> => {
    const response = await api.get(`/api/sessions/${sessionId}/populations`);
    return response.data;
  },
};

export const populationAPI = {
  initialize: async (sessionId: string): Promise<any> => {
    const response = await api.post('/api/populations/initialize', {
      session_id: sessionId,
    });
    return response.data;
  },

  get: async (populationId: string): Promise<PopulationWithSolutions> => {
    const response = await api.get(`/api/populations/${populationId}`);
    return response.data;
  },
};

export const comparisonAPI = {
  getNext: async (): Promise<{ comparison?: Comparison; message?: string }> => {
    const response = await api.get('/api/comparisons/next');
    return response.data;
  },

  submitPreference: async (
    comparisonId: string,
    preference: 'a' | 'b',
    confidence: number,
    notes?: string
  ): Promise<{ message: string }> => {
    const response = await api.post(`/api/comparisons/${comparisonId}/preference`, {
      preference,
      confidence,
      notes,
    });
    return response.data;
  },

  get: async (comparisonId: string): Promise<any> => {
    const response = await api.get(`/api/comparisons/${comparisonId}`);
    return response.data;
  },
};

export const audioAPI = {
  getStreamUrl: (fileId: string): string => {
    return `${API_BASE_URL}/api/audio/${fileId}/stream`;
  },

  getInfo: async (fileId: string): Promise<AudioFile> => {
    const response = await api.get(`/api/audio/${fileId}`);
    return response.data;
  },

  list: async (): Promise<AudioFile[]> => {
    const response = await api.get('/api/audio-files');
    return response.data;
  },
};

export const statsAPI = {
  get: async (): Promise<Stats> => {
    const response = await api.get('/api/stats');
    return response.data;
  },
};

export default api;
