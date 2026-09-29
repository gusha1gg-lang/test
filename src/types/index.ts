export type PageType = 'dashboard' | 'graph' | 'new-work' | 'works-list' | 'calendar' | 'sla-report' | 'settings' | 'users' | 'groups' | 'audit';

export interface User {
  id: number;
  username: string;
  email?: string;
  full_name?: string;
  is_active: boolean;
  is_admin: boolean;
  created_at: string;
  groups: Group[];
}

export interface Group {
  id: number;
  name: string;
  description?: string;
  created_at: string;
  users_count: number;
  services_count: number;
  services: ServiceInfo[];
}

export interface ServiceInfo {
  id: string;
  name: string;
  status: string;
  algorithm?: string;
  parent_id?: string;
}
