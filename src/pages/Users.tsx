import React, { useState, useEffect } from 'react';
import { api } from '../api/client';

const Users: React.FC = () => {
  const [users, setUsers] = useState<any[]>([]);
  const [groups, setGroups] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [editingUser, setEditingUser] = useState<any>(null);
  const [error, setError] = useState('');

  // Форма
  const [username, setUsername] = useState('');
  const [email, setEmail] = useState('');
  const [fullName, setFullName] = useState('');
  const [isAdmin, setIsAdmin] = useState(false);
  const [selectedGroups, setSelectedGroups] = useState<number[]>([]);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    setLoading(true);
    try {
      const [usersData, groupsData] = await Promise.all([
        api.getUsers(),
        api.getGroups(),
      ]);
      setUsers(usersData);
      setGroups(groupsData);
    } catch (e: any) {
      setError(e.message || 'Ошибка загрузки');
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');

    try {
      if (editingUser) {
        await api.updateUser(editingUser.id, {
          email,
          full_name: fullName,
          is_admin: isAdmin,
          group_ids: selectedGroups,
        });
      } else {
        await api.createUser({
          username,
          email,
          full_name: fullName,
          is_admin: isAdmin,
          group_ids: selectedGroups,
        });
      }
      resetForm();
      await loadData();
    } catch (e: any) {
      setError(e.message || 'Ошибка сохранения');
    }
  };

  const handleEdit = (user: any) => {
    setEditingUser(user);
    setUsername(user.username);
    setEmail(user.email || '');
    setFullName(user.full_name || '');
    setIsAdmin(user.is_admin);
    setSelectedGroups(user.groups?.map((g: any) => g.id) || []);
    setShowForm(true);
  };

  const handleDelete = async (id: number, username: string) => {
    if (!confirm(`Удалить пользователя "${username}"?`)) return;
    try {
      await api.deleteUser(id);
      await loadData();
    } catch (e: any) {
      alert(`Ошибка: ${e.message}`);
    }
  };

  const resetForm = () => {
    setShowForm(false);
    setEditingUser(null);
    setUsername('');
    setEmail('');
    setFullName('');
    setIsAdmin(false);
    setSelectedGroups([]);
    setError('');
  };

  const toggleGroup = (groupId: number) => {
    setSelectedGroups(prev =>
      prev.includes(groupId)
        ? prev.filter(id => id !== groupId)
        : [...prev, groupId]
    );
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
          <h2 className="text-xl font-bold text-gray-800">👤 Пользователи</h2>
          <p className="text-sm text-gray-500 mt-1">Управление пользователями системы</p>
        </div>
        <button
          onClick={() => setShowForm(true)}
          className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 text-sm font-medium"
        >
          + Новый пользователь
        </button>
      </div>

      {error && (
        <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg text-sm text-red-700">
          ❌ {error}
        </div>
      )}

      {/* Форма создания/редактирования */}
      {showForm && (
        <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6 mb-6">
          <h3 className="text-lg font-semibold text-gray-800 mb-4">
            {editingUser ? '✏️ Редактирование пользователя' : '➕ Новый пользователь'}
          </h3>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Логин <span className="text-red-500">*</span>
                </label>
                <input
                  type="text"
                  value={username}
                  onChange={e => setUsername(e.target.value)}
                  disabled={!!editingUser}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm disabled:bg-gray-100"
                  required
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Email</label>
                <input
                  type="email"
                  value={email}
                  onChange={e => setEmail(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm"
                />
              </div>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">ФИО</label>
              <input
                type="text"
                value={fullName}
                onChange={e => setFullName(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm"
                placeholder="Иванов Иван Иванович"
              />
            </div>
            <div className="flex items-center gap-2">
              <input
                type="checkbox"
                id="is_admin"
                checked={isAdmin}
                onChange={e => setIsAdmin(e.target.checked)}
                className="w-4 h-4"
              />
              <label htmlFor="is_admin" className="text-sm text-gray-700">
                Администратор (полный доступ ко всем функциям)
              </label>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Группы</label>
              {groups.length === 0 ? (
                <p className="text-sm text-gray-500">Нет доступных групп. Создайте группы на странице "Группы и права".</p>
              ) : (
                <div className="flex flex-wrap gap-2">
                  {groups.map(group => (
                    <button
                      key={group.id}
                      type="button"
                      onClick={() => toggleGroup(group.id)}
                      className={`px-3 py-1 rounded-full text-sm border transition-colors ${
                        selectedGroups.includes(group.id)
                          ? 'bg-blue-100 border-blue-300 text-blue-800'
                          : 'bg-white border-gray-300 text-gray-600 hover:bg-gray-50'
                      }`}
                    >
                      {group.name}
                    </button>
                  ))}
                </div>
              )}
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

      {/* Таблица пользователей */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
        {users.length === 0 ? (
          <div className="text-center py-12 text-gray-500">
            <p className="text-3xl mb-2">👤</p>
            <p>Нет пользователей. Создайте первого пользователя.</p>
          </div>
        ) : (
          <table className="w-full">
            <thead>
              <tr className="bg-gray-50 border-b border-gray-200">
                <th className="text-left px-4 py-3 text-xs font-medium text-gray-500 uppercase">Пользователь</th>
                <th className="text-left px-4 py-3 text-xs font-medium text-gray-500 uppercase">Email</th>
                <th className="text-left px-4 py-3 text-xs font-medium text-gray-500 uppercase">Группы</th>
                <th className="text-left px-4 py-3 text-xs font-medium text-gray-500 uppercase">Роль</th>
                <th className="text-left px-4 py-3 text-xs font-medium text-gray-500 uppercase">Статус</th>
                <th className="text-left px-4 py-3 text-xs font-medium text-gray-500 uppercase">Действия</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {users.map(user => (
                <tr key={user.id} className="hover:bg-gray-50">
                  <td className="px-4 py-3">
                    <div>
                      <p className="text-sm font-medium text-gray-800">{user.username}</p>
                      {user.full_name && <p className="text-xs text-gray-500">{user.full_name}</p>}
                    </div>
                  </td>
                  <td className="px-4 py-3 text-sm text-gray-600">{user.email || '—'}</td>
                  <td className="px-4 py-3">
                    <div className="flex flex-wrap gap-1">
                      {user.groups?.length > 0 ? (
                        user.groups.map((g: any) => (
                          <span key={g.id} className="px-2 py-0.5 bg-blue-50 text-blue-700 text-xs rounded-full">
                            {g.name}
                          </span>
                        ))
                      ) : (
                        <span className="text-xs text-gray-400">Нет групп</span>
                      )}
                    </div>
                  </td>
                  <td className="px-4 py-3">
                    {user.is_admin ? (
                      <span className="px-2 py-1 bg-purple-100 text-purple-800 text-xs rounded-full">Админ</span>
                    ) : (
                      <span className="px-2 py-1 bg-gray-100 text-gray-600 text-xs rounded-full">Пользователь</span>
                    )}
                  </td>
                  <td className="px-4 py-3">
                    {user.is_active ? (
                      <span className="text-green-600 text-sm">✅ Активен</span>
                    ) : (
                      <span className="text-red-600 text-sm">⛔ Заблокирован</span>
                    )}
                  </td>
                  <td className="px-4 py-3">
                    <div className="flex items-center gap-2">
                      <button
                        onClick={() => handleEdit(user)}
                        className="px-2 py-1 text-xs bg-blue-100 text-blue-800 rounded hover:bg-blue-200"
                      >
                        ✏️
                      </button>
                      <button
                        onClick={() => handleDelete(user.id, user.username)}
                        className="px-2 py-1 text-xs bg-red-100 text-red-800 rounded hover:bg-red-200"
                      >
                        🗑️
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
};

export default Users;
