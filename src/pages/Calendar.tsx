import React, { useState } from 'react';
import { demoWorks } from '../data/mockData';
import { PlannedWork } from '../types';

const MONTHS = [
  'Январь', 'Февраль', 'Март', 'Апрель', 'Май', 'Июнь',
  'Июль', 'Август', 'Сентябрь', 'Октябрь', 'Ноябрь', 'Декабрь'
];

const WEEKDAYS = ['ПН', 'Вт', 'Ср', 'Чт', 'ПТ', 'Сб', 'Вс'];

const Calendar: React.FC<{ onNavigateToNewWork: () => void }> = ({ onNavigateToNewWork }) => {
  const [currentYear, setCurrentYear] = useState(2026);
  const [currentMonth, setCurrentMonth] = useState(9); // Сентябрь (1-indexed)

  const works = demoWorks.filter(work => {
    const start = new Date(work.startTime);
    return start.getFullYear() === currentYear && start.getMonth() === currentMonth - 1;
  });

  const prevMonth = () => {
    if (currentMonth === 1) {
      setCurrentMonth(12);
      setCurrentYear(currentYear - 1);
    } else {
      setCurrentMonth(currentMonth - 1);
    }
  };

  const nextMonth = () => {
    if (currentMonth === 12) {
      setCurrentMonth(1);
      setCurrentYear(currentYear + 1);
    } else {
      setCurrentMonth(currentMonth + 1);
    }
  };

  // Получаем дни месяца
  const daysInMonth = new Date(currentYear, currentMonth, 0).getDate();
  const firstDayOfWeek = new Date(currentYear, currentMonth - 1, 1).getDay();
  // В JS воскресенье = 0, нам нужно ПН = 0
  const startOffset = firstDayOfWeek === 0 ? 6 : firstDayOfWeek - 1;

  const getWorksForDay = (day: number): PlannedWork[] => {
    return works.filter(work => {
      const start = new Date(work.startTime);
      const end = new Date(work.endTime);
      const checkDate = new Date(currentYear, currentMonth - 1, day);
      return checkDate >= new Date(start.getFullYear(), start.getMonth(), start.getDate()) &&
             checkDate <= new Date(end.getFullYear(), end.getMonth(), end.getDate());
    });
  };

  const getStatusColor = (status: PlannedWork['status']): string => {
    const colors: Record<PlannedWork['status'], string> = {
      planned: '#0d6efd',
      in_progress: '#ffc107',
      completed: '#28a745',
      cancelled: '#dc3545',
    };
    return colors[status];
  };

  const getStatusLabel = (status: PlannedWork['status']): string => {
    const labels: Record<PlannedWork['status'], string> = {
      planned: 'Запланировано',
      in_progress: 'В процессе',
      completed: 'Завершено',
      cancelled: 'Отменено',
    };
    return labels[status];
  };

  return (
    <div className="p-6">
      {/* Заголовок */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h2 className="text-xl font-bold text-gray-800">📅 Календарь плановых работ</h2>
          <p className="text-sm text-gray-500 mt-1">Визуальное представление графика работ</p>
        </div>
        <button
          onClick={onNavigateToNewWork}
          className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors text-sm font-medium"
        >
          + Новая работа
        </button>
      </div>

      {/* Календарь */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
        {/* Навигация */}
        <div className="flex items-center justify-between mb-6">
          <button
            onClick={prevMonth}
            className="px-3 py-2 text-gray-600 hover:bg-gray-100 rounded-lg transition-colors"
          >
            ← Пред.
          </button>
          <h3 className="text-lg font-semibold text-gray-800">
            {MONTHS[currentMonth - 1].toLowerCase()} {currentYear}
          </h3>
          <button
            onClick={nextMonth}
            className="px-3 py-2 text-gray-600 hover:bg-gray-100 rounded-lg transition-colors"
          >
            След. →
          </button>
        </div>

        {/* Заголовки дней недели */}
        <div className="grid grid-cols-7 gap-1 mb-2">
          {WEEKDAYS.map(day => (
            <div key={day} className="text-center text-xs font-medium text-gray-500 py-2">
              {day}
            </div>
          ))}
        </div>

        {/* Сетка календаря */}
        <div className="grid grid-cols-7 gap-1">
          {/* Пустые ячейки до начала месяца */}
          {Array.from({ length: startOffset }).map((_, i) => (
            <div key={`empty-${i}`} className="h-24 bg-gray-50 rounded border border-gray-100"></div>
          ))}

          {/* Дни месяца */}
          {Array.from({ length: daysInMonth }).map((_, i) => {
            const day = i + 1;
            const dayWorks = getWorksForDay(day);
            const isToday = day === new Date().getDate() && 
                           currentMonth === new Date().getMonth() + 1 && 
                           currentYear === new Date().getFullYear();

            return (
              <div
                key={day}
                className={`h-24 p-1 border rounded overflow-hidden ${
                  isToday ? 'border-blue-300 bg-blue-50' : 'border-gray-100 bg-white'
                }`}
              >
                <div className={`text-xs font-medium mb-1 ${isToday ? 'text-blue-600' : 'text-gray-600'}`}>
                  {day}
                </div>
                <div className="space-y-0.5">
                  {dayWorks.slice(0, 2).map(work => (
                    <div
                      key={work.id}
                      className="text-[10px] text-white px-1 py-0.5 rounded truncate"
                      style={{ backgroundColor: getStatusColor(work.status) }}
                      title={`${work.workTitle} — ${work.serviceName}`}
                    >
                      {work.workTitle}
                    </div>
                  ))}
                  {dayWorks.length > 2 && (
                    <div className="text-[10px] text-gray-500 px-1">
                      +{dayWorks.length - 2} ещё
                    </div>
                  )}
                </div>
              </div>
            );
          })}
        </div>

        {/* Легенда */}
        <div className="mt-6 pt-4 border-t border-gray-100 flex items-center gap-6 flex-wrap">
          <span className="text-xs text-gray-500 font-medium">Легенда:</span>
          <div className="flex items-center gap-2">
            <span className="w-3 h-3 rounded" style={{ backgroundColor: '#0d6efd' }}></span>
            <span className="text-xs text-gray-600">{getStatusLabel('planned')}</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="w-3 h-3 rounded" style={{ backgroundColor: '#ffc107' }}></span>
            <span className="text-xs text-gray-600">{getStatusLabel('in_progress')}</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="w-3 h-3 rounded" style={{ backgroundColor: '#28a745' }}></span>
            <span className="text-xs text-gray-600">{getStatusLabel('completed')}</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="w-3 h-3 rounded" style={{ backgroundColor: '#dc3545' }}></span>
            <span className="text-xs text-gray-600">{getStatusLabel('cancelled')}</span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Calendar;
