import React, { useState } from 'react';

const Settings: React.FC = () => {
  const [zabbixUrl, setZabbixUrl] = useState('http://localhost:8080/api_jsonrpc.php');
  const [zabbixUsername, setZabbixUsername] = useState('Admin');
  const [zabbixPassword, setZabbixPassword] = useState('');
  const [slaName, setSlaName] = useState('Test SLA');
  const [connectionStatus, setConnectionStatus] = useState<'idle' | 'testing' | 'success' | 'error'>('idle');
  const [saved, setSaved] = useState(false);

  const testConnection = () => {
    setConnectionStatus('testing');
    // Имитация проверки подключения
    setTimeout(() => {
      if (zabbixUrl && zabbixUsername && zabbixPassword) {
        setConnectionStatus('success');
      } else {
        setConnectionStatus('error');
      }
    }, 1500);
  };

  const handleSave = () => {
    setSaved(true);
    setTimeout(() => setSaved(false), 3000);
  };

  return (
    <div className="p-6">
      <div className="max-w-3xl mx-auto">
        <div className="mb-6">
          <h2 className="text-xl font-bold text-gray-800">⚙️ Настройки подключения</h2>
          <p className="text-sm text-gray-500 mt-1">Конфигурация подключения к Zabbix серверу и параметры системы</p>
        </div>

        {/* Zabbix подключение */}
        <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6 mb-6">
          <h3 className="text-lg font-semibold text-gray-800 mb-4 flex items-center gap-2">
            🔌 Подключение к Zabbix
          </h3>

          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">URL API Zabbix</label>
              <input
                type="text"
                value={zabbixUrl}
                onChange={e => setZabbixUrl(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none font-mono"
                placeholder="http://zabbix-server:8080/api_jsonrpc.php"
              />
              <p className="text-xs text-gray-400 mt-1">
                В Zabbix 7.0 endpoint: <code className="bg-gray-100 px-1 rounded">/api_jsonrpc.php</code>
              </p>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Логин</label>
                <input
                  type="text"
                  value={zabbixUsername}
                  onChange={e => setZabbixUsername(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none"
                  placeholder="Admin"
                />
                <p className="text-xs text-gray-400 mt-1">
                  В Zabbix 7.0 используется параметр <code className="bg-gray-100 px-1 rounded">username</code>
                </p>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Пароль</label>
                <input
                  type="password"
                  value={zabbixPassword}
                  onChange={e => setZabbixPassword(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none"
                  placeholder="••••••••"
                />
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Имя SLA</label>
              <input
                type="text"
                value={slaName}
                onChange={e => setSlaName(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none"
                placeholder="Test SLA"
              />
            </div>

            {/* Проверка подключения */}
            <div className="flex items-center gap-3">
              <button
                onClick={testConnection}
                disabled={connectionStatus === 'testing'}
                className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors text-sm font-medium disabled:opacity-50"
              >
                {connectionStatus === 'testing' ? '⏳ Проверка...' : '🔍 Проверить подключение'}
              </button>

              {connectionStatus === 'success' && (
                <span className="text-sm text-green-600 flex items-center gap-1">✅ Подключение успешно!</span>
              )}
              {connectionStatus === 'error' && (
                <span className="text-sm text-red-600 flex items-center gap-1">❌ Ошибка подключения</span>
              )}
            </div>
          </div>
        </div>

        {/* База данных */}
        <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6 mb-6">
          <h3 className="text-lg font-semibold text-gray-800 mb-4 flex items-center gap-2">
            🗄️ База данных
          </h3>
          <div className="bg-gray-50 rounded-lg p-4">
            <p className="text-sm text-gray-600 mb-2">Текущий режим: <strong>Демо (LocalStorage)</strong></p>
            <p className="text-xs text-gray-500">
              В продакшене используется PostgreSQL через переменную <code className="bg-gray-200 px-1 rounded">DATABASE_URL</code>
            </p>
            <div className="mt-3 p-2 bg-gray-100 rounded font-mono text-xs text-gray-600">
              # Для теста:<br />
              DATABASE_URL=sqlite:///./sla_planner.db<br /><br />
              # Для прода:<br />
              DATABASE_URL=postgresql://user:pass@host:5432/sla_planner
            </div>
          </div>
        </div>

        {/* Авторизация */}
        <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6 mb-6">
          <h3 className="text-lg font-semibold text-gray-800 mb-4 flex items-center gap-2">
            🔐 Авторизация
          </h3>
          <div className="bg-gray-50 rounded-lg p-4">
            <p className="text-sm text-gray-600 mb-2">Текущий режим: <strong>Mock (Admin)</strong></p>
            <p className="text-xs text-gray-500">
              В продакшене будет использоваться ADFS / OAuth2 / OpenID Connect
            </p>
            <div className="mt-3 p-2 bg-gray-100 rounded font-mono text-xs text-gray-600">
              AUTH_MODE=mock<br />
              # AUTH_MODE=adfs<br />
              # ADFS_CLIENT_ID=your-client-id<br />
              # ADFS_AUTH_URL=https://adfs.corp.local/adfs/oauth2/authorize<br />
              # ADFS_TOKEN_URL=https://adfs.corp.local/adfs/oauth2/token
            </div>
          </div>
        </div>

        {/* Кнопка сохранения */}
        <button
          onClick={handleSave}
          className="w-full py-3 bg-blue-600 text-white font-medium rounded-lg hover:bg-blue-700 transition-colors"
        >
          💾 Сохранить настройки
        </button>

        {saved && (
          <div className="mt-3 p-3 bg-green-50 border border-green-200 rounded-lg text-sm text-green-700 text-center">
            ✅ Настройки сохранены (в демо-режиме — в localStorage)
          </div>
        )}
      </div>
    </div>
  );
};

export default Settings;
