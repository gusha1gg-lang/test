import React from 'react';
import { PageType } from '../types';

interface SidebarProps {
  currentPage: PageType;
  onNavigate: (page: PageType) => void;
}

const menuItems: Array<{ id: PageType; icon: string; label: string }> = [
  { id: 'dashboard', icon: '📊', label: 'Панель управления' },
  { id: 'graph', icon: '🌐', label: 'SLA-услуги из Zabbix' },
  { id: 'new-work', icon: '➕', label: 'Новая работа' },
  { id: 'works-list', icon: '📋', label: 'Список работ' },
  { id: 'calendar', icon: '📅', label: 'Календарь' },
  { id: 'sla-report', icon: '📈', label: 'SLA Отчёт' },
  { id: 'users', icon: '👤', label: 'Пользователи' },
  { id: 'groups', icon: '👥', label: 'Группы и права' },
  { id: 'audit', icon: '📝', label: 'Аудит-лог' },
  { id: 'settings', icon: '⚙️', label: 'Настройки' },
];

const Sidebar: React.FC<SidebarProps> = ({ currentPage, onNavigate }) => {
  return (
    <aside className="fixed left-0 top-0 h-full w-[250px] bg-[#f8f9fa] border-r border-gray-200 flex flex-col z-50">
      <div className="p-5 border-b border-gray-200">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 bg-blue-600 rounded-lg flex items-center justify-center text-white font-bold text-lg">
            S
          </div>
          <div>
            <h1 className="text-lg font-bold text-gray-800">SLA Planner</h1>
            <p className="text-xs text-gray-500">Плановые работы</p>
          </div>
        </div>
      </div>

      <nav className="flex-1 py-4 overflow-y-auto">
        {menuItems.map(item => (
          <button
            key={item.id}
            onClick={() => onNavigate(item.id)}
            className={`w-full flex items-center gap-3 px-5 py-3 text-left text-sm transition-colors ${
              currentPage === item.id
                ? 'bg-[#e7f1ff] text-blue-700 font-medium border-r-3 border-blue-600'
                : 'text-gray-600 hover:bg-gray-100 hover:text-gray-800'
            }`}
          >
            <span className="text-lg">{item.icon}</span>
            <span>{item.label}</span>
          </button>
        ))}
      </nav>

      <div className="p-4 border-t border-gray-200">
        <div className="flex items-center gap-2 text-xs text-gray-400">
          <span className="w-2 h-2 bg-blue-400 rounded-full"></span>
          <span>FastAPI Backend</span>
        </div>
      </div>
    </aside>
  );
};

export default Sidebar;
