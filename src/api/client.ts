// --- ФАЙЛ: src/api/client.ts ---
// API клиент для работы с FastAPI бэкендом
const API_BASE = '/api';

export interface ServiceNode {
  id: string;
  name: string;
  status: string;
  algorithm?: string;
  parent_id?: string | null;
  children?: string[];
}

export interface PlannedWork {
  id: number;
  service_name: string;
  service_id_zabbix?: string;
  work_title: string;
  description?: string;
  start_time: string;
  end_time: string;
  status: string;
  zabbix_exclusion_created: boolean;
  created_by: string;
  created_at: string;
  updated_at?: string;
}

export interface HealthStatus {
  status: string;
  zabbix_connected: boolean;
  mode: string;
  user?: string;
}

export interface ServicesTree {
  nodes: ServiceNode[];
  edges: Array<{ from: string; to: string }>;
  empty?: boolean;
  message?: string;
  error?: boolean;
}

class ApiClient {
  private async request<T>(endpoint: string, options?: RequestInit): Promise<T> {
    const response = await fetch(`${API_BASE}${endpoint}`, {
      headers: { 'Content-Type': 'application/json' },
      ...options,
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: 'Unknown error' }));
      throw new Error(error.detail || `HTTP ${response.status}`);
    }

    return response.json();
  }

  // Health check
  async getHealth(): Promise<HealthStatus> {
    return this.request<HealthStatus>('/health');
  }

  // Services tree from Zabbix
  async getServicesTree(): Promise<ServicesTree> {
    return this.request<ServicesTree>('/services_tree');
  }

  // Planned works
  async getWorks(status?: string): Promise<PlannedWork[]> {
    const query = status ? `?status=${status}` : '';
    return this.request<PlannedWork[]>(`/works${query}`);
  }

  async createWork(work: {
    service_name: string;
    service_id_zabbix?: string;
    work_title: string;
    description?: string;
    start_time: string;
    end_time: string;
  }): Promise<PlannedWork> {
    return this.request<PlannedWork>('/works', {
      method: 'POST',
      body: JSON.stringify(work),
    });
  }

  async updateWork(id: number, update: { status?: string }): Promise<PlannedWork> {
    return this.request<PlannedWork>(`/works/${id}`, {
      method: 'PATCH',
      body: JSON.stringify(update),
    });
  }

  async deleteWork(id: number): Promise<void> {
    await this.request<void>(`/works/${id}`, { method: 'DELETE' });
  }

  // Calendar
  async getCalendarWorks(year: number, month: number): Promise<PlannedWork[]> {
    return this.request<PlannedWork[]>(`/calendar?year=${year}&month=${month}`);
  }

  // Settings
  async getSettings(): Promise<any> {
    return this.request<any>('/settings');
  }

  async testZabbixConnection(): Promise<{ connected: boolean; message: string }> {
    return this.request<{ connected: boolean; message: string }>('/settings/test', {
      method: 'POST',
    });
  }

  // ============================================
  // Пользователи и группы
  // ============================================

  async getUsers(): Promise<any[]> {
    return this.request<any[]>('/users');
  }

  async getCurrentUser(): Promise<any> {
    return this.request<any>('/users/me');
  }

  async createUser(user: {
    username: string;
    email?: string;
    full_name?: string;
    is_admin: boolean;
    group_ids: number[];
  }): Promise<any> {
    return this.request<any>('/users', {
      method: 'POST',
      body: JSON.stringify(user),
    });
  }

  async updateUser(id: number, data: any): Promise<any> {
    return this.request<any>(`/users/${id}`, {
      method: 'PATCH',
      body: JSON.stringify(data),
    });
  }

  async deleteUser(id: number): Promise<void> {
    await this.request<void>(`/users/${id}`, { method: 'DELETE' });
  }

  async getGroups(): Promise<any[]> {
    return this.request<any[]>('/groups');
  }

  async createGroup(group: {
    name: string;
    description?: string;
    service_ids: string[];
  }): Promise<any> {
    return this.request<any>('/groups', {
      method: 'POST',
      body: JSON.stringify(group),
    });
  }

  async updateGroup(id: number, data: any): Promise<any> {
    return this.request<any>(`/groups/${id}`, {
      method: 'PATCH',
      body: JSON.stringify(data),
    });
  }

  async deleteGroup(id: number): Promise<void> {
    await this.request<void>(`/groups/${id}`, { method: 'DELETE' });
  }

  async getAllServices(): Promise<any[]> {
    return this.request<any[]>('/services/all');
  }

  async syncServices(): Promise<{ status: string; synced: number; message: string }> {
    return this.request<{ status: string; synced: number; message: string }>('/services/sync', {
      method: 'POST',
    });
  }
}

export const api = new ApiClient();
