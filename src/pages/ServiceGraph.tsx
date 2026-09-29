import React, { useEffect, useRef, useState } from 'react';
import { Network, Options } from 'vis-network';
import { DataSet } from 'vis-data';
import { getServicesTree } from '../data/mockData';
import { ServiceNode } from '../types';

interface ServiceGraphProps {
  onServiceSelect: (serviceName: string) => void;
  onNavigateToNewWork: () => void;
}

const ServiceGraph: React.FC<ServiceGraphProps> = ({ onServiceSelect, onNavigateToNewWork }) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const networkRef = useRef<Network | null>(null);
  const [selectedService, setSelectedService] = useState<ServiceNode | null>(null);

  useEffect(() => {
    if (!containerRef.current) return;

    const { nodes: services, edges: serviceEdges } = getServicesTree();

    // Подготовка данных для vis-network
    const statusColors: Record<string, string> = {
      ok: '#28a745',
      warning: '#ffc107',
      problem: '#dc3545',
    };

    const visNodes = new DataSet(
      services.map(service => ({
        id: service.id,
        label: service.name,
        color: {
          background: statusColors[service.status] || '#6c757d',
          border: statusColors[service.status] || '#6c757d',
          highlight: {
            background: statusColors[service.status] || '#6c757d',
            border: '#0d6efd',
          },
        },
        font: {
          color: '#ffffff',
          size: 13,
          face: 'system-ui',
        },
        shape: 'box' as const,
        shapeProperties: {
          borderRadius: 8,
        },
        borderWidth: 2,
        borderWidthSelected: 4,
        margin: 12,
        level: getLevel(service.id, services),
      }))
    );

    const visEdges = new DataSet(
      serviceEdges.map(edge => ({
        id: `${edge.from}-${edge.to}`,
        from: edge.from,
        to: edge.to,
        arrows: { to: { enabled: true, scaleFactor: 0.8 } },
        color: { color: '#adb5bd', highlight: '#0d6efd' },
        width: 2,
        smooth: { type: 'cubicBezier' as const, forceDirection: 'vertical' as const, roundness: 0.4 },
      }))
    );

    const options: Options = {
      layout: {
        hierarchical: {
          enabled: true,
          direction: 'UD',
          sortMethod: 'directed',
          levelSeparation: 100,
          nodeSpacing: 160,
          treeSpacing: 200,
          blockShifting: true,
          edgeMinimization: true,
          parentCentralization: true,
        },
      },
      physics: {
        enabled: false,
      },
      interaction: {
        hover: true,
        zoomView: true,
        dragView: true,
      },
      nodes: {
        chosen: true,
      },
      edges: {
        chosen: true,
      },
    };

    const network = new Network(containerRef.current, { nodes: visNodes as any, edges: visEdges as any }, options);
    networkRef.current = network;

    // Обработка клика по узлу
    network.on('click', (params: any) => {
      if (params.nodes.length > 0) {
        const nodeId = params.nodes[0];
        const service = services.find(s => s.id === nodeId);
        if (service) {
          setSelectedService(service);
          onServiceSelect(service.name);
          // Подсветка выбранного узла
          network.selectNodes([nodeId]);
        }
      }
    });

    return () => {
      network.destroy();
    };
  }, []);

  return (
    <div className="p-6">
      {/* Демо-алерт */}
      <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4 flex items-start gap-3 mb-6">
        <span className="text-xl">⚠️</span>
        <div>
          <p className="font-medium text-yellow-800">Демо-режим: Zabbix не настроен — показаны тестовые данные.</p>
          <p className="text-sm text-yellow-700">
            Настройте подключение в разделе «Настройки».
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-5 gap-6">
        {/* Левая колонка — Граф (60%) */}
        <div className="lg:col-span-3 bg-white rounded-xl shadow-sm border border-gray-100 p-6">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-3">
              <h3 className="text-lg font-semibold text-gray-800">Дерево сервисов Zabbix</h3>
              <span className="px-2 py-0.5 bg-yellow-100 text-yellow-800 text-xs font-medium rounded-full">DEMO</span>
            </div>
            <div className="flex items-center gap-3 text-xs">
              <span className="flex items-center gap-1"><span className="w-3 h-3 bg-green-500 rounded-full"></span> OK</span>
              <span className="flex items-center gap-1"><span className="w-3 h-3 bg-yellow-500 rounded-full"></span> Warning</span>
              <span className="flex items-center gap-1"><span className="w-3 h-3 bg-red-500 rounded-full"></span> Problem</span>
            </div>
          </div>

          {/* Контейнер для графа */}
          <div
            ref={containerRef}
            className="w-full h-[450px] border border-gray-200 rounded-lg bg-gray-50"
          />

          <p className="text-xs text-gray-500 mt-3 flex items-center gap-1">
            ⚙️ Кликните по сервису для выбора
          </p>
        </div>

        {/* Правая колонка — Параметры работы (40%) */}
        <div className="lg:col-span-2 bg-white rounded-xl shadow-sm border border-gray-100 p-6">
          <h3 className="text-lg font-semibold text-gray-800 mb-4">Параметры работы</h3>

          <div className="space-y-4">
            {/* Имя сервиса */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Имя сервиса / ИС <span className="text-red-500">*</span>
              </label>
              <input
                type="text"
                value={selectedService?.name || ''}
                readOnly
                className="w-full px-3 py-2 border border-gray-300 rounded-lg bg-gray-50 text-gray-700 text-sm"
                placeholder="Выберите сервис из графа..."
              />
              <p className="text-xs text-gray-400 mt-1">
                Заполняется автоматически при клике по узлу дерева Zabbix
              </p>
            </div>

            {/* Статус выбранного сервиса */}
            {selectedService && (
              <div className="flex items-center gap-2 p-2 bg-gray-50 rounded-lg">
                <span className={`w-3 h-3 rounded-full ${
                  selectedService.status === 'ok' ? 'bg-green-500' :
                  selectedService.status === 'warning' ? 'bg-yellow-500' : 'bg-red-500'
                }`}></span>
                <span className="text-sm text-gray-600">
                  Статус: <strong>{
                    selectedService.status === 'ok' ? 'OK' :
                    selectedService.status === 'warning' ? 'Warning' : 'Problem'
                  }</strong>
                </span>
              </div>
            )}

            {/* Название работы */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Название работы <span className="text-red-500">*</span>
              </label>
              <input
                type="text"
                className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none"
                placeholder="Например: Обновление PostgreSQL"
              />
            </div>

            {/* Описание */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Описание</label>
              <textarea
                className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none resize-none"
                rows={3}
                placeholder="Описание плановых работ..."
              />
            </div>

            {/* Даты */}
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Дата начала</label>
                <input
                  type="date"
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Время начала</label>
                <input
                  type="time"
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none"
                />
              </div>
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Дата окончания</label>
                <input
                  type="date"
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Время окончания</label>
                <input
                  type="time"
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none"
                />
              </div>
            </div>

            {/* Кнопка сохранения */}
            <button
              onClick={onNavigateToNewWork}
              disabled={!selectedService}
              className="w-full py-3 bg-blue-600 text-white font-medium rounded-lg hover:bg-blue-700 transition-colors disabled:bg-gray-300 disabled:cursor-not-allowed"
            >
              💾 Сохранить локально
            </button>

            {/* Информационный блок */}
            <div className="bg-blue-50 border border-blue-100 rounded-lg p-4">
              <h4 className="text-sm font-medium text-blue-800 flex items-center gap-2">
                <span>ℹ️</span> Что произойдёт при отправке в Zabbix:
              </h4>
              <ul className="mt-2 space-y-1 text-xs text-blue-700">
                <li>• Будет создан запис о плановой работе в БД</li>
                <li>• В SLA Zabbix будет добавлено исключение простоя</li>
                <li>• В период ПР недоступность ИС не будет учитываться</li>
                <li>• Отчёт SLA не будет испорчен</li>
              </ul>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

// Вспомогательная функция для определения уровня узла в иерархии
function getLevel(nodeId: string, services: ServiceNode[]): number {
  let level = 0;
  let current = services.find(s => s.id === nodeId);
  while (current?.parentId) {
    level++;
    current = services.find(s => s.id === current!.parentId);
  }
  return level;
}

export default ServiceGraph;
