// static/js/app.js — Главный JS файл, роутинг между страницами (SPA-подобно)

const App = {
    currentPage: 'dashboard',
    selectedService: '',

    init() {
        this.setupNavigation();
        this.showPage('dashboard');
        this.updateDate();
    },

    setupNavigation() {
        document.querySelectorAll('.sidebar-nav a').forEach(link => {
            link.addEventListener('click', (e) => {
                e.preventDefault();
                const page = link.dataset.page;
                this.showPage(page);
            });
        });
    },

    showPage(page) {
        this.currentPage = page;

        // Скрыть все страницы
        document.querySelectorAll('.page').forEach(p => {
            p.style.display = 'none';
        });

        // Показать нужную
        const targetPage = document.getElementById(`page-${page}`);
        if (targetPage) {
            targetPage.style.display = 'block';
        }

        // Обновить активный пункт меню
        document.querySelectorAll('.sidebar-nav a').forEach(link => {
            link.classList.toggle('active', link.dataset.page === page);
        });

        // Обновить заголовок
        const titles = {
            'dashboard': '📊 Панель управления',
            'graph': '🌐 Плановые работы из графа сервисов',
            'new-work': '➕ Регистрация плановой работы',
            'works-list': '📋 Список плановых работ',
            'calendar': '📅 Календарь плановых работ',
            'sla-report': '📈 SLA Отчёт',
            'settings': '⚙️ Настройки подключения',
        };
        document.getElementById('page-title').textContent = titles[page] || '';

        // Загрузить данные для страницы
        if (page === 'graph' && typeof Graph !== 'undefined') {
            Graph.init();
        }
        if (page === 'calendar' && typeof Calendar !== 'undefined') {
            Calendar.init();
        }
        if (page === 'works-list') {
            this.loadWorksList();
        }
    },

    updateDate() {
        const now = new Date();
        const options = { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' };
        document.getElementById('header-date').textContent = now.toLocaleDateString('ru-RU', options);
    },

    async loadWorksList() {
        try {
            const response = await fetch('/api/works');
            if (response.ok) {
                const works = await response.json();
                this.renderWorksList(works);
            }
        } catch (e) {
            console.log('Using demo data for works list');
        }
    },

    renderWorksList(works) {
        const tbody = document.getElementById('works-tbody');
        if (!tbody) return;

        tbody.innerHTML = works.map(work => `
            <tr>
                <td>${work.work_title}</td>
                <td>${work.service_name}</td>
                <td>${new Date(work.start_time).toLocaleDateString('ru-RU')}</td>
                <td><span class="badge badge-${work.status === 'planned' ? 'ok' : 'warning'}">${work.status}</span></td>
                <td>${work.zabbix_exclusion_created ? '✅' : '—'}</td>
            </tr>
        `).join('');
    },

    // Глобальное событие выбора сервиса из графа
    selectService(serviceName) {
        this.selectedService = serviceName;
        const input = document.getElementById('service-name-input');
        if (input) {
            input.value = serviceName;
        }
        // Перейти на страницу новой работы
        this.showPage('new-work');
    }
};

// Запуск при загрузке
document.addEventListener('DOMContentLoaded', () => App.init());
