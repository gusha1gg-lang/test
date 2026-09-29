import React, { useState, useEffect } from 'react';
import { api, PlannedWork } from '../api/client';

interface CalendarProps {
  onNavigateToNewWork: () => void;
}

const MONTHS = ['Январь', 'Февраль', 'Март', 'Апрель', 'Май', 'Июнь', 'Июль', 'Август', 'Сентябрь', 'Октябрь', 'Ноябрь', 'Декабрь'];
const WEEKDAYS = ['ПН', 'Вт', 'Ср', 'Чт', 'ПТ', 'Сб', 'Вс'];

const Calendar: React.FC<CalendarProps> = ({ onNavigateToNewWork }) => {
  const now = new Date();
  const [year, setYear] = useState(now.getFullYear());
  const [month, setMonth] = useState(now.getMonth() + 1);
  const [works, setWorks] = useState<PlannedWork[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadWorks();
  }, [year, month]);

  const loadWorks = async () => {
    setLoading(true);
    try {
      const data = await api.getCalendarWorks(year, month);
      setWorks(data);
    } catch (e) {
      setWorks([]);
    } finally {
      setLoading(false);
    }
  };

  const prevMonth = () => {
    if (month === 1) { setMonth(12); setYear(year - 1); }
    else setMonth(month - 1);
  };

  const nextMonth = () => {
    if (month === 12) { setMonth(1); setYear(year + 1); }
    else setMonth(month + 1);
  };

  const daysInMonth = new Date(year, month, 0).getDate();
  const firstDay = new Date(year, month - 1, 1).getDay();
  const startOffset = firstDay === 0 ? 6 : firstDay - 1;

  const getWorksForDay = (day: number) => {
    return works.filter(w => {
      const start = new Date(w.start_time);
      const end = new Date(w.end_time);
      const check = new Date(year, month - 1, day);
      return check >= new Date(start.getFullYear(), start.getMonth(), start.getDate()) &&
             check <= new Date(end.getFullYear(), end.getMonth(), end.getDate());
    });
  };

  const getStatusColor = (status: string): string => {
    const c: Record<string, string> = { planned: '#0d6efd', in_progress: '#ffc107', completed: '#28a745', cancelled: '#dc3545' };
    return c[status] || '#6c757d';
  };

  const getStatusLabel = (status: string): string => {
    const l: Record<string, string> = { planned: 'Запланировано', in_progress: 'В процессе', completed: 'Завершено', cancelled: 'Отменено' };
    return l[status] || status;
  };

  return (
    <div className="p-6">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h2 className="text-xl font-bold text-gray-800">📅 Календарь плановых работ</h2>
          <p className="text-sm text-gray-500 mt-1">Визуальное представление графика работ</p>
        </div>
        <button onClick={onNavigateToNewWork} className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 text-sm font-medium">
          + Новая работа
        </button>
      </div>

      <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
        <div className="flex items-center justify-between mb-6">
          <button onClick={prevMonth} className="px-3 py-2 text-gray-600 hover:bg-gray-100 rounded-lg">← Пред.</button>
          <h3 className="text-lg font-semibold text-gray-800">{MONTHS[month - 1].toLowerCase()} {year}</h3>
          <button onClick={nextMonth} className="px-3 py-2 text-gray-600 hover:bg-gray-100 rounded-lg">След. →</button>
        </div>

        <div className="grid grid-cols-7 gap-1 mb-2">
          {WEEKDAYS.map(d => <div key={d} className="text-center text-xs font-medium text-gray-500 py-2">{d}</div>)}
        </div>

        {loading ? (
          <div className="text-center py-12 text-gray-500">Загрузка...</div>
        ) : (
          <div className="grid grid-cols-7 gap-1">
            {Array.from({ length: startOffset }).map((_, i) => (
              <div key={`e${i}`} className="h-24 bg-gray-50 rounded border border-gray-100"></div>
            ))}
            {Array.from({ length: daysInMonth }).map((_, i) => {
              const day = i + 1;
              const dayWorks = getWorksForDay(day);
              const isToday = day === now.getDate() && month === now.getMonth() + 1 && year === now.getFullYear();
              return (
                <div key={day} className={`h-24 p-1 border rounded overflow-hidden ${isToday ? 'border-blue-300 bg-blue-50' : 'border-gray-100 bg-white'}`}>
                  <div className={`text-xs font-medium mb-1 ${isToday ? 'text-blue-600' : 'text-gray-600'}`}>{day}</div>
                  <div className="space-y-0.5">
                    {dayWorks.slice(0, 2).map(w => (
                      <div key={w.id} className="text-[10px] text-white px-1 py-0.5 rounded truncate" style={{ backgroundColor: getStatusColor(w.status) }} title={`${w.work_title} — ${w.service_name}`}>
                        {w.work_title}
                      </div>
                    ))}
                    {dayWorks.length > 2 && <div className="text-[10px] text-gray-500 px-1">+{dayWorks.length - 2}</div>}
                  </div>
                </div>
              );
            })}
          </div>
        )}

        <div className="mt-6 pt-4 border-t border-gray-100 flex items-center gap-6 flex-wrap">
          <span className="text-xs text-gray-500 font-medium">Легенда:</span>
          {['planned', 'in_progress', 'completed', 'cancelled'].map(s => (
            <div key={s} className="flex items-center gap-2">
              <span className="w-3 h-3 rounded" style={{ backgroundColor: getStatusColor(s) }}></span>
              <span className="text-xs text-gray-600">{getStatusLabel(s)}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default Calendar;
