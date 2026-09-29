import React from 'react';
import { demoWorks, demoServices } from '../data/mockData';

const Dashboard: React.FC = () => {
  const totalWorks = demoWorks.length;
  const plannedWorks = demoWorks.filter(w => w.status === 'planned').length;
  const inProgressWorks = demoWorks.filter(w => w.status === 'in_progress').length;
  const completedWorks = demoWorks.filter(w => w.status === 'completed').length;
  const cancelledWorks = demoWorks.filter(w => w.status === 'cancelled').length;
  const servicesWithProblems = demoServices.filter(s => s.status === 'problem').length;
  const servicesWithWarnings = demoServices.filter(s => s.status === 'warning').length;
  const zabbixExclusions = demoWorks.filter(w => w.zabbixExclusionCreated).length;

  const upcomingWorks = demoWorks
    .filter(w => w.status === 'planned' || w.status === 'in_progress')
    .sort((a, b) => new Date(a.startTime).getTime() - new Date(b.startTime).getTime())
    .slice(0, 5);

  return (
    <div className="p-6 space-y-6">
      {/* Демо-алерт */}
      <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4 flex items-start gap-3">
        <span className="text-xl">⚠️</span>
        <div>
          <p className="font-medium text-yellow-800">Демо-режим</p>
          <p className="text-sm text-yellow-700">
            Zabbix не настроен — показаны тестовые данные. Настройте подключение в разделе «Настройки».
          </p>
        </div>
      </div>

      {/* Статистика */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          title="Всего плановых работ"
          value={totalWorks}
          icon="📋"
          color="blue"
        />
        <StatCard
          title="Запланировано"
          value={plannedWorks}
          icon="📌"
          color="indigo"
        />
        <StatCard
          title="В процессе"
          value={inProgressWorks}
          icon="🔄"
          color="yellow"
        />
        <StatCard
          title="Завершено"
          value={completedWorks}
          icon="✅"
          color="green"
        />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Ближайшие работы */}
        <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
          <h3 className="text-lg font-semibold text-gray-800 mb-4">📌 Ближайшие работы</h3>
          <div className="space-y-3">
            {upcomingWorks.map(work => (
              <div key={work.id} className="flex items-center gap-3 p-3 bg-gray-50 rounded-lg">
                <div className={`w-3 h-3 rounded-full ${
                  work.status === 'planned' ? 'bg-blue-500' : 'bg-yellow-500'
                }`}></div>
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-gray-800 truncate">{work.workTitle}</p>
                  <p className="text-xs text-gray-500">{work.serviceName}</p>
                </div>
                <div className="text-right">
                  <p className="text-xs text-gray-600">
                    {new Date(work.startTime).toLocaleDateString('ru-RU', { day: '2-digit', month: '2-digit' })}
                  </p>
                  <p className="text-xs text-gray-400">
                    {new Date(work.startTime).toLocaleTimeString('ru-RU', { hour: '2-digit', minute: '2-digit' })}
                  </p>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Статус сервисов */}
        <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
          <h3 className="text-lg font-semibold text-gray-800 mb-4">🖥️ Статус сервисов Zabbix</h3>
          <div className="space-y-4">
            <div className="flex items-center justify-between p-3 bg-green-50 rounded-lg">
              <div className="flex items-center gap-3">
                <span className="w-4 h-4 bg-green-500 rounded-full"></span>
                <span className="text-sm font-medium text-gray-700">OK</span>
              </div>
              <span className="text-lg font-bold text-green-700">
                {demoServices.filter(s => s.status === 'ok').length}
              </span>
            </div>
            <div className="flex items-center justify-between p-3 bg-yellow-50 rounded-lg">
              <div className="flex items-center gap-3">
                <span className="w-4 h-4 bg-yellow-500 rounded-full"></span>
                <span className="text-sm font-medium text-gray-700">Warning</span>
              </div>
              <span className="text-lg font-bold text-yellow-700">{servicesWithWarnings}</span>
            </div>
            <div className="flex items-center justify-between p-3 bg-red-50 rounded-lg">
              <div className="flex items-center gap-3">
                <span className="w-4 h-4 bg-red-500 rounded-full"></span>
                <span className="text-sm font-medium text-gray-700">Problem</span>
              </div>
              <span className="text-lg font-bold text-red-700">{servicesWithProblems}</span>
            </div>
          </div>

          <div className="mt-6 pt-4 border-t border-gray-100">
            <div className="flex items-center justify-between">
              <span className="text-sm text-gray-600">Исключений SLA создано</span>
              <span className="text-lg font-bold text-blue-700">{zabbixExclusions}</span>
            </div>
            <div className="flex items-center justify-between mt-2">
              <span className="text-sm text-gray-600">Отменено работ</span>
              <span className="text-lg font-bold text-red-600">{cancelledWorks}</span>
            </div>
          </div>
        </div>
      </div>

      {/* Информация о системе */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
        <h3 className="text-lg font-semibold text-gray-800 mb-3">ℹ️ О системе</h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
          <div>
            <p className="text-gray-500">Версия портала</p>
            <p className="font-medium text-gray-800">1.0.0 (PoC)</p>
          </div>
          <div>
            <p className="text-gray-500">Режим работы</p>
            <p className="font-medium text-yellow-600">Демо (без Zabbix)</p>
          </div>
          <div>
            <p className="text-gray-500">База данных</p>
            <p className="font-medium text-gray-800">LocalStorage (демо)</p>
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
