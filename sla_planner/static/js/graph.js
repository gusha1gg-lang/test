// static/js/graph.js — Интерактивный граф сервисов (vis-network)

const Graph = {
    network: null,
    selectedNode: null,

    async init() {
        const container = document.getElementById('graph-container');
        if (!container) return;

        try {
            // Загрузка данных дерева сервисов
            const response = await fetch('/api/services_tree');
            let data;
            if (response.ok) {
                data = await response.json();
            } else {
                data = this.getDemoData();
            }
            this.render(container, data);
        } catch (e) {
            console.log('Zabbix unavailable, using demo data');
            data = this.getDemoData();
            this.render(container, data);
        }
    },

    getDemoData() {
        return {
            nodes: [
                { id: "1", name: "IT Инфраструктура", status: "ok", parent_id: null },
                { id: "2", name: "Почтовый сервер", status: "ok", parent_id: "1" },
                { id: "3", name: "CRM Система", status: "ok", parent_id: "1" },
                { id: "4", name: "БД PostgreSQL", status: "ok", parent_id: "3" },
                { id: "5", name: "ERP Система", status: "warning", parent_id: "1" },
                { id: "6", name: "БД Oracle", status: "ok", parent_id: "5" },
                { id: "7", name: "1С Бухгалтерия", status: "problem", parent_id: "5" },
                { id: "8", name: "Портал клиентов", status: "ok", parent_id: "1" },
                { id: "9", name: "Веб-сервер Nginx", status: "ok", parent_id: "8" },
                { id: "10", name: "Файловый сервер", status: "ok", parent_id: "1" },
            ],
            edges: [
                { from: "1", to: "2" }, { from: "1", to: "3" }, { from: "1", to: "5" },
                { from: "1", to: "8" }, { from: "1", to: "10" }, { from: "3", to: "4" },
                { from: "5", to: "6" }, { from: "5", to: "7" }, { from: "8", to: "9" },
            ]
        };
    },

    render(container, data) {
        const statusColors = {
            ok: '#28a745',
            warning: '#ffc107',
            problem: '#dc3545',
        };

        // Определение уровня узла
        const getLevel = (nodeId) => {
            let level = 0;
            let current = data.nodes.find(n => n.id === nodeId);
            while (current && current.parent_id) {
                level++;
                current = data.nodes.find(n => n.id === current.parent_id);
            }
            return level;
        };

        // Подготовка узлов
        const nodes = new vis.DataSet(data.nodes.map(node => ({
            id: node.id,
            label: node.name,
            color: {
                background: statusColors[node.status] || '#6c757d',
                border: statusColors[node.status] || '#6c757d',
                highlight: {
                    background: statusColors[node.status] || '#6c757d',
                    border: '#0d6efd',
                },
            },
            font: { color: '#ffffff', size: 13, face: 'system-ui' },
            shape: 'box',
            shapeProperties: { borderRadius: 8 },
            borderWidth: 2,
            borderWidthSelected: 4,
            margin: 12,
            level: getLevel(node.id),
        })));

        // Подготовка рёбер
        const edges = new vis.DataSet(data.edges.map((edge, i) => ({
            id: `e${i}`,
            from: edge.from,
            to: edge.to,
            arrows: { to: { enabled: true, scaleFactor: 0.8 } },
            color: { color: '#adb5bd', highlight: '#0d6efd' },
            width: 2,
            smooth: { type: 'cubicBezier', forceDirection: 'vertical', roundness: 0.4 },
        })));

        const options = {
            layout: {
                hierarchical: {
                    enabled: true,
                    direction: 'UD',
                    sortMethod: 'directed',
                    levelSeparation: 100,
                    nodeSpacing: 160,
                    treeSpacing: 200,
                },
            },
            physics: { enabled: false },
            interaction: { hover: true, zoomView: true, dragView: true },
        };

        // Уничтожить предыдущий граф если есть
        if (this.network) {
            this.network.destroy();
        }

        this.network = new vis.Network(container, { nodes, edges }, options);

        // Обработка клика по узлу
        this.network.on('click', (params) => {
            if (params.nodes.length > 0) {
                const nodeId = params.nodes[0];
                const node = data.nodes.find(n => n.id === nodeId);
                if (node) {
                    this.selectedNode = node;
                    this.network.selectNodes([nodeId]);

                    // Заполнить поле имени сервиса
                    const input = document.getElementById('service-name-input');
                    if (input) input.value = node.name;

                    // Обновить информацию о выбранном сервисе
                    const info = document.getElementById('selected-service-info');
                    if (info) {
                        info.innerHTML = `
                            <div style="display:flex;align-items:center;gap:8px;padding:8px;background:#f8f9fa;border-radius:8px;">
                                <span style="width:12px;height:12px;border-radius:50%;background:${statusColors[node.status]}"></span>
                                <span style="font-size:13px;color:#555;">Статус: <strong>${node.status.toUpperCase()}</strong></span>
                            </div>
                        `;
                    }
                }
            }
        });
    }
};
