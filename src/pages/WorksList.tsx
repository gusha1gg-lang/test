import React, { useState, useEffect } from 'react';
import { api, PlannedWork } from '../api/client';

const WorksList: React.FC = () => {
  const [works, setWorks] = useState<PlannedWork[]>([]);
  const [filterStatus, setFilterStatus] = useState<string>('');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadWorks();
  }, [filterStatus]);

  const loadWorks = async () => {
    setLoading(true);
    try {
      const data = await api.getWorks(filterStatus || undefined);
      setWorks(data);
    } catch (e) {
      setWorks([]);
    } finally {
      setLoading(false);
    }
  };

  const handleStatusChange = async (workId: number, newStatus: string) => {
    try {
      await api.updateWork(workId, { status: newStatus });
      await loadWorks();
    } catch (e: any) {
      alert(`Ошибка: ${e.message}`);
    }
  };

  const handleDelete = async (workId: number) => {
    if (!confirm('Удалить плановую работу?')) return;
    try {
      await api.deleteWork(workId);
      await loadWorks();
    } catch (e: any) {
      alert(`Ошибка: ${e.message}`);
    }
  };

  const getStatusBadge = (status: string) => {
    const config: Record<string, { bg: string; text: string; label: string }> = {
      planned: { bg: 'bg-blue-100', text: 'text-blue-800', label: 'Запланировано' },
      in_progress: { bg: 'bg-yellow-100', text: 'text-yellow-800', label: 'В процессе' },
      completed: { bg: 'bg-green-100', text: 'text-green-800', label: 'Завершено' },
      cancelled: { bg: 'bg-red-100', text: 'text-red-800', label: 'Отменено' },
    };
    const c = config[status] || { bg: 'bg-gray-100', text: 'text-gray-800', label: status };
    return <span className={`px-2 py-1 rounded-full text-xs font-medium ${c.bg} ${c.text}`}>{c.label}</span>;
  };

  const formatDate = (d: string) => new Date(d).toLocaleDateString('ru-RU', { day: '2-digit', month: '2-digit', year: 'numeric' });
  const formatTime = (d: string) => new Date(d).toLocaleTimeString('ru-RU', { hour: '2-digit', minute: '2-digit' });

  return (
    <div className="p-6">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h2 className="text-xl font-bold text-gray-800">📋 Список плановых работ</h2>
          <p className="text-sm text-gray-500 mt-1">Управление зарегистрированными работами</p>
        </div>
        <select
          value={filterStatus}
          onChange={e => setFilterStatus(e.target.value)}
          className="px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 outline-none"
        >
          <option value="">Все статусы</option>
          <option value="planned">Запланировано</option>
          <option value="in_progress">В процессе</option>
          <option value="completed">Завершено</option>
          <option value="cancelled">Отменено</option>
        </select>
      </div>

      <div className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
        {loading ? (
          <div className="text-center py-12 text-gray-500">Загрузка...</div>
        ) : works.length === 0 ? (
          <div className="text-center py-12 text-gray-500">
            <p className="text-3xl mb-2">📭</p>
            <p>Нет плановых работ</p>
          </div>
        ) : (
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
              {works.map(work => (
                <tr key={work.id} className="hover:bg-gray-50">
                  <td className="px-4 py-3">
                    <p className="text-sm font-medium text-gray-800">{work.work_title}</p>
                    {work.description && <p className="text-xs text-gray-500 mt-0.5 truncate max-w-[200px]">{work.description}</p>}
                  </td>
                  <td className="px-4 py-3 text-sm text-gray-700">{work.service_name}</td>
                  <td className="px-4 py-3">
                    <div className="text-sm text-gray-700">
                      <div>{formatDate(work.start_time)}</div>
                      <div className="text-xs text-gray-500">{formatTime(work.start_time)} — {formatTime(work.end_time)}</div>
                    </div>
                  </td>
                  <td className="px-4 py-3">{getStatusBadge(work.status)}</td>
                  <td className="px-4 py-3">
                    {work.zabbix_exclusion_created
                      ? <span className="text-green-600 text-sm">✅ Создано</span>
                      : <span className="text-gray-400 text-sm">—</span>}
                  </td>
                  <td className="px-4 py-3">
                    <div className="flex items-center gap-1">
                      {work.status === 'planned' && (
                        <button onClick={() => handleStatusChange(work.id, 'in_progress')} className="px-2 py-1 text-xs bg-yellow-100 text-yellow-800 rounded hover:bg-yellow-200">▶ Начать</button>
                      )}
                      {work.status === 'in_progress' && (
                        <button onClick={() => handleStatusChange(work.id, 'completed')} className="px-2 py-1 text-xs bg-green-100 text-green-800 rounded hover:bg-green-200">✓ Завершить</button>
                      )}
                      {(work.status === 'planned' || work.status === 'in_progress') && (
                        <button onClick={() => handleStatusChange(work.id, 'cancelled')} className="px-2 py-1 text-xs bg-red-100 text-red-800 rounded hover:bg-red-200">✕ Отменить</button>
                      )}
                      <button onClick={() => handleDelete(work.id)} className="px-2 py-1 text-xs bg-gray-100 text-gray-600 rounded hover:bg-gray-200">🗑</button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {!loading && works.length > 0 && (
        <div className="mt-4 text-sm text-gray-500">
          Всего: <strong className="text-gray-700">{works.length}</strong> | 
          С исключением в Zabbix: <strong className="text-gray-700">{works.filter(w => w.zabbix_exclusion_created).length}</strong>
        </div>
      )}
    </div>
  );
};

export default WorksList;
