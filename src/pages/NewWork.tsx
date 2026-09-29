import React, { useState, useEffect } from 'react';
import { demoServices } from '../data/mockData';

interface NewWorkProps {
  preselectedService?: string;
}

const NewWork: React.FC<NewWorkProps> = ({ preselectedService }) => {
  const [serviceName, setServiceName] = useState(preselectedService || '');
  const [workTitle, setWorkTitle] = useState('');
  const [description, setDescription] = useState('');
  const [startDate, setStartDate] = useState('');
  const [startTime, setStartTime] = useState('22:00');
  const [endDate, setEndDate] = useState('');
  const [endTime, setEndTime] = useState('06:00');
  const [submitted, setSubmitted] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    if (preselectedService) {
      setServiceName(preselectedService);
    }
  }, [preselectedService]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setError('');

    // Валидация
    if (!serviceName) {
      setError('Выберите сервис из графа');
      return;
    }
    if (!workTitle) {
      setError('Укажите название работы');
      return;
    }
    if (!startDate || !startTime || !endDate || !endTime) {
      setError('Укажите дату и время начала и окончания');
      return;
    }

    const start = new Date(`${startDate}T${startTime}`);
    const end = new Date(`${endDate}T${endTime}`);
    if (end <= start) {
      setError('Время окончания должно быть позже времени начала');
      return;
    }

    setSubmitted(true);
  };

  const handleReset = () => {
    setServiceName('');
    setWorkTitle('');
    setDescription('');
    setStartDate('');
    setStartTime('22:00');
    setEndDate('');
    setEndTime('06:00');
    setSubmitted(false);
    setError('');
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
              Плановая работа «{workTitle}» для сервиса «{serviceName}» успешно сохранена.
            </p>
            <div className="bg-blue-50 border border-blue-100 rounded-lg p-4 mb-6 text-left">
              <h4 className="text-sm font-medium text-blue-800 mb-2">ℹ️ Статус отправки в Zabbix:</h4>
              <p className="text-sm text-blue-700">
                В демо-режиме исключение SLA не создаётся. При подключении к реальному Zabbix серверу 
                исключение будет добавлено автоматически через метод <code className="bg-blue-100 px-1 rounded">sla.update</code>.
              </p>
            </div>
            <div className="flex gap-3 justify-center">
              <button
                onClick={handleReset}
                className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
              >
                + Ещё одна работа
              </button>
              <button
                onClick={() => window.location.reload()}
                className="px-6 py-2 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300 transition-colors"
              >
                К списку работ
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
          <p className="text-sm text-gray-500 mt-1">Заполните форму для создания новой плановой работы</p>
        </div>

        <form onSubmit={handleSubmit} className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
          {error && (
            <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg text-sm text-red-700">
              ❌ {error}
            </div>
          )}

          <div className="space-y-5">
            {/* Сервис */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Имя сервиса / ИС <span className="text-red-500">*</span>
              </label>
              <select
                value={serviceName}
                onChange={e => setServiceName(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none"
              >
                <option value="">— Выберите сервис —</option>
                {demoServices.map(s => (
                  <option key={s.id} value={s.name}>
                    {s.name} {s.status === 'problem' ? '🔴' : s.status === 'warning' ? '🟡' : '🟢'}
                  </option>
                ))}
              </select>
              <p className="text-xs text-gray-400 mt-1">
                Можно также выбрать кликом по узлу на странице «Плановые из графа»
              </p>
            </div>

            {/* Название работы */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Название работы <span className="text-red-500">*</span>
              </label>
              <input
                type="text"
                value={workTitle}
                onChange={e => setWorkTitle(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none"
                placeholder="Например: Обновление PostgreSQL"
              />
            </div>

            {/* Описание */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Описание</label>
              <textarea
                value={description}
                onChange={e => setDescription(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none resize-none"
                rows={4}
                placeholder="Описание плановых работ..."
              />
            </div>

            {/* Даты и время */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Дата и время начала <span className="text-red-500">*</span>
                </label>
                <div className="flex gap-2">
                  <input
                    type="date"
                    value={startDate}
                    onChange={e => setStartDate(e.target.value)}
                    className="flex-1 px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none"
                  />
                  <input
                    type="time"
                    value={startTime}
                    onChange={e => setStartTime(e.target.value)}
                    className="w-28 px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none"
                  />
                </div>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Дата и время окончания <span className="text-red-500">*</span>
                </label>
                <div className="flex gap-2">
                  <input
                    type="date"
                    value={endDate}
                    onChange={e => setEndDate(e.target.value)}
                    className="flex-1 px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none"
                  />
                  <input
                    type="time"
                    value={endTime}
                    onChange={e => setEndTime(e.target.value)}
                    className="w-28 px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none"
                  />
                </div>
              </div>
            </div>

            {/* Кнопка отправки */}
            <button
              type="submit"
              className="w-full py-3 bg-blue-600 text-white font-medium rounded-lg hover:bg-blue-700 transition-colors text-sm"
            >
              💾 Сохранить и отправить в Zabbix
            </button>
          </div>
        </form>

        {/* Информационный блок */}
        <div className="mt-6 bg-blue-50 border border-blue-100 rounded-xl p-5">
          <h4 className="text-sm font-medium text-blue-800 flex items-center gap-2 mb-3">
            <span>ℹ️</span> Что произойдёт при отправке в Zabbix:
          </h4>
          <ul className="space-y-2 text-sm text-blue-700">
            <li className="flex items-start gap-2">
              <span className="mt-1">1.</span>
              <span>Запись о плановой работе будет сохранена в базу данных портала</span>
            </li>
            <li className="flex items-start gap-2">
              <span className="mt-1">2.</span>
              <span>Через Zabbix API (<code className="bg-blue-100 px-1 rounded">sla.update</code>) будет добавлено исключение простоя</span>
            </li>
            <li className="flex items-start gap-2">
              <span className="mt-1">3.</span>
              <span>В указанный период недоступность сервиса не будет учитываться в SLA-отчёте</span>
            </li>
            <li className="flex items-start gap-2">
              <span className="mt-1">4.</span>
              <span>Исключение будет названо: «ПР: {workTitle || '[название работы]'} ({serviceName || '[сервис]'})»</span>
            </li>
          </ul>
        </div>
      </div>
    </div>
  );
};

export default NewWork;
