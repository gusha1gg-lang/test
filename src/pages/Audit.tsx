import React, { useState, useEffect } from 'react';
import { api } from '../api/client';

const Audit: React.FC = () => {
  const [logs, setLogs] = useState<any[]>([]);
  const [stats, setStats] = useState<any>(null);
  const [users, setUsers] = useState<string[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  // Фильтры
  const [filterUser, setFilterUser] = useState('');
  const [filterAction, setFilterAction] = useState('');
  const [filterResource, setFilterResource] = useState('');
  const [limit, setLimit] = useState(100);

  useEffect(() => {
    loadData();
  }, [filterUser, filterAction, filterResource, limit]);

  const loadData = async () => {
    setLoading(true);
    setError('');
    try {
      const [logsData, statsData, usersData] = await Promise.all([
        api.getAuditLogs({
          limit,
          username: filterUser || undefined,
          action: filterAction || undefined,
          resource_type: filterResource || undefined,
        }),
        api.getAuditStats(7),
        api.getAuditUsers(),
      ]);
      setLogs(logsData);
      setStats(statsData);
      setUsers(usersData);
    } catch (e: any) {
      setError(e.message || 'Ошибка загрузки');
    } finally {
      setLoading(false);
    }
  };

  const formatDateTime = (dateStr: string) => {
    return new Date(dateStr).toLocaleString('ru-RU', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
    });
  };

  const getActionBadge = (action: string) => {
    const config: Record<string, { bg: string; text: string; icon: string }> = {
      create: { bg: 'bg-green-100', text: 'text-green-800', icon: '➕' },
      update: { bg: 'bg-blue-100', text: 'text-blue-800', icon: '✏️' },
      delete: { bg: 'bg-red-100', text: 'text-red-800', icon: '🗑️' },
      login: { bg: 'bg-purple-100', text: 'text-purple-800', icon: '🔐' },
      logout: { bg: 'bg-gray-100', text: 'text-gray-800', icon: '🚪' },
    };
    const c = config[action] || { bg: 'bg-gray-100', text: 'text-gray-800', icon: '❓' };
    return (
      <span className={`px-2 py-1 rounded-full text-xs font-medium ${c.bg} ${c.text}`}>
        {c.icon} {action}
      </span>
    );
  };

  const getResourceBadge = (type: string) => {
    const config: Record<string, string> = {
      work: 'bg-indigo-100 text-indigo-800',
      user: 'bg-pink-100 text-pink-800',
      group: 'bg-yellow-100 text-yellow-800',
      service: 'bg-teal-100 text-teal-800',
    };
    const className = config[type] || 'bg-gray-100 text-gray-800';
    return (
      <span className={`px-2 py-1 rounded-full text-xs font-medium ${className}`}>
        {type}
      </span>
    );
  };

  if (loading) {
    return (
      <div className="p-6 flex items-center justify-center h-64">
        <div className="animate-spin w-8 h-8 border-4 border-blue-600 border-t-transparent rounded-full"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-6">
        <div className="bg-red-50 border border-red-200 rounded-lg p-6 text-center">
          <span className="text-4xl mb-4 block">❌</span>
          <h3 className="text-lg font-bold text-red-800 mb-2">Ошибка загрузки</h3>
          <p className="text-red-600 mb-4">{error}</p>
          <p className="text-sm text-red-500">
            Убедитесь, что у вас есть права администратора для просмотра аудита.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="p-6">
      <div className="mb-6">
        <h2 className="text-xl font-bold text-gray-800">📝 Аудит-лог</h2>
        <p className="text-sm text-gray-500 mt-1">История всех действий пользователей в системе</p>
      </div>

      {/* Статистика */}
      {stats && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
          <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-4">
            <p className="text-sm text-gray-500">Действий за 7 дней</p>
            <p className="text-2xl font-bold text-gray-800 mt-1">{stats.total_actions}</p>
          </div>
          <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-4">
            <p className="text-sm text-gray-500">Создано</p>
            <p className="text-2xl font-bold text-green-600 mt-1">{stats.actions_by_type?.create || 0}</p>
          </div>
          <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-4">
            <p className="text-sm text-gray-500">Изменено</p>
            <p className="text-2xl font-bold text-blue-600 mt-1">{stats.actions_by_type?.update || 0}</p>
          </div>
          <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-4">
            <p className="text-sm text-gray-500">Удалено</p>
            <p className="text-2xl font-bold text-red-600 mt-1">{stats.actions_by_type?.delete || 0}</p>
          </div>
        </div>
      )}

      {/* Фильтры */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-4 mb-6">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div>
            <label className="block text-xs font-medium text-gray-600 mb-1">Пользователь</label>
            <select
              value={filterUser}
              onChange={e => setFilterUser(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm"
            >
              <option value="">Все</option>
              {users.map(u => (
                <option key={u} value={u}>{u}</option>
              ))}
            </select>
          </div>
          <div>
            <label className="block text-xs font-medium text-gray-600 mb-1">Действие</label>
            <select
              value={filterAction}
              onChange={e => setFilterAction(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm"
            >
              <option value="">Все</option>
              <option value="create">Создание</option>
              <option value="update">Изменение</option>
              <option value="delete">Удаление</option>
            </select>
          </div>
          <div>
            <label className="block text-xs font-medium text-gray-600 mb-1">Тип ресурса</label>
            <select
              value={filterResource}
              onChange={e => setFilterResource(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm"
            >
              <option value="">Все</option>
              <option value="work">Плановые работы</option>
              <option value="user">Пользователи</option>
              <option value="group">Группы</option>
              <option value="service">Сервисы</option>
            </select>
          </div>
          <div>
            <label className="block text-xs font-medium text-gray-600 mb-1">Записей</label>
            <select
              value={limit}
              onChange={e => setLimit(Number(e.target.value))}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm"
            >
              <option value={50}>50</option>
              <option value={100}>100</option>
              <option value={200}>200</option>
              <option value={500}>500</option>
            </select>
          </div>
        </div>
      </div>

      {/* Таблица логов */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
        {logs.length === 0 ? (
          <div className="text-center py-12 text-gray-500">
            <p className="text-3xl mb-2">📭</p>
            <p>Нет записей в аудит-логе</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="bg-gray-50 border-b border-gray-200">
                  <th className="text-left px-4 py-3 text-xs font-medium text-gray-500 uppercase">Время</th>
                  <th className="text-left px-4 py-3 text-xs font-medium text-gray-500 uppercase">Пользователь</th>
                  <th className="text-left px-4 py-3 text-xs font-medium text-gray-500 uppercase">Действие</th>
                  <th className="text-left px-4 py-3 text-xs font-medium text-gray-500 uppercase">Ресурс</th>
                  <th className="text-left px-4 py-3 text-xs font-medium text-gray-500 uppercase">Объект</th>
                  <th className="text-left px-4 py-3 text-xs font-medium text-gray-500 uppercase">IP</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {logs.map(log => (
                  <tr key={log.id} className="hover:bg-gray-50">
                    <td className="px-4 py-3 text-sm text-gray-600 whitespace-nowrap">
                      {formatDateTime(log.timestamp)}
                    </td>
                    <td className="px-4 py-3">
                      <span className="text-sm font-medium text-gray-800">{log.username}</span>
                    </td>
                    <td className="px-4 py-3">
                      {getActionBadge(log.action)}
                    </td>
                    <td className="px-4 py-3">
                      {getResourceBadge(log.resource_type)}
                    </td>
                    <td className="px-4 py-3">
                      <div>
                        <p className="text-sm text-gray-800">{log.resource_name || '—'}</p>
                        {log.resource_id && (
                          <p className="text-xs text-gray-500">ID: {log.resource_id}</p>
                        )}
                      </div>
                    </td>
                    <td className="px-4 py-3 text-sm text-gray-500 font-mono">
                      {log.ip_address || '—'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Информация */}
      <div className="mt-4 text-sm text-gray-500">
        Показано: <strong>{logs.length}</strong> записей
      </div>
    </div>
  );
};

export default Audit;
