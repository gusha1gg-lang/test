import React, { useState, useEffect } from 'react';
import { api } from '../api/client';

const Groups: React.FC = () => {
  const [groups, setGroups] = useState<any[]>([]);
  const [allServices, setAllServices] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [editingGroup, setEditingGroup] = useState<any>(null);
  const [error, setError] = useState('');
  const [syncing, setSyncing] = useState(false);

  // Форма
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [selectedServices, setSelectedServices] = useState<string[]>([]);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    setLoading(true);
    try {
      const [groupsData, servicesData] = await Promise.all([
        api.getGroups(),
        api.getAllServices(),
      ]);
      setGroups(groupsData);
      setAllServices(servicesData);
    } catch (e: any) {
      setError(e.message || 'Ошибка загрузки');
    } finally {
      setLoading(false);
    }
  };

  const handleSync = async () => {
    setSyncing(true);
    try {
      const result = await api.syncServices();
      alert(result.message);
      await loadData();
    } catch (e: any) {
      alert(`Ошибка синхронизации: ${e.message}`);
    } finally {
      setSyncing(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');

    try {
      if (editingGroup) {
        await api.updateGroup(editingGroup.id, {
          name,
          description,
          service_ids: selectedServices,
        });
      } else {
        await api.createGroup({
          name,
          description,
          service_ids: selectedServices,
        });
      }
      resetForm();
      await loadData();
    } catch (e: any) {
      setError(e.message || 'Ошибка сохранения');
    }
  };

  const handleEdit = (group: any) => {
    setEditingGroup(group);
    setName(group.name);
    setDescription(group.description || '');
    setSelectedServices(group.services?.map((s: any) => s.id) || []);
    setShowForm(true);
  };

  const handleDelete = async (id: number, name: string) => {
    if (!confirm(`Удалить группу "${name}"?`)) return;
    try {
      await api.deleteGroup(id);
      await loadData();
    } catch (e: any) {
      alert(`Ошибка: ${e.message}`);
    }
  };

  const resetForm = () => {
    setShowForm(false);
    setEditingGroup(null);
    setName('');
    setDescription('');
    setSelectedServices([]);
    setError('');
  };

  const toggleService = (serviceId: string) => {
    setSelectedServices(prev =>
      prev.includes(serviceId)
        ? prev.filter(id => id !== serviceId)
        : [...prev, serviceId]
    );
  };

  const selectAllServices = () => {
    setSelectedServices(allServices.map(s => s.id));
  };

  const deselectAllServices = () => {
    setSelectedServices([]);
  };

  if (loading) {
    return (
      <div className="p-6 flex items-center justify-center h-64">
        <div className="animate-spin w-8 h-8 border-4 border-blue-600 border-t-transparent rounded-full"></div>
      </div>
    );
  }

  return (
    <div className="p-6">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h2 className="text-xl font-bold text-gray-800">👥 Группы и права доступа</h2>
          <p className="text-sm text-gray-500 mt-1">Управление группами пользователей и их доступом к ИС</p>
        </div>
        <div className="flex gap-2">
          <button
            onClick={handleSync}
            disabled={syncing}
            className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 text-sm font-medium disabled:opacity-50"
          >
            {syncing ? '⏳ Синхронизация...' : '🔄 Синхронизировать из Zabbix'}
          </button>
          <button
            onClick={() => setShowForm(true)}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 text-sm font-medium"
          >
            + Новая группа
          </button>
        </div>
      </div>

      {error && (
        <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg text-sm text-red-700">
          ❌ {error}
        </div>
      )}

      {allServices.length === 0 && (
        <div className="mb-4 p-3 bg-yellow-50 border border-yellow-200 rounded-lg text-sm text-yellow-700">
          ⚠️ Нет сервисов в базе данных. Нажмите "Синхронизировать из Zabbix" для загрузки SLA-услуг.
        </div>
      )}

      {/* Форма создания/редактирования */}
      {showForm && (
        <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6 mb-6">
          <h3 className="text-lg font-semibold text-gray-800 mb-4">
            {editingGroup ? '✏️ Редактирование группы' : '➕ Новая группа'}
          </h3>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Название группы <span className="text-red-500">*</span>
              </label>
              <input
                type="text"
                value={name}
                onChange={e => setName(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm"
                placeholder="Например: Команда разработки"
                required
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Описание</label>
              <textarea
                value={description}
                onChange={e => setDescription(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm resize-none"
                rows={2}
                placeholder="Описание группы и её назначение..."
              />
            </div>
            <div>
              <div className="flex items-center justify-between mb-2">
                <label className="block text-sm font-medium text-gray-700">
                  Доступ к ИС (SLA-услугам)
                </label>
                <div className="flex gap-2">
                  <button
                    type="button"
                    onClick={selectAllServices}
                    className="text-xs text-blue-600 hover:underline"
                  >
                    Выбрать все
                  </button>
                  <button
                    type="button"
                    onClick={deselectAllServices}
                    className="text-xs text-gray-600 hover:underline"
                  >
                    Снять все
                  </button>
                </div>
              </div>
              {allServices.length === 0 ? (
                <p className="text-sm text-gray-500">Нет доступных сервисов. Сначала синхронизируйте с Zabbix.</p>
              ) : (
                <div className="max-h-64 overflow-y-auto border border-gray-200 rounded-lg p-3">
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
                    {allServices.map(service => (
                      <label
                        key={service.id}
                        className={`flex items-center gap-2 p-2 rounded cursor-pointer transition-colors ${
                          selectedServices.includes(service.id)
                            ? 'bg-blue-50 border border-blue-200'
                            : 'hover:bg-gray-50 border border-transparent'
                        }`}
                      >
                        <input
                          type="checkbox"
                          checked={selectedServices.includes(service.id)}
                          onChange={() => toggleService(service.id)}
                          className="w-4 h-4"
                        />
                        <span className="text-sm text-gray-700">{service.name}</span>
                        <span className={`w-2 h-2 rounded-full ml-auto ${
                          service.status === 'ok' ? 'bg-green-500' :
                          service.status === 'warning' ? 'bg-yellow-500' : 'bg-red-500'
                        }`}></span>
                      </label>
                    ))}
                  </div>
                </div>
              )}
              <p className="text-xs text-gray-500 mt-1">
                Выбрано: {selectedServices.length} из {allServices.length}
              </p>
            </div>
            <div className="flex gap-3">
              <button
                type="submit"
                className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 text-sm"
              >
                💾 Сохранить
              </button>
              <button
                type="button"
                onClick={resetForm}
                className="px-4 py-2 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300 text-sm"
              >
                Отмена
              </button>
            </div>
          </form>
        </div>
      )}

      {/* Список групп */}
      <div className="space-y-4">
        {groups.length === 0 ? (
          <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-12 text-center text-gray-500">
            <p className="text-3xl mb-2">👥</p>
            <p>Нет групп. Создайте первую группу для назначения прав доступа.</p>
          </div>
        ) : (
          groups.map(group => (
            <div key={group.id} className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <div className="flex items-center gap-3 mb-2">
                    <h3 className="text-lg font-semibold text-gray-800">{group.name}</h3>
                    <span className="px-2 py-0.5 bg-blue-50 text-blue-700 text-xs rounded-full">
                      {group.users_count} польз.
                    </span>
                    <span className="px-2 py-0.5 bg-green-50 text-green-700 text-xs rounded-full">
                      {group.services_count} ИС
                    </span>
                  </div>
                  {group.description && (
                    <p className="text-sm text-gray-600 mb-3">{group.description}</p>
                  )}
                  <div className="flex flex-wrap gap-1">
                    {group.services?.length > 0 ? (
                      group.services.map((s: any) => (
                        <span
                          key={s.id}
                          className="px-2 py-0.5 bg-gray-100 text-gray-700 text-xs rounded-full flex items-center gap-1"
                        >
                          <span className={`w-2 h-2 rounded-full ${
                            s.status === 'ok' ? 'bg-green-500' :
                            s.status === 'warning' ? 'bg-yellow-500' : 'bg-red-500'
                          }`}></span>
                          {s.name}
                        </span>
                      ))
                    ) : (
                      <span className="text-xs text-gray-400">Нет доступа к ИС</span>
                    )}
                  </div>
                </div>
                <div className="flex items-center gap-2 ml-4">
                  <button
                    onClick={() => handleEdit(group)}
                    className="px-3 py-1 text-xs bg-blue-100 text-blue-800 rounded hover:bg-blue-200"
                  >
                    ✏️ Редактировать
                  </button>
                  <button
                    onClick={() => handleDelete(group.id, group.name)}
                    className="px-3 py-1 text-xs bg-red-100 text-red-800 rounded hover:bg-red-200"
                  >
                    🗑️ Удалить
                  </button>
                </div>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
};

export default Groups;
