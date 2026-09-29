// Типы данных для SLA Planner

export interface ServiceNode {
  id: string;
  name: string;
  status: 'ok' | 'warning' | 'problem';
  algorithm?: 'all' | 'min_n' | 'percent';
  parentId?: string | null;
  children?: string[];
}

export interface PlannedWork {
  id: string;
  serviceName: string;
  serviceIdZabbix?: string;
  workTitle: string;
  description?: string;
  startTime: string; // ISO string
  endTime: string;   // ISO string
  status: 'planned' | 'in_progress' | 'completed' | 'cancelled';
  zabbixExclusionCreated: boolean;
  createdBy: string;
  createdAt: string;
}

export interface ZabbixSettings {
  url: string;
  username: string;
  password: string;
  slaName: string;
  connected: boolean;
}

export type PageType = 'dashboard' | 'graph' | 'new-work' | 'works-list' | 'calendar' | 'sla-report' | 'settings' | 'backend-docs';
