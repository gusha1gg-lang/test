import React from 'react';
import { demoServices, demoWorks } from '../data/mockData';

const SlaReport: React.FC = () => {
  // Расчёт демо SLA
  const totalServices = demoServices.length;
  const okServices = demoServices.filter(s => s.status === 'ok').length;
  const slaPercentage = ((okServices / totalServices) * 100).toFixed(1);
  const targetSla = 99.9;
  const exclusionsCount = demoWorks.filter(w => w.zabbixExclusionCreated).length;

  return (
    <div className="p-6">
      <div className="mb-6">
        <h2 className="text-xl font-bold text-gray-800">📈 SLA Отчёт</h2>
        <p className="text-sm text-gray-500 mt-1">Отчёт по доступности сервисов и плановым работам</p>
      </div>

      {/* Демо-алерт */}
      <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4 flex items-start gap-3 mb-6">
        <span className="text-xl">⚠️</span>
        <div>
          <p className="font-medium text-yellow-800">Демо-режим</p>
          <p className="text-sm text-yellow-700">
            Данные рассчитаны на основе тестовых значений. При подключении к Zabbix будут отображены реальные метрики SLA.
          </p>
        </div>
      </div>

      {/* Основные метрики */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
        <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6 text-center">
          <p className="text-sm text-gray-500 mb-2">Текущий SLA</p>
          <p className={`text-4xl font-bold ${parseFloat(slaPercentage) >= targetSla ? 'text-green-600' : 'text-red-600'}`}>
            {slaPercentage}%
          </p>
          <p className="text-xs text-gray-400 mt-2">Цель: {targetSla}%</p>
        </div>
        <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6 text-center">
          <p className="text-sm text-gray-500 mb-2">Исключений простоя</p>
          <p className="text-4xl font-bold text-blue-600">{exclusionsCount}</p>
          <p className="text-xs text-gray-400 mt-2">Создано через портал</p>
        </div>
        <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6 text-center">
          <p className="text-sm text-gray-500 mb-2">Сервисов OK</p>
          <p className="text-4xl font-bold text-green-600">{okServices}/{totalServices}</p>
          <p className="text-xs text-gray-400 mt-2">Доступно в данный момент</p>
        </div>
      </div>

      {/* Таблица сервисов */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden mb-6">
        <div className="px-6 py-4 border-b border-gray-100">
          <h3 className="font-semibold text-gray-800">Доступность по сервисам</h3>
        </div>
        <table className="w-full">
          <thead>
            <tr className="bg-gray-50 border-b border-gray-200">
              <th className="text-left px-4 py-3 text-xs font-medium text-gray-500 uppercase">Сервис</th>
              <th className="text-left px-4 py-3 text-xs font-medium text-gray-500 uppercase">Статус</th>
              <th className="text-left px-4 py-3 text-xs font-medium text-gray-500 uppercase">SLA</th>
              <th className="text-left px-4 py-3 text-xs font-medium text-gray-500 uppercase">ПР в этом месяце</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            {demoServices.map(service => {
              const serviceWorks = demoWorks.filter(w => w.serviceName === service.name);
              const demoSla = service.status === 'ok' ? 99.95 + Math.random() * 0.04 :
                             service.status === 'warning' ? 98.5 + Math.random() * 1 :
                             95 + Math.random() * 3;
              return (
                <tr key={service.id} className="hover:bg-gray-50">
                  <td className="px-4 py-3 text-sm text-gray-800 font-medium">{service.name}</td>
                  <td className="px-4 py-3">
                    <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium ${
                      service.status === 'ok' ? 'bg-green-100 text-green-800' :
                      service.status === 'warning' ? 'bg-yellow-100 text-yellow-800' :
                      'bg-red-100 text-red-800'
                    }`}>
                      <span className={`w-2 h-2 rounded-full ${
                        service.status === 'ok' ? 'bg-green-500' :
                        service.status === 'warning' ? 'bg-yellow-500' : 'bg-red-500'
                      }`}></span>
                      {service.status === 'ok' ? 'OK' : service.status === 'warning' ? 'Warning' : 'Problem'}
                    </span>
                  </td>
                  <td className="px-4 py-3">
                    <span className={`text-sm font-medium ${demoSla >= targetSla ? 'text-green-600' : 'text-red-600'}`}>
                      {demoSla.toFixed(2)}%
                    </span>
                  </td>
                  <td className="px-4 py-3 text-sm text-gray-600">
                    {serviceWorks.length > 0 ? (
                      <span>{serviceWorks.length} ПР ({serviceWorks.filter(w => w.zabbixExclusionCreated).length} в Zabbix)</span>
                    ) : (
                      <span className="text-gray-400">—</span>
                    )}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      {/* Временная шкала исключений */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
        <h3 className="font-semibold text-gray-800 mb-4">📊 Исключения SLA (плановые работы)</h3>
        <div className="space-y-3">
          {demoWorks.filter(w => w.zabbixExclusionCreated).map(work => (
            <div key={work.id} className="flex items-center gap-4 p-3 bg-blue-50 rounded-lg">
              <div className="w-2 h-8 bg-blue-500 rounded-full"></div>
              <div className="flex-1">
                <p className="text-sm font-medium text-gray-800">
                  ПР: {work.workTitle} ({work.serviceName})
                </p>
                <p className="text-xs text-gray-500">
                  {new Date(work.startTime).toLocaleDateString('ru-RU')} {new Date(work.startTime).toLocaleTimeString('ru-RU', { hour: '2-digit', minute: '2-digit' })}
                  {' — '}
                  {new Date(work.endTime).toLocaleDateString('ru-RU')} {new Date(work.endTime).toLocaleTimeString('ru-RU', { hour: '2-digit', minute: '2-digit' })}
                </p>
              </div>
              <span className="text-xs text-green-600 font-medium">✅ В Zabbix</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default SlaReport;
