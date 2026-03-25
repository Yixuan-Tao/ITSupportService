/**
 * API 客户端模块
 *
 * 基于 fetch 封装后端 API 调用，提供类型安全的接口
 */

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api";

export interface ChatMessage {
  role: "user" | "assistant";
  content: string;
}

export interface ChatRequest {
  message: string;
  conversation_id?: number;
  user_id?: number;
}

export interface ChatResponse {
  response: string;
  conversation_id: number;
  intent?: string;
  references: string[];
}

export interface Ticket {
  id: number;
  title: string;
  category: string;
  priority: string;
  status: string;
  description: string;
  jira_id?: string;
  created_at: string;
}

export interface Document {
  id: number;
  title: string;
  content: string;
  source_type: string;
  created_at: string;
}

class ApiClient {
  private baseUrl: string;

  constructor(baseUrl: string) {
    this.baseUrl = baseUrl;
  }

  private async request<T>(path: string, options?: RequestInit): Promise<T> {
    const response = await fetch(`${this.baseUrl}${path}`, {
      headers: {
        "Content-Type": "application/json",
      },
      ...options,
    });

    if (!response.ok) {
      throw new Error(`API Error: ${response.status}`);
    }

    return response.json();
  }

  get<T>(path: string): Promise<T> {
    return this.request<T>(path);
  }

  post<T>(path: string, data?: unknown): Promise<T> {
    return this.request<T>(path, {
      method: "POST",
      body: data ? JSON.stringify(data) : undefined,
    });
  }
}

const api = new ApiClient(API_BASE_URL);

export const chatApi = {
  sendMessage: (data: ChatRequest) => api.post<ChatResponse>("/chat", data),
  getConversation: (id: number) => api.get<{ messages: ChatMessage[] }>(`/conversations/${id}`),
  listConversations: (skip = 0, limit = 10) =>
    api.get<{ conversations: Array<{ id: number; created_at: string; status: string }> }>(
      `/conversations?skip=${skip}&limit=${limit}`
    ),
};

export interface SyncResponse {
  success: boolean;
  synced?: number;
  updated?: string[];
  error?: string;
}

export const ticketApi = {
  create: (data: Partial<Ticket>) => api.post<Ticket>("/tickets", data),
  get: (id: number) => api.get<Ticket>(`/tickets/${id}`),
  list: (skip = 0, limit = 10) => api.get<Ticket[]>(`/tickets?skip=${skip}&limit=${limit}`),
  sync: () => api.post<SyncResponse>("/tickets/sync"),
};

export const documentApi = {
  create: (data: Partial<Document>) => api.post<Document>("/documents", data),
  list: (skip = 0, limit = 10) =>
    api.get<Document[]>(`/documents?skip=${skip}&limit=${limit}`),
};

export default api;
