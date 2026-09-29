import React, { useState, useEffect } from 'react';
import { api } from '../api/client';

const Settings: React.FC = () => {
  const [settings, setSettings] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [testResult, setTestResult] = useState<{ connected: boolean; message: string } | null>(null);
  const [testing, setTesting] = useState(false);

  useEffect(() => {
    loadSettings();
  }, []);

  const loadSettings = async () => {
    setLoading(true);
    try {
      const data = await api.getSettings();
      setSettings(data);
    } catch (e) {
      setSettings(null);
    } finally {
      setLoading(false);
    }
  };

  const testConnection = async () => {
    setTesting(true);
    setTestResult(null);
    try {
      const result = await api.testZabbixConnection();
      setTestResult(result);
    } catch (e: any) {
      setTestResult({ connected: false, message: e.message || 'Ошибка подключения' });
    } finally {
      setTesting(false);
    }
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
      <div className="max-w-3xl mx-auto">
        <div className="mb-6">
          <h2 className="text-xl font-bold text-gray-800">⚙️ Настройки</h2>
          <p className="text-sm text-gray-500 mt-1">Текущие настройки бэкенда (из .env файла)</p>
        </div>

        {/* Zabbix */}
        <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6 mb-6">
          <h3 className="text-lg font-semibold text-gray-800 mb-4">🔌 Подключение к Zabbix</h3>
          {settings ? (
            <div className="space-y-3">
              <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                <span className="text-sm text-gray-600">URL API</span>
                <span className="text-sm font-mono text-gray-800">{settings.zabbix_url}</span>
              </div>
              <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                <span className="text-sm text-gray-600">Пользователь</span>
                <span className="text-sm font-medium text-gray-800">{settings.zabbix_username}</span>
              </div>
              <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                <span className="text-sm text-gray-600">Имя SLA</span>
                <span className="text-sm font-medium text-gray-800">{settings.zabbix_sla_name}</span>
              </div>
            </div>
          ) : (
            <p className="text-red-600">Не удалось загрузить настройки. Проверьте что бэкенд запущен.</p>
          )}

          <div className="mt-4 flex items-center gap-3">
            <button
              onClick={testConnection}
              disabled={testing}
              className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 text-sm font-medium disabled:opacity-50"
            >
              {testing ? '⏳ Проверка...' : '🔍 Проверить подключение'}
            </button>
            {testResult && (
              <span className={`text-sm ${testResult.connected ? 'text-green-600' : 'text-red-600'}`}>
                {testResult.connected ? '✅' : '❌'} {testResult.message}
              </span>
            )}
          </div>
        </div>

        {/* Database */}
        <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6 mb-6">
          <h3 className="text-lg font-semibold text-gray-800 mb-4">🗄️ База данных</h3>
          <div className="p-3 bg-gray-50 rounded-lg">
            <p className="text-sm text-gray-600 mb-1">Строка подключения:</p>
            <code className="text-xs text-gray-800 font-mono break-all">{settings?.database_url || '—'}</code>
          </div>
          <p className="text-xs text-gray-500 mt-3">
            Измените <code className="bg-gray-200 px-1 rounded">DATABASE_URL</code> в файле .env для смены БД.
          </p>
        </div>

        {/* Auth */}
        <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6 mb-6">
          <h3 className="text-lg font-semibold text-gray-800 mb-4">🔐 Авторизация</h3>
          <div className="p-3 bg-gray-50 rounded-lg">
            <p className="text-sm text-gray-600">
              Режим: <strong className="text-gray-800">{settings?.auth_mode || '—'}</strong>
            </p>
          </div>
          <p className="text-xs text-gray-500 mt-3">
            Измените <code className="bg-gray-200 px-1 rounded">AUTH_MODE</code> в файле .env для переключения на ADFS/OAuth2.
          </p>
        </div>

        {/* Info */}
        <div className="bg-blue-50 border border-blue-100 rounded-xl p-5">
          <h4 className="text-sm font-medium text-blue-800 mb-2">ℹ️ Как изменить настройки</h4>
          <p className="text-sm text-blue-700">
            Все настройки хранятся в файле <code className="bg-blue-100 px-1 rounded">.env</code> в папке бэкенда.
            После изменения перезапустите FastAPI сервер.
          </p>
        </div>
      </div>
    </div>
  );
};

export default Settings;
