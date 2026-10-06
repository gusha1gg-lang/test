import React, { useState, useEffect } from 'react';
import { api, PlannedWork, ServicesTree } from '../api/client';

const SlaReport: React.FC = () => {
  const [works, setWorks] = useState<PlannedWork[]>([]);
  const [tree, setTree] = useState<ServicesTree | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    setLoading(true);
    try {
      const [worksData, treeData] = await Promise.all([
        api.getWorks(),
        api.getServicesTree(),
      ]);
      setWorks(worksData);
      setTree(treeData);
    } catch (e) {
      // ignore
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="p-6 flex items-center justify-center h-64">
        <div className="animate-spin w-8 h-8 border-4 border-blue-600 border-t-transparent rounded-full"></div>
      </div>
    );
  }

  const totalServices = tree?.nodes.length || 0;
  const okServices = tree?.nodes.filter(s => s.status === 'ok').length || 0;
  const exclusionsCount = works.filter(w => w.zabbix_exclusion_created).length;

  return (
    <div className="p-6">
      <div className="mb-6">
        <h2 className="text-xl font-bold text-gray-800">📈 SLA Отчёт</h2>
        <p className="text-sm text-gray-500 mt-1">Данные из Zabbix в реальном времени</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
        <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6 text-center">
          <p className="text-sm text-gray-500 mb-2">SLA-услуг в Zabbix</p>
          <p className="text-4xl font-bold text-blue-600">{totalServices}</p>
        </div>
        <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6 text-center">
          <p className="text-sm text-gray-500 mb-2">Исключений простоя</p>
          <p className="text-4xl font-bold text-green-600">{exclusionsCount}</p>
        </div>
        <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6 text-center">
          <p className="text-sm text-gray-500 mb-2">Услуг OK</p>
          <p className="text-4xl font-bold text-green-600">{okServices}/{totalServices}</p>
        </div>
      </div>

      {/* Услуги */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden mb-6">
        <div className="px-6 py-4 border-b border-gray-100">
          <h3 className="font-semibold text-gray-800">SLA-услуги из Zabbix</h3>
        </div>
        {tree && tree.nodes.length > 0 ? (
          <table className="w-full">
            <thead>
              <tr className="bg-gray-50 border-b border-gray-200">
                <th className="text-left px-4 py-3 text-xs font-medium text-gray-500 uppercase">Услуга</th>
                <th className="text-left px-4 py-3 text-xs font-medium text-gray-500 uppercase">Статус</th>
                <th className="text-left px-4 py-3 text-xs font-medium text-gray-500 uppercase">Алгоритм</th>
                <th className="text-left px-4 py-3 text-xs font-medium text-gray-500 uppercase">ПР</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {tree.nodes.map(node => {
                const nodeWorks = works.filter(w => w.service_id_zabbix === node.id);
                return (
                  <tr key={node.id} className="hover:bg-gray-50">
                    <td className="px-4 py-3 text-sm text-gray-800 font-medium">{node.name}</td>
                    <td className="px-4 py-3">
                      <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium ${
                        node.status === 'ok' ? 'bg-green-100 text-green-800' :
                        node.status === 'warning' ? 'bg-yellow-100 text-yellow-800' :
                        'bg-red-100 text-red-800'
                      }`}>
                        <span className={`w-2 h-2 rounded-full ${
                          node.status === 'ok' ? 'bg-green-500' :
                          node.status === 'warning' ? 'bg-yellow-500' : 'bg-red-500'
                        }`}></span>
                        {node.status.toUpperCase()}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-sm text-gray-600">{node.algorithm || '—'}</td>
                    <td className="px-4 py-3 text-sm text-gray-600">
                      {nodeWorks.length > 0
                        ? `${nodeWorks.length} ПР (${nodeWorks.filter(w => w.zabbix_exclusion_created).length} в Zabbix)`
                        : '—'}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        ) : (
          <div className="text-center py-12 text-gray-500">Нет данных. Проверьте подключение к Zabbix.</div>
        )}
      </div>

      {/* Исключения */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
        <h3 className="font-semibold text-gray-800 mb-4">📊 Исключения SLA (созданные через портал)</h3>
        {works.filter(w => w.zabbix_exclusion_created).length === 0 ? (
          <p className="text-gray-500 text-center py-4">Нет созданных исключений</p>
        ) : (
          <div className="space-y-3">
            {works.filter(w => w.zabbix_exclusion_created).map(work => (
              <div key={work.id} className="flex items-center gap-4 p-3 bg-blue-50 rounded-lg">
                <div className="w-2 h-8 bg-blue-500 rounded-full"></div>
                <div className="flex-1">
                  <p className="text-sm font-medium text-gray-800">ПР: {work.work_title} ({work.service_name})</p>
                  <p className="text-xs text-gray-500">
                    {new Date(work.start_time).toLocaleString('ru-RU')} — {new Date(work.end_time).toLocaleString('ru-RU')}
                  </p>
                </div>
                <span className="text-xs text-green-600 font-medium">✅ В Zabbix</span>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default SlaReport;
