// --- ФАЙЛ: src/pages/Dashboard.tsx ---
import React, { useEffect, useState } from 'react';
import { api, HealthStatus, PlannedWork } from '../api/client';

const Dashboard: React.FC = () => {
  const [health, setHealth] = useState<HealthStatus | null>(null);
  const [works, setWorks] = useState<PlannedWork[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    setLoading(true);
    setError('');
    try {
      const [healthData, worksData] = await Promise.all([
        api.getHealth(),
        api.getWorks(),
      ]);
      setHealth(healthData);
      setWorks(worksData);
    } catch (e: any) {
      setError(e.message || 'Не удалось подключиться к серверу');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="p-6 flex items-center justify-center h-64">
        <div className="text-center">
          <div className="animate-spin w-8 h-8 border-4 border-blue-600 border-t-transparent rounded-full mx-auto mb-4"></div>
          <p className="text-gray-500">Загрузка данных...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-6">
        <div className="bg-red-50 border border-red-200 rounded-lg p-6 text-center">
          <span className="text-4xl mb-4 block">❌</span>
          <h3 className="text-lg font-bold text-red-800 mb-2">Ошибка подключения</h3>
          <p className="text-red-600 mb-4">{error}</p>
          <p className="text-sm text-red-500 mb-4">
            Убедитесь что FastAPI бэкенд запущен и доступен.
          </p>
          <button
            onClick={loadData}
            className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700"
          >
            🔄 Повторить
          </button>
        </div>
      </div>
    );
  }

  const plannedWorks = works.filter(w => w.status === 'planned');
  const inProgressWorks = works.filter(w => w.status === 'in_progress');
  const completedWorks = works.filter(w => w.status === 'completed');
  const cancelledWorks = works.filter(w => w.status === 'cancelled');

  const upcomingWorks = works
    .filter(w => w.status === 'planned' || w.status === 'in_progress')
    .sort((a, b) => new Date(a.start_time).getTime() - new Date(b.start_time).getTime())
    .slice(0, 5);

  return (
    <div className="p-6 space-y-6">
      {/* Статус подключения */}
      {!health?.zabbix_connected && (
        <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4 flex items-start gap-3">
          <span className="text-xl">⚠️</span>
          <div>
            <p className="font-medium text-yellow-800">Zabbix не подключён</p>
            <p className="text-sm text-yellow-700">
              Проверьте настройки подключения в разделе «Настройки». Данные о сервисах недоступны.
            </p>
          </div>
        </div>
      )}

      {health?.zabbix_connected && (
        <div className="bg-green-50 border border-green-200 rounded-lg p-4 flex items-start gap-3">
          <span className="text-xl">✅</span>
          <div>
            <p className="font-medium text-green-800">Zabbix подключён</p>
            <p className="text-sm text-green-700">
              Режим: {health.mode} | Пользователь: {health.user}
            </p>
          </div>
        </div>
      )}

      {/* Статистика */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard title="Всего работ" value={works.length} icon="📋" color="blue" />
        <StatCard title="Запланировано" value={plannedWorks.length} icon="📌" color="indigo" />
        <StatCard title="В процессе" value={inProgressWorks.length} icon="🔄" color="yellow" />
        <StatCard title="Завершено" value={completedWorks.length} icon="✅" color="green" />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Ближайшие работы */}
        <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
          <h3 className="text-lg font-semibold text-gray-800 mb-4">📌 Ближайшие работы</h3>
          {upcomingWorks.length === 0 ? (
            <p className="text-gray-500 text-center py-8">Нет запланированных работ</p>
          ) : (
            <div className="space-y-3">
              {upcomingWorks.map(work => (
                <div key={work.id} className="flex items-center gap-3 p-3 bg-gray-50 rounded-lg">
                  <div className={`w-3 h-3 rounded-full ${
                    work.status === 'planned' ? 'bg-blue-500' : 'bg-yellow-500'
                  }`}></div>
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-gray-800 truncate">{work.work_title}</p>
                    <p className="text-xs text-gray-500">{work.service_name}</p>
                  </div>
                  <div className="text-right">
                    <p className="text-xs text-gray-600">
                      {new Date(work.start_time).toLocaleDateString('ru-RU', { day: '2-digit', month: '2-digit' })}
                    </p>
                    <p className="text-xs text-gray-400">
                      {new Date(work.start_time).toLocaleTimeString('ru-RU', { hour: '2-digit', minute: '2-digit' })}
                    </p>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Статус системы */}
        <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
          <h3 className="text-lg font-semibold text-gray-800 mb-4">🖥️ Статус системы</h3>
          <div className="space-y-4">
            <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
              <span className="text-sm text-gray-600">Подключение к Zabbix</span>
              <span className={`font-medium ${health?.zabbix_connected ? 'text-green-600' : 'text-red-600'}`}>
                {health?.zabbix_connected ? '✅ Подключено' : '❌ Нет'}
              </span>
            </div>
            <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
              <span className="text-sm text-gray-600">Режим работы</span>
              <span className="font-medium text-gray-800">{health?.mode || '—'}</span>
            </div>
            <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
              <span className="text-sm text-gray-600">Исключений SLA создано</span>
              <span className="font-medium text-blue-600">
                {works.filter(w => w.zabbix_exclusion_created).length}
              </span>
            </div>
            <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
              <span className="text-sm text-gray-600">Отменено работ</span>
              <span className="font-medium text-red-600">{cancelledWorks.length}</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

interface StatCardProps {
  title: string;
  value: number;
  icon: string;
  color: string;
}

const StatCard: React.FC<StatCardProps> = ({ title, value, icon, color }) => {
  const colorClasses: Record<string, string> = {
    blue: 'bg-blue-50 border-blue-100',
    indigo: 'bg-indigo-50 border-indigo-100',
    yellow: 'bg-yellow-50 border-yellow-100',
    green: 'bg-green-50 border-green-100',
  };

  return (
    <div className={`rounded-xl border p-5 ${colorClasses[color] || 'bg-gray-50 border-gray-100'}`}>
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm text-gray-600">{title}</p>
          <p className="text-3xl font-bold text-gray-800 mt-1">{value}</p>
        </div>
        <span className="text-3xl">{icon}</span>
      </div>
    </div>
  );
};

export default Dashboard;
