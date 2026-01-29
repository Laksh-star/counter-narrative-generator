/**
 * API client for Counter-Narrative Generator backend
 */

import axios, { AxiosInstance } from 'axios';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

// Types matching backend schemas
export interface QueryRequest {
  belief: string;
  topics?: string[];
  n_results?: number;
  user_context?: string;
  verbose?: boolean;
}

export interface QueryResponse {
  conventional_wisdom: string;
  topics_filter: string[] | null;
  forethought: Record<string, any>;
  quickaction: Record<string, any>;
  examiner: Record<string, any>;
  metadata: {
    success: boolean;
    total_tokens: {
      prompt: number;
      completion: number;
      total: number;
    };
    execution_time_ms: number;
    errors: string[];
  };
}

export interface StatsResponse {
  total_chunks: number;
  collection_name: string;
  topics?: Record<string, number>;
  sample_chunks?: Array<Record<string, any>>;
}

export interface TopicsResponse {
  topics: string[];
  taxonomy: Record<string, string[]>;
}

export interface HealthResponse {
  status: string;
  version: string;
  vectorstore_loaded: boolean;
  api_key_configured: boolean;
}

export interface ProgressUpdate {
  agent: string;
  status: string;
  message?: string;
  data?: Record<string, any>;
  timestamp: string;
}

class ApiClient {
  private client: AxiosInstance;

  constructor() {
    this.client = axios.create({
      baseURL: `${API_URL}/api`,
      timeout: 600000, // 10 minutes for long-running queries
      headers: {
        'Content-Type': 'application/json',
      },
    });
  }

  /**
   * Check API health
   */
  async health(): Promise<HealthResponse> {
    const response = await this.client.get<HealthResponse>('/health');
    return response.data;
  }

  /**
   * Get available topics
   */
  async getTopics(): Promise<TopicsResponse> {
    const response = await this.client.get<TopicsResponse>('/topics');
    return response.data;
  }

  /**
   * Get vector store statistics
   */
  async getStats(): Promise<StatsResponse> {
    const response = await this.client.get<StatsResponse>('/stats');
    return response.data;
  }

  /**
   * Query for counter-narratives
   */
  async query(request: QueryRequest): Promise<QueryResponse> {
    const response = await this.client.post<QueryResponse>('/query', request);
    return response.data;
  }

  /**
   * Get WebSocket URL for streaming queries
   */
  getWebSocketUrl(): string {
    const wsProtocol = API_URL.startsWith('https') ? 'wss' : 'ws';
    const baseUrl = API_URL.replace(/^https?:\/\//, '');
    return `${wsProtocol}://${baseUrl}/api/query/stream`;
  }
}

// Export singleton instance
export const apiClient = new ApiClient();
