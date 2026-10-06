// --- ФАЙЛ: src/pages/NewWork.tsx ---
import React, { useState, useEffect } from 'react';
import { api, ServiceNode } from '../api/client';

interface NewWorkProps {
  preselectedService?: string;
  preselectedServiceId?: string;
}

const NewWork: React.FC<NewWorkProps> = ({ preselectedService, preselectedServiceId }) => {
  const [services, setServices] = useState<ServiceNode[]>([]);
  const [loadingServices, setLoadingServices] = useState(true);
  const [serviceName, setServiceName] = useState(preselectedService || '');
  const [serviceId, setServiceId] = useState(preselectedServiceId || '');
  const [workTitle, setWorkTitle] = useState('');
  const [description, setDescription] = useState('');
  const [startDate, setStartDate] = useState('');
  const [startTime, setStartTime] = useState('22:00');
  const [endDate, setEndDate] = useState('');
  const [endTime, setEndTime] = useState('06:00');
  const [submitted, setSubmitted] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState('');
  const [lastResult, setLastResult] = useState<any>(null);

  useEffect(() => {
    loadServices();
  }, []);

  useEffect(() => {
    if (preselectedService) setServiceName(preselectedService);
    if (preselectedServiceId) setServiceId(preselectedServiceId);
  }, [preselectedService, preselectedServiceId]);

  const loadServices = async () => {
    setLoadingServices(true);
    try {
      const data = await api.getServicesTree();
      setServices(data.nodes || []);
    } catch (e) {
      console.error('Ошибка загрузки сервисов:', e);
      setServices([]);
    } finally {
      setLoadingServices(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');

    if (!serviceName) { setError('Выберите SLA-услугу'); return; }
    if (!workTitle) { setError('Укажите название работы'); return; }
    if (!startDate || !startTime || !endDate || !endTime) { setError('Укажите дату и время'); return; }

    const start = new Date(`${startDate}T${startTime}`);
    const end = new Date(`${endDate}T${endTime}`);
    if (end <= start) { setError('Время окончания должно быть позже начала'); return; }

    setSubmitting(true);
    try {
      const result = await api.createWork({
        service_name: serviceName,
        service_id_zabbix: serviceId || undefined,
        work_title: workTitle,
        description: description || undefined,
        start_time: start.toISOString(),
        end_time: end.toISOString(),
      });
      setLastResult(result);
      setSubmitted(true);
    } catch (e: any) {
      setError(e.message || 'Ошибка сохранения');
    } finally {
      setSubmitting(false);
    }
  };

  const handleReset = () => {
    setServiceName('');
    setServiceId('');
    setWorkTitle('');
    setDescription('');
    setStartDate('');
    setStartTime('22:00');
    setEndDate('');
    setEndTime('06:00');
    setSubmitted(false);
    setError('');
    setLastResult(null);
  };

  if (submitted) {
    return (
      <div className="p-6">
        <div className="max-w-2xl mx-auto">
          <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-8 text-center">
            <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4">
              <span className="text-3xl">✅</span>
            </div>
            <h3 className="text-xl font-bold text-gray-800 mb-2">Работа зарегистрирована!</h3>
            <p className="text-gray-600 mb-4">
              «{lastResult?.work_title}» для услуги «{lastResult?.service_name}»
            </p>
            <div className={`border rounded-lg p-4 mb-6 text-left ${
              lastResult?.zabbix_exclusion_created
                ? 'bg-green-50 border-green-200'
                : 'bg-yellow-50 border-yellow-200'
            }`}>
              <h4 className="text-sm font-medium mb-2">
                {lastResult?.zabbix_exclusion_created ? '✅ Исключение SLA создано в Zabbix' : '⚠️ Исключение не создано'}
              </h4>
              <p className="text-sm">
                {lastResult?.zabbix_exclusion_created
                  ? 'Период простоя будет исключён из SLA-отчёта.'
                  : 'Проверьте подключение к Zabbix в настройках.'}
              </p>
            </div>
            <div className="flex gap-3 justify-center">
              <button onClick={handleReset} className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700">
                + Ещё одна работа
              </button>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="p-6">
      <div className="max-w-3xl mx-auto">
        <div className="mb-6">
          <h2 className="text-xl font-bold text-gray-800">➕ Регистрация плановой работы</h2>
          <p className="text-sm text-gray-500 mt-1">После сохранения работа будет отправлена в Zabbix как исключение SLA</p>
        </div>

        <form onSubmit={handleSubmit} className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
          {error && (
            <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg text-sm text-red-700">❌ {error}</div>
          )}

          <div className="space-y-5">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                SLA-услуга / ИС <span className="text-red-500">*</span>
              </label>
              
              {loadingServices ? (
                <div className="flex items-center gap-2 p-3 bg-gray-50 rounded-lg">
                  <div className="animate-spin w-4 h-4 border-2 border-blue-600 border-t-transparent rounded-full"></div>
                  <span className="text-sm text-gray-600">Загрузка услуг из Zabbix...</span>
                </div>
              ) : services.length === 0 ? (
                <div className="p-4 bg-yellow-50 border border-yellow-200 rounded-lg">
                  <p className="text-sm text-yellow-800 font-medium mb-2">⚠️ Нет доступных SLA-услуг</p>
                  <p className="text-xs text-yellow-700">
                    Создайте услуги в Zabbix: <strong>Сервисы → Дерево сервисов → Создать сервис</strong>
                  </p>
                </div>
              ) : (
                <>
                  <select
                    value={serviceName}
                    onChange={e => {
                      setServiceName(e.target.value);
                      const svc = services.find(s => s.name === e.target.value);
                      if (svc) setServiceId(svc.id);
                    }}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 outline-none"
                  >
                    <option value="">— Выберите услугу из Zabbix —</option>
                    {services.map(s => (
                      <option key={s.id} value={s.name}>
                        {s.name} {s.status === 'problem' ? '🔴' : s.status === 'warning' ? '🟡' : '🟢'}
                      </option>
                    ))}
                  </select>
                  <p className="text-xs text-gray-400 mt-1">
                    Загружено из Zabbix: {services.length} услуг
                  </p>
                </>
              )}
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Название работы <span className="text-red-500">*</span>
              </label>
              <input
                type="text"
                value={workTitle}
                onChange={e => setWorkTitle(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 outline-none"
                placeholder="Например: Обновление PostgreSQL"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Описание</label>
              <textarea
                value={description}
                onChange={e => setDescription(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 outline-none resize-none"
                rows={4}
                placeholder="Описание плановых работ..."
              />
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Начало <span className="text-red-500">*</span></label>
                <div className="flex gap-2">
                  <input type="date" value={startDate} onChange={e => setStartDate(e.target.value)} className="flex-1 px-3 py-2 border border-gray-300 rounded-lg text-sm outline-none" />
                  <input type="time" value={startTime} onChange={e => setStartTime(e.target.value)} className="w-28 px-3 py-2 border border-gray-300 rounded-lg text-sm outline-none" />
                </div>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Окончание <span className="text-red-500">*</span></label>
                <div className="flex gap-2">
                  <input type="date" value={endDate} onChange={e => setEndDate(e.target.value)} className="flex-1 px-3 py-2 border border-gray-300 rounded-lg text-sm outline-none" />
                  <input type="time" value={endTime} onChange={e => setEndTime(e.target.value)} className="w-28 px-3 py-2 border border-gray-300 rounded-lg text-sm outline-none" />
                </div>
              </div>
            </div>

            <button
              type="submit"
              disabled={submitting || services.length === 0}
              className="w-full py-3 bg-blue-600 text-white font-medium rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {submitting ? '⏳ Отправка...' : '💾 Сохранить и отправить в Zabbix'}
            </button>
          </div>
        </form>

        <div className="mt-6 bg-blue-50 border border-blue-100 rounded-xl p-5">
          <h4 className="text-sm font-medium text-blue-800 flex items-center gap-2 mb-3">
            <span>ℹ️</span> Что произойдёт:
          </h4>
          <ul className="space-y-2 text-sm text-blue-700">
            <li>1. Запись сохранится в БД портала</li>
            <li>2. Через Zabbix API (<code className="bg-blue-100 px-1 rounded">sla.update</code>) будет добавлено исключение простоя</li>
            <li>3. В указанный период недоступность не учитывается в SLA</li>
          </ul>
        </div>
      </div>
    </div>
  );
};

export default NewWork;
