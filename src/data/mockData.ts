import { ServiceNode, PlannedWork } from '../types';

// Демо-данные для дерева сервисов Zabbix
export const demoServices: ServiceNode[] = [
  { id: '1', name: 'IT Инфраструктура', status: 'ok', algorithm: 'all', parentId: null },
  { id: '2', name: 'Почтовый сервер', status: 'ok', parentId: '1' },
  { id: '3', name: 'CRM Система', status: 'ok', algorithm: 'all', parentId: '1' },
  { id: '4', name: 'БД PostgreSQL', status: 'ok', parentId: '3' },
  { id: '5', name: 'ERP Система', status: 'warning', algorithm: 'min_n', parentId: '1' },
  { id: '6', name: 'БД Oracle', status: 'ok', parentId: '5' },
  { id: '7', name: '1С Бухгалтерия', status: 'problem', parentId: '5' },
  { id: '8', name: 'Портал клиентов', status: 'ok', parentId: '1' },
  { id: '9', name: 'Веб-сервер Nginx', status: 'ok', parentId: '8' },
  { id: '10', name: 'Файловый сервер', status: 'ok', parentId: '1' },
];

// Демо-данные для плановых работ
export const demoWorks: PlannedWork[] = [
  {
    id: '1',
    serviceName: 'БД PostgreSQL',
    serviceIdZabbix: '4',
    workTitle: 'Обновление PostgreSQL до версии 16',
    description: 'Плановое обновление СУБД PostgreSQL с версии 15 до 16. Включает бэкап, обновление пакетов, миграцию данных и проверку работоспособности.',
    startTime: '2026-09-15T22:00:00',
    endTime: '2026-09-16T06:00:00',
    status: 'completed',
    zabbixExclusionCreated: true,
    createdBy: 'Admin',
    createdAt: '2026-09-01T10:00:00',
  },
  {
    id: '2',
    serviceName: 'Веб-сервер Nginx',
    serviceIdZabbix: '9',
    workTitle: 'Обновление SSL-сертификатов',
    description: 'Продление и установка новых SSL-сертификатов для портала клиентов.',
    startTime: '2026-09-20T01:00:00',
    endTime: '2026-09-20T03:00:00',
    status: 'planned',
    zabbixExclusionCreated: false,
    createdBy: 'Admin',
    createdAt: '2026-09-05T14:30:00',
  },
  {
    id: '3',
    serviceName: 'CRM Система',
    serviceIdZabbix: '3',
    workTitle: 'Техническое обслуживание CRM',
    description: 'Оптимизация индексов БД, очистка временных таблиц, обновление кэша.',
    startTime: '2026-09-22T23:00:00',
    endTime: '2026-09-23T05:00:00',
    status: 'planned',
    zabbixExclusionCreated: false,
    createdBy: 'Admin',
    createdAt: '2026-09-08T09:15:00',
  },
  {
    id: '4',
    serviceName: '1С Бухгалтерия',
    serviceIdZabbix: '7',
    workTitle: 'Обновление платформы 1С',
    description: 'Обновление платформы 1С:Предприятие до версии 8.3.24. Тестирование совместимости конфигураций.',
    startTime: '2026-09-25T18:00:00',
    endTime: '2026-09-26T08:00:00',
    status: 'in_progress',
    zabbixExclusionCreated: true,
    createdBy: 'Admin',
    createdAt: '2026-09-10T11:00:00',
  },
  {
    id: '5',
    serviceName: 'Почтовый сервер',
    serviceIdZabbix: '2',
    workTitle: 'Миграция почтовых ящиков',
    description: 'Перенос почтовых ящиков на новое хранилище. Работы отменены в связи с переносом на следующий месяц.',
    startTime: '2026-09-18T20:00:00',
    endTime: '2026-09-19T08:00:00',
    status: 'cancelled',
    zabbixExclusionCreated: false,
    createdBy: 'Admin',
    createdAt: '2026-09-03T16:45:00',
  },
  {
    id: '6',
    serviceName: 'Файловый сервер',
    serviceIdZabbix: '10',
    workTitle: 'Расширение дискового пространства',
    description: 'Добавление новых дисков и расширение RAID-массива.',
    startTime: '2026-09-28T22:00:00',
    endTime: '2026-09-29T06:00:00',
    status: 'planned',
    zabbixExclusionCreated: false,
    createdBy: 'Admin',
    createdAt: '2026-09-12T08:30:00',
  },
  {
    id: '7',
    serviceName: 'IT Инфраструктура',
    serviceIdZabbix: '1',
    workTitle: 'Плановое отключение электроснабжения',
    description: 'Тестирование ИБП и генераторов. Все системы будут переведены на резервное питание.',
    startTime: '2026-10-05T10:00:00',
    endTime: '2026-10-05T14:00:00',
    status: 'planned',
    zabbixExclusionCreated: false,
    createdBy: 'Admin',
    createdAt: '2026-09-15T12:00:00',
  },
];

// Утилиты для работы с данными
export function getServicesTree(): { nodes: ServiceNode[]; edges: Array<{ from: string; to: string }> } {
  const edges: Array<{ from: string; to: string }> = [];
  demoServices.forEach(service => {
    if (service.parentId) {
      edges.push({ from: service.parentId, to: service.id });
    }
  });
  return { nodes: demoServices, edges };
}

export function getWorksForMonth(year: number, month: number): PlannedWork[] {
  return demoWorks.filter(work => {
    const start = new Date(work.startTime);
    return start.getFullYear() === year && start.getMonth() === month - 1;
  });
}

export function getStatusLabel(status: PlannedWork['status']): string {
  const labels: Record<PlannedWork['status'], string> = {
    planned: 'Запланировано',
    in_progress: 'В процессе',
    completed: 'Завершено',
    cancelled: 'Отменено',
  };
  return labels[status];
}

export function getStatusColor(status: PlannedWork['status']): string {
  const colors: Record<PlannedWork['status'], string> = {
    planned: '#0d6efd',
    in_progress: '#ffc107',
    completed: '#28a745',
    cancelled: '#dc3545',
  };
  return colors[status];
}
