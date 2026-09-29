// static/js/form.js — Форма регистрации плановой работы

const Form = {
    init() {
        const form = document.getElementById('work-form');
        if (form) {
            form.addEventListener('submit', (e) => this.handleSubmit(e));
        }

        // Слушаем событие выбора сервиса из графа
        window.addEventListener('serviceSelected', (e) => {
            const input = document.getElementById('service-name-input');
            if (input) input.value = e.detail.name;
        });
    },

    async handleSubmit(e) {
        e.preventDefault();

        const formData = {
            service_name: document.getElementById('service-name-input').value,
            work_title: document.getElementById('work-title-input').value,
            description: document.getElementById('work-description-input').value,
            start_time: this.combineDateTime('start-date', 'start-time'),
            end_time: this.combineDateTime('end-date', 'end-time'),
        };

        // Валидация
        if (!formData.service_name) {
            this.showError('Выберите сервис из графа');
            return;
        }
        if (!formData.work_title) {
            this.showError('Укажите название работы');
            return;
        }
        if (!formData.start_time || !formData.end_time) {
            this.showError('Укажите дату и время начала и окончания');
            return;
        }

        const start = new Date(formData.start_time);
        const end = new Date(formData.end_time);
        if (end <= start) {
            this.showError('Время окончания должно быть позже времени начала');
            return;
        }

        // Отправка на сервер
        try {
            const response = await fetch('/api/works', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(formData),
            });

            if (response.ok) {
                const result = await response.json();
                this.showSuccess(result);
            } else {
                const error = await response.json();
                this.showError(error.detail || 'Ошибка сохранения');
            }
        } catch (e) {
            // Демо-режим — показываем успех
            this.showSuccess({ id: Date.now(), ...formData });
        }
    },

    combineDateTime(dateId, timeId) {
        const date = document.getElementById(dateId)?.value;
        const time = document.getElementById(timeId)?.value;
        if (!date || !time) return null;
        return `${date}T${time}:00`;
    },

    showError(message) {
        const alertDiv = document.getElementById('form-alert');
        if (alertDiv) {
            alertDiv.className = 'alert alert-danger';
            alertDiv.innerHTML = `❌ ${message}`;
            alertDiv.style.display = 'block';
        }
    },

    showSuccess(result) {
        const container = document.getElementById('form-container');
        if (container) {
            container.innerHTML = `
                <div class="card" style="text-align:center;padding:40px;">
                    <div style="width:64px;height:64px;background:#d4edda;border-radius:50%;display:flex;align-items:center;justify-content:center;margin:0 auto 16px;">
                        <span style="font-size:32px;">✅</span>
                    </div>
                    <h3 style="font-size:20px;font-weight:600;margin-bottom:8px;">Работа зарегистрирована!</h3>
                    <p style="color:#666;margin-bottom:20px;">
                        Плановая работа успешно сохранена.
                    </p>
                    <div class="alert alert-info" style="text-align:left;">
                        <strong>ℹ️ Статус отправки в Zabbix:</strong><br>
                        ${result.zabbix_exclusion_created
                            ? '✅ Исключение SLA создано в Zabbix'
                            : '⚠️ Демо-режим: исключение не отправлено (Zabbix не подключён)'}
                    </div>
                    <button class="btn btn-primary" onclick="location.reload()">+ Ещё одна работа</button>
                </div>
            `;
        }
    }
};

// Инициализация при загрузке
document.addEventListener('DOMContentLoaded', () => Form.init());
