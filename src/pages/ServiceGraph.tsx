import React, { useEffect, useRef, useState } from 'react';
import { Network, Options } from 'vis-network';
import { DataSet } from 'vis-data';
import { api, ServiceNode, ServicesTree } from '../api/client';

interface ServiceGraphProps {
  onServiceSelect: (serviceName: string, serviceId?: string) => void;
  onNavigateToNewWork: () => void;
}

const ServiceGraph: React.FC<ServiceGraphProps> = ({ onServiceSelect, onNavigateToNewWork }) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const networkRef = useRef<Network | null>(null);
  const [selectedService, setSelectedService] = useState<ServiceNode | null>(null);
  const [tree, setTree] = useState<ServicesTree | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    loadTree();
    return () => {
      if (networkRef.current) networkRef.current.destroy();
    };
  }, []);

  const loadTree = async () => {
    setLoading(true);
    setError('');
    try {
      const data = await api.getServicesTree();
      setTree(data);
    } catch (e: any) {
      setError(e.message || 'Не удалось загрузить дерево сервисов');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (!tree || !containerRef.current) return;

    const statusColors: Record<string, string> = {
      ok: '#28a745',
      warning: '#ffc107',
      problem: '#dc3545',
    };

    const getLevel = (nodeId: string): number => {
      let level = 0;
      let current = tree.nodes.find(n => n.id === nodeId);
      while (current?.parent_id) {
        level++;
        current = tree.nodes.find(n => n.id === current!.parent_id);
      }
      return level;
    };

    const visNodes = new DataSet(
      tree.nodes.map(node => ({
        id: node.id,
        label: node.name,
        color: {
          background: statusColors[node.status] || '#6c757d',
          border: statusColors[node.status] || '#6c757d',
          highlight: {
            background: statusColors[node.status] || '#6c757d',
            border: '#0d6efd',
          },
        },
        font: { color: '#ffffff', size: 13, face: 'system-ui' },
        shape: 'box' as const,
        shapeProperties: { borderRadius: 8 },
        borderWidth: 2,
        borderWidthSelected: 4,
        margin: 12,
        level: getLevel(node.id),
      }))
    );

    const visEdges = new DataSet(
      tree.edges.map((edge, i) => ({
        id: `e${i}`,
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
        },
      },
      physics: { enabled: false },
      interaction: { hover: true, zoomView: true, dragView: true },
    };

    if (networkRef.current) networkRef.current.destroy();

    const network = new Network(containerRef.current, { nodes: visNodes as any, edges: visEdges as any }, options);
    networkRef.current = network;

    network.on('click', (params: any) => {
      if (params.nodes.length > 0) {
        const nodeId = params.nodes[0];
        const node = tree.nodes.find(n => n.id === nodeId);
        if (node) {
          setSelectedService(node);
          onServiceSelect(node.name, node.id);
          network.selectNodes([nodeId]);
        }
      }
    });
  }, [tree]);

  if (loading) {
    return (
      <div className="p-6 flex items-center justify-center h-64">
        <div className="text-center">
          <div className="animate-spin w-8 h-8 border-4 border-blue-600 border-t-transparent rounded-full mx-auto mb-4"></div>
          <p className="text-gray-500">Загрузка дерева сервисов из Zabbix...</p>
        </div>
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
          <button onClick={loadTree} className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700">
            🔄 Повторить
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="p-6">
      <div className="grid grid-cols-1 lg:grid-cols-5 gap-6">
        {/* Граф */}
        <div className="lg:col-span-3 bg-white rounded-xl shadow-sm border border-gray-100 p-6">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-3">
              <h3 className="text-lg font-semibold text-gray-800">Дерево SLA-услуг Zabbix</h3>
              <span className="text-xs text-gray-500">({tree?.nodes.length || 0} услуг)</span>
            </div>
            <div className="flex items-center gap-3 text-xs">
              <span className="flex items-center gap-1"><span className="w-3 h-3 bg-green-500 rounded-full"></span> OK</span>
              <span className="flex items-center gap-1"><span className="w-3 h-3 bg-yellow-500 rounded-full"></span> Warning</span>
              <span className="flex items-center gap-1"><span className="w-3 h-3 bg-red-500 rounded-full"></span> Problem</span>
            </div>
          </div>

          <div ref={containerRef} className="w-full h-[450px] border border-gray-200 rounded-lg bg-gray-50" />
          <p className="text-xs text-gray-500 mt-3">⚙️ Кликните по услуге для выбора</p>
        </div>

        {/* Параметры */}
        <div className="lg:col-span-2 bg-white rounded-xl shadow-sm border border-gray-100 p-6">
          <h3 className="text-lg font-semibold text-gray-800 mb-4">Параметры работы</h3>

          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Имя сервиса / ИС <span className="text-red-500">*</span>
              </label>
              <input
                type="text"
                value={selectedService?.name || ''}
                readOnly
                className="w-full px-3 py-2 border border-gray-300 rounded-lg bg-gray-50 text-gray-700 text-sm"
                placeholder="Кликните по узлу графа..."
              />
              <p className="text-xs text-gray-400 mt-1">Заполняется автоматически при клике по узлу</p>
            </div>

            {selectedService && (
              <div className="flex items-center gap-2 p-2 bg-gray-50 rounded-lg">
                <span className={`w-3 h-3 rounded-full ${
                  selectedService.status === 'ok' ? 'bg-green-500' :
                  selectedService.status === 'warning' ? 'bg-yellow-500' : 'bg-red-500'
                }`}></span>
                <span className="text-sm text-gray-600">
                  Статус: <strong>{selectedService.status.toUpperCase()}</strong>
                </span>
              </div>
            )}

            <button
              onClick={() => {
                if (selectedService) onNavigateToNewWork();
              }}
              disabled={!selectedService}
              className="w-full py-3 bg-blue-600 text-white font-medium rounded-lg hover:bg-blue-700 transition-colors disabled:bg-gray-300 disabled:cursor-not-allowed"
            >
              💾 Перейти к регистрации ПР
            </button>

            <div className="bg-blue-50 border border-blue-100 rounded-lg p-4">
              <h4 className="text-sm font-medium text-blue-800 flex items-center gap-2">
                <span>ℹ️</span> Что произойдёт при отправке:
              </h4>
              <ul className="mt-2 space-y-1 text-xs text-blue-700">
                <li>• Запись о ПР сохранится в БД</li>
                <li>• В Zabbix SLA будет добавлено исключение простоя</li>
                <li>• В период ПР недоступность не учитывается в SLA</li>
              </ul>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ServiceGraph;
