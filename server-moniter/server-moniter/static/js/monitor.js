// 监控系统功能
console.log('监控系统JS加载完成');

class SimpleMonitor {
    constructor() {
        this.init();
    }

    init() {
        console.log('初始化监控系统');
        this.loadData();
        // 每5秒自动刷新
        setInterval(() => this.loadData(), 5000);
    }

    async loadData() {
        try {
            this.showLoading();
            const response = await fetch('/api/monitor/data');
            const data = await response.json();
            this.updateDisplay(data);
        } catch (error) {
            console.error('加载数据失败:', error);
            this.showError('加载失败: ' + error.message);
        }
    }

    showLoading() {
        const tbody = document.getElementById('hostTableBody');
        if (tbody) {
            tbody.innerHTML = '<tr><td colspan="5" class="loading">加载中...</td></tr>';
        }
    }

    showError(message) {
        const tbody = document.getElementById('hostTableBody');
        if (tbody) {
            tbody.innerHTML = '<tr><td colspan="5" class="text-danger">' + message + '</td></tr>';
        }
    }

    updateDisplay(hosts) {
        const tbody = document.getElementById('hostTableBody');
        if (!tbody) return;

        if (!hosts || hosts.length === 0) {
            tbody.innerHTML = '<tr><td colspan="5" class="text-muted text-center">暂无数据</td></tr>';
            return;
        }

        tbody.innerHTML = hosts.map(host => `
            <tr>
                <td>${host.ip_address}</td>
                <td><span class="badge ${host.status === 'online' ? 'bg-success' : 'bg-danger'}">${host.status_text}</span></td>
                <td>${host.monitor?.cpu_usage || 0}%</td>
                <td>${host.monitor?.memory_usage || 0}%</td>
                <td>${host.monitor?.timestamp || '--'}</td>
            </tr>
        `).join('');
    }
}

// 页面加载后初始化
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => new SimpleMonitor());
} else {
    new SimpleMonitor();
}
