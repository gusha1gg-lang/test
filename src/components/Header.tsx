import React from 'react';
import { PageType } from '../types';

interface HeaderProps {
  currentPage: PageType;
}

const pageTitles: Record<PageType, string> = {
  dashboard: '📊 Панель управления',
  graph: '🌐 SLA-услуги из Zabbix',
  'new-work': '➕ Регистрация плановой работы',
  'works-list': '📋 Список плановых работ',
  calendar: '📅 Календарь плановых работ',
  'sla-report': '📈 SLA Отчёт',
  settings: '⚙️ Настройки',
};

function getFormattedDate(): string {
  const now = new Date();
  const options: Intl.DateTimeFormatOptions = {
    weekday: 'long',
    year: 'numeric',
    month: 'long',
    day: 'numeric',
  };
  return now.toLocaleDateString('ru-RU', options);
}

const Header: React.FC<HeaderProps> = ({ currentPage }) => {
  return (
    <header className="h-16 bg-white border-b border-gray-200 flex items-center justify-between px-6 shadow-sm">
      <h2 className="text-lg font-semibold text-gray-800">
        {pageTitles[currentPage]}
      </h2>
      <div className="flex items-center gap-4">
        <span className="text-sm text-gray-500">{getFormattedDate()}</span>
        <div className="w-9 h-9 bg-blue-600 rounded-full flex items-center justify-center text-white font-bold text-sm">
          А
        </div>
      </div>
    </header>
  );
};

export default Header;
