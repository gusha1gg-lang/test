import React, { useState } from 'react';
import { demoWorks } from '../data/mockData';
import { PlannedWork } from '../types';

const WorksList: React.FC = () => {
  const [filterStatus, setFilterStatus] = useState<string>('all');
  const [works, setWorks] = useState<PlannedWork[]>(demoWorks);

  const filteredWorks = filterStatus === 'all'
    ? works
    : works.filter(w => w.status === filterStatus);

  const getStatusBadge = (status: PlannedWork['status']) => {
    const config: Record<PlannedWork['status'], { bg: string; text: string; label: string }> = {
      planned: { bg: 'bg-blue-100', text: 'text-blue-800', label: 'Запланировано' },
      in_progress: { bg: 'bg-yellow-100', text: 'text-yellow-800', label: 'В процессе' },
      completed: { bg: 'bg-green-100', text: 'text-green-800', label: 'Завершено' },
      cancelled: { bg: 'bg-red-100', text: 'text-red-800', label: 'Отменено' },
    };
    const c = config[status];
    return (
      <span className={`px-2 py-1 rounded-full text-xs font-medium ${c.bg} ${c.text}`}>
        {c.label}
      </span>
    );
  };

  const formatDate = (dateStr: string) => {
    return new Date(dateStr).toLocaleDateString('ru-RU', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
    });
  };

  const formatTime = (dateStr: string) => {
    return new Date(dateStr).toLocaleTimeString('ru-RU', {
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  const handleStatusChange = (workId: string, newStatus: PlannedWork['status']) => {
    setWorks(prev => prev.map(w =>
      w.id === workId ? { ...w, status: newStatus } : w
    ));
  };

  return (
    <div className="p-6">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h2 className="text-xl font-bold text-gray-800">📋 Список плановых работ</h2>
          <p className="text-sm text-gray-500 mt-1">Управление зарегистрированными работами</p>
        </div>
        <div className="flex items-center gap-2">
          <select
            value={filterStatus}
            onChange={e => setFilterStatus(e.target.value)}
            className="px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 outline-none"
          >
            <option value="all">Все статусы</option>
            <option value="planned">Запланировано</option>
            <option value="in_progress">В процессе</option>
            <option value="completed">Завершено</option>
            <option value="cancelled">Отменено</option>
          </select>
        </div>
      </div>

      <div className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
        <table className="w-full">
          <thead>
            <tr className="bg-gray-50 border-b border-gray-200">
              <th className="text-left px-4 py-3 text-xs font-medium text-gray-500 uppercase">Работа</th>
              <th className="text-left px-4 py-3 text-xs font-medium text-gray-500 uppercase">Сервис</th>
              <th className="text-left px-4 py-3 text-xs font-medium text-gray-500 uppercase">Период</th>
              <th className="text-left px-4 py-3 text-xs font-medium text-gray-500 uppercase">Статус</th>
              <th className="text-left px-4 py-3 text-xs font-medium text-gray-500 uppercase">Zabbix</th>
              <th className="text-left px-4 py-3 text-xs font-medium text-gray-500 uppercase">Действия</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            {filteredWorks.map(work => (
              <tr key={work.id} className="hover:bg-gray-50 transition-colors">
                <td className="px-4 py-3">
                  <p className="text-sm font-medium text-gray-800">{work.workTitle}</p>
                  {work.description && (
                    <p className="text-xs text-gray-500 mt-0.5 truncate max-w-[200px]">{work.description}</p>
                  )}
                </td>
                <td className="px-4 py-3">
                  <span className="text-sm text-gray-700">{work.serviceName}</span>
                </td>
                <td className="px-4 py-3">
                  <div className="text-sm text-gray-700">
                    <div>{formatDate(work.startTime)}</div>
                    <div className="text-xs text-gray-500">
                      {formatTime(work.startTime)} — {formatTime(work.endTime)}
                    </div>
                  </div>
                </td>
                <td className="px-4 py-3">
                  {getStatusBadge(work.status)}
                </td>
                <td className="px-4 py-3">
                  {work.zabbixExclusionCreated ? (
                    <span className="text-green-600 text-sm">✅ Создано</span>
                  ) : (
                    <span className="text-gray-400 text-sm">—</span>
                  )}
                </td>
                <td className="px-4 py-3">
                  <div className="flex items-center gap-1">
                    {work.status === 'planned' && (
                      <button
                        onClick={() => handleStatusChange(work.id, 'in_progress')}
                        className="px-2 py-1 text-xs bg-yellow-100 text-yellow-800 rounded hover:bg-yellow-200 transition-colors"
                        title="Начать"
                      >
                        ▶ Начать
                      </button>
                    )}
                    {work.status === 'in_progress' && (
                      <button
                        onClick={() => handleStatusChange(work.id, 'completed')}
                        className="px-2 py-1 text-xs bg-green-100 text-green-800 rounded hover:bg-green-200 transition-colors"
                        title="Завершить"
                      >
                        ✓ Завершить
                      </button>
                    )}
                    {(work.status === 'planned' || work.status === 'in_progress') && (
                      <button
                        onClick={() => handleStatusChange(work.id, 'cancelled')}
                        className="px-2 py-1 text-xs bg-red-100 text-red-800 rounded hover:bg-red-200 transition-colors"
                        title="Отменить"
                      >
                        ✕ Отменить
                      </button>
                    )}
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>

        {filteredWorks.length === 0 && (
          <div className="text-center py-12 text-gray-500">
            <p className="text-lg">📭</p>
            <p className="mt-2">Нет работ с выбранным фильтром</p>
          </div>
        )}
      </div>

      {/* Сводка */}
      <div className="mt-4 flex items-center gap-4 text-sm text-gray-500">
        <span>Всего: <strong className="text-gray-700">{filteredWorks.length}</strong></span>
        <span>•</span>
        <span>С исключением в Zabbix: <strong className="text-gray-700">{filteredWorks.filter(w => w.zabbixExclusionCreated).length}</strong></span>
      </div>
    </div>
  );
};

export default WorksList;
