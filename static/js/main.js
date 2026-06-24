document.addEventListener('DOMContentLoaded', () => {
    loadMonitors();
    
    // Modal Logic
    const modal = document.getElementById('addModal');
    document.getElementById('addMonitorBtn').onclick = () => modal.style.display = "block";
    document.querySelector('.close').onclick = () => modal.style.display = "none";
    window.onclick = (e) => { if(e.target == modal) modal.style.display = "none"; }
    
    // Form Submit
    document.getElementById('addMonitorForm').onsubmit = async (e) => {
        e.preventDefault();
        const data = {
            name: document.getElementById('mName').value,
            url: document.getElementById('mUrl').value,
            method: document.getElementById('mMethod').value,
            frequency: parseInt(document.getElementById('mFrequency').value),
            alert_email: document.getElementById('mEmail').value
        };
        
        const res = await fetch('/api/monitors', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(data)
        });
        
        if (res.ok) {
            modal.style.display = "none";
            document.getElementById('addMonitorForm').reset();
            loadMonitors();
        } else {
            alert('Error adding monitor');
        }
    };
    
    // Refresh monitors every 30 seconds
    setInterval(loadMonitors, 30000);
});

let lineChart = null;

async function loadMonitors() {
    try {
        const res = await fetch('/api/monitors');
        const monitors = await res.json();
        
        const grid = document.getElementById('monitorsList');
        grid.innerHTML = '';
        
        monitors.forEach(m => {
            const card = document.createElement('div');
            card.className = `monitor-card ${m.uptime_percent < 100 ? 'down' : ''}`;
            card.innerHTML = `
                <h3>${m.name}</h3>
                <div class="url">${m.url}</div>
                <div class="card-footer">
                    <div class="uptime" style="color: ${m.uptime_percent == 100 ? 'var(--success-color)' : 'var(--danger-color)'}">${m.uptime_percent}%</div>
                    <div style="font-size: 0.8rem; color: var(--text-secondary)">Every ${m.frequency}s</div>
                </div>
            `;
            card.onclick = () => loadMonitorDetails(m);
            grid.appendChild(card);
        });
    } catch(e) {
        console.error("Failed to load monitors", e);
    }
}

async function loadMonitorDetails(monitor) {
    document.getElementById('detailsSection').style.display = 'block';
    // Scroll to details
    document.getElementById('detailsSection').scrollIntoView({ behavior: 'smooth' });
    document.getElementById('detailName').textContent = `${monitor.name} Details`;
    
    try {
        // Load Stats
        const statsRes = await fetch(`/api/monitors/${monitor.id}/stats`);
        const stats = await statsRes.json();
        
        document.getElementById('statUptime').textContent = `${stats.uptime_24h}%`;
        document.getElementById('statAvgResp').textContent = `${stats.avg_response_time_ms} ms`;
        document.getElementById('statDowntime').textContent = stats.downtime_incidents;
        
        // Load Logs
        const logsRes = await fetch(`/api/monitors/${monitor.id}/logs`);
        const logs = await logsRes.json();
        
        const tbody = document.getElementById('logsBody');
        tbody.innerHTML = '';
        
        // Chart data
        const chartLabels = [];
        const chartData = [];
        
        logs.slice(0, 15).forEach(log => {
            const tr = document.createElement('tr');
            const dt = new Date(log.timestamp);
            tr.innerHTML = `
                <td>${dt.toLocaleTimeString()}</td>
                <td>${log.status_code || 'N/A'}</td>
                <td>${log.response_time ? log.response_time.toFixed(0) : 'N/A'}</td>
                <td><span class="badge ${log.is_success ? 'success' : 'danger'}">${log.is_success ? 'UP' : 'DOWN'}</span></td>
            `;
            tbody.appendChild(tr);
        });
        
        [...logs].reverse().forEach(log => {
            const dt = new Date(log.timestamp);
            chartLabels.push(dt.toLocaleTimeString());
            chartData.push(log.response_time || 0);
        });
        
        renderChart(chartLabels, chartData);
    } catch(e) {
        console.error("Error loading monitor details", e);
    }
}

function renderChart(labels, data) {
    const ctx = document.getElementById('responseTimeChart').getContext('2d');
    
    if (lineChart) {
        lineChart.destroy();
    }
    
    Chart.defaults.color = '#94a3b8';
    Chart.defaults.font.family = 'Inter';
    
    lineChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [{
                label: 'Response Time (ms)',
                data: data,
                borderColor: '#3b82f6',
                backgroundColor: 'rgba(59, 130, 246, 0.1)',
                borderWidth: 2,
                fill: true,
                tension: 0.4,
                pointRadius: 3,
                pointBackgroundColor: '#3b82f6'
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: false
                },
                tooltip: {
                    mode: 'index',
                    intersect: false,
                    backgroundColor: '#1e293b',
                    titleColor: '#f8fafc',
                    bodyColor: '#e2e8f0',
                    borderColor: '#334155',
                    borderWidth: 1
                }
            },
            scales: {
                y: { 
                    beginAtZero: true,
                    grid: {
                        color: '#334155',
                        drawBorder: false
                    }
                },
                x: {
                    grid: {
                        display: false,
                        drawBorder: false
                    },
                    ticks: {
                        maxTicksLimit: 10
                    }
                }
            },
            interaction: {
                mode: 'nearest',
                axis: 'x',
                intersect: false
            }
        }
    });
}
