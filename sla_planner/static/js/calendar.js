// static/js/calendar.js — Календарь плановых работ

const Calendar = {
    currentYear: 2026,
    currentMonth: 9, // Сентябрь

    months: [
        'Январь', 'Февраль', 'Март', 'Апрель', 'Май', 'Июнь',
        'Июль', 'Август', 'Сентябрь', 'Октябрь', 'Ноябрь', 'Декабрь'
    ],

    weekdays: ['ПН', 'Вт', 'Ср', 'Чт', 'ПТ', 'Сб', 'Вс'],

    async init() {
        await this.loadWorks();
        this.render();
    },

    async loadWorks() {
        try {
            const response = await fetch(`/api/calendar?year=${this.currentYear}&month=${this.currentMonth}`);
            if (response.ok) {
                this.works = await response.json();
            } else {
                this.works = this.getDemoWorks();
            }
        } catch (e) {
            this.works = this.getDemoWorks();
        }
    },

    getDemoWorks() {
        return [
            { id: 1, service_name: "БД PostgreSQL", work_title: "Обновление PostgreSQL", start_time: "2026-09-15T22:00:00", end_time: "2026-09-16T06:00:00", status: "completed" },
            { id: 2, service_name: "Веб-сервер Nginx", work_title: "Обновление SSL", start_time: "2026-09-20T01:00:00", end_time: "2026-09-20T03:00:00", status: "planned" },
            { id: 3, service_name: "CRM Система", work_title: "ТО CRM", start_time: "2026-09-22T23:00:00", end_time: "2026-09-23T05:00:00", status: "planned" },
            { id: 4, service_name: "1С Бухгалтерия", work_title: "Обновление 1С", start_time: "2026-09-25T18:00:00", end_time: "2026-09-26T08:00:00", status: "in_progress" },
            { id: 5, service_name: "Почтовый сервер", work_title: "Миграция ящиков", start_time: "2026-09-18T20:00:00", end_time: "2026-09-19T08:00:00", status: "cancelled" },
        ];
    },

    prevMonth() {
        if (this.currentMonth === 1) {
            this.currentMonth = 12;
            this.currentYear--;
        } else {
            this.currentMonth--;
        }
        this.loadWorks().then(() => this.render());
    },

    nextMonth() {
        if (this.currentMonth === 12) {
            this.currentMonth = 1;
            this.currentYear++;
        } else {
            this.currentMonth++;
        }
        this.loadWorks().then(() => this.render());
    },

    render() {
        const container = document.getElementById('calendar-container');
        if (!container) return;

        const daysInMonth = new Date(this.currentYear, this.currentMonth, 0).getDate();
        const firstDay = new Date(this.currentYear, this.currentMonth - 1, 1).getDay();
        const startOffset = firstDay === 0 ? 6 : firstDay - 1;

        let html = `
            <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:20px;">
                <button class="btn" onclick="Calendar.prevMonth()">← Пред.</button>
                <h3 style="font-size:18px;font-weight:600;">${this.months[this.currentMonth - 1].toLowerCase()} ${this.currentYear}</h3>
                <button class="btn" onclick="Calendar.nextMonth()">След. →</button>
            </div>
            <div class="calendar-grid">
        `;

        // Заголовки дней
        this.weekdays.forEach(day => {
            html += `<div class="calendar-header">${day}</div>`;
        });

        // Пустые ячейки
        for (let i = 0; i < startOffset; i++) {
            html += `<div class="calendar-day" style="background:#f9f9f9;"></div>`;
        }

        // Дни месяца
        const today = new Date();
        for (let day = 1; day <= daysInMonth; day++) {
            const isToday = day === today.getDate() &&
                           this.currentMonth === today.getMonth() + 1 &&
                           this.currentYear === today.getFullYear();

            const dayWorks = this.getWorksForDay(day);

            html += `<div class="calendar-day ${isToday ? 'today' : ''}">`;
            html += `<div class="day-number">${day}</div>`;

            dayWorks.slice(0, 2).forEach(work => {
                html += `<div class="calendar-event ${work.status}" title="${work.work_title}">${work.work_title}</div>`;
            });

            if (dayWorks.length > 2) {
                html += `<div style="font-size:10px;color:#888;padding:2px 4px;">+${dayWorks.length - 2} ещё</div>`;
            }

            html += `</div>`;
        }

        html += `</div>`;

        // Легенда
        html += `
            <div class="legend">
                <span style="font-size:12px;color:#888;font-weight:500;">Легенда:</span>
                <div class="legend-item"><div class="legend-dot" style="background:#0d6efd;"></div> Запланировано</div>
                <div class="legend-item"><div class="legend-dot" style="background:#ffc107;"></div> В процессе</div>
                <div class="legend-item"><div class="legend-dot" style="background:#28a745;"></div> Завершено</div>
                <div class="legend-item"><div class="legend-dot" style="background:#dc3545;"></div> Отменено</div>
            </div>
        `;

        container.innerHTML = html;
    },

    getWorksForDay(day) {
        return this.works.filter(work => {
            const start = new Date(work.start_time);
            const end = new Date(work.end_time);
            const checkDate = new Date(this.currentYear, this.currentMonth - 1, day);
            const startDay = new Date(start.getFullYear(), start.getMonth(), start.getDate());
            const endDay = new Date(end.getFullYear(), end.getMonth(), end.getDate());
            return checkDate >= startDay && checkDate <= endDay;
        });
    }
};
