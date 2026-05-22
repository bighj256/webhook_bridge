// ---------- DOM 元素绑定 ----------
const pHValueEl = document.getElementById('pHValue');
const co2ValueEl = document.getElementById('co2Value');
const moistureValueEl = document.getElementById('moistureValue');
const lightValueEl = document.getElementById('lightValue');
const airTempValueEl = document.getElementById('airTempValue');
const airHumValueEl = document.getElementById('airHumValue');

const pHFill = document.getElementById('pHFill');
const co2Fill = document.getElementById('co2Fill');
const moistureFill = document.getElementById('moistureFill');
const lightFill = document.getElementById('lightFill');
const tempFill = document.getElementById('tempFill');
const airHumFill = document.getElementById('airHumFill');

const pHStatus = document.getElementById('pHStatus');
const co2Status = document.getElementById('co2Status');
const moistureStatus = document.getElementById('moistureStatus');
const lightStatus = document.getElementById('lightStatus');
const tempStatus = document.getElementById('tempStatus');
const airHumStatus = document.getElementById('airHumStatus');

// ---------- 防刷屏状态记录 ----------
const previousStates = {
    ph: 'good', co2: 'good', soilMoisture: 'good',
    light: 'good', airTemp: 'good', airHum: 'good'
};

function showToast(title, message, type='alert') {
    const container = document.getElementById('toastContainer');
    if(!container) return;
    
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    
    const icon = type === 'alert' ? '🔴' : '🟡';
    
    toast.innerHTML = `
        <div class="toast-icon">${icon}</div>
        <div class="toast-content">
            <div class="toast-title">${title}</div>
            <div class="toast-desc">${message}</div>
        </div>
    `;
    
    container.appendChild(toast);
    
    setTimeout(() => {
        toast.classList.add('hiding');
        toast.addEventListener('animationend', () => {
            toast.remove();
        });
    }, 4000);
}

function getStatusDetails(value, metric) {
    let state = 'good';
    let text = '';
    
    switch(metric) {
        case 'airTemp':
            if(value < 10) { state = 'alert'; text = '低温 · 防寒冻'; }
            else if(value < 18) { state = 'warning'; text = '偏凉 · 注意保温'; }
            else if(value <= 28) { state = 'good'; text = '舒适 · 生长旺盛'; }
            else if(value <= 35) { state = 'warning'; text = '偏热 · 适当通风'; }
            else { state = 'alert'; text = '高温 · 防热害'; }
            break;
        case 'airHum':
            if(value < 30) { state = 'alert'; text = '干燥 · 增湿'; }
            else if(value < 45) { state = 'warning'; text = '偏干 · 注意'; }
            else if(value <= 75) { state = 'good'; text = '适宜 · 健康'; }
            else if(value <= 85) { state = 'warning'; text = '偏湿 · 注意排湿'; }
            else { state = 'alert'; text = '过湿 · 防病害'; }
            break;
        case 'soilMoisture':
            if(value < 30) { state = 'alert'; text = '干旱 · 立即灌溉'; }
            else if(value < 40) { state = 'warning'; text = '偏干 · 准备灌溉'; }
            else if(value <= 70) { state = 'good'; text = '适宜 · 墒情良好'; }
            else if(value <= 80) { state = 'warning'; text = '偏湿 · 注意'; }
            else { state = 'alert'; text = '过湿 · 排水防涝'; }
            break;
        case 'light':
            if(value < 2000) { state = 'alert'; text = '光照极低 · 补光'; }
            else if(value < 3000) { state = 'warning'; text = '光照不足 · 补光'; }
            else if(value <= 10000) { state = 'good'; text = '光强适宜 · 健康'; }
            else if(value <= 12000) { state = 'warning'; text = '偏强 · 注意'; }
            else { state = 'alert'; text = '光强过强 · 遮阴'; }
            break;
        case 'co2':
            if(value < 300) { state = 'alert'; text = '浓度极低 · 光合停滞'; }
            else if(value < 400) { state = 'warning'; text = '偏低 · 光合减弱'; }
            else if(value <= 800) { state = 'good'; text = '正常 · 生长佳'; }
            else if(value <= 1000) { state = 'warning'; text = '偏高 · 注意'; }
            else { state = 'alert'; text = '过高 · 注意通风'; }
            break;
        case 'ph':
            if(value < 5.5) { state = 'alert'; text = '极酸 · 需改良'; }
            else if(value < 6.0) { state = 'warning'; text = '偏酸性 · 注意调节'; }
            else if(value <= 7.5) { state = 'good'; text = '中性 · 适宜'; }
            else if(value <= 8.0) { state = 'warning'; text = '偏碱性 · 注意调节'; }
            else { state = 'alert'; text = '极碱 · 需改良'; }
            break;
    }
    return { state, text };
}

function updateMetricUI(metricName, value, valElem, fillElem, statusElem, percentValue, formatFn) {
    if (value === undefined || value === null) return;
    
    const details = getStatusDetails(value, metricName);
    const newState = details.state;
    
    valElem.innerText = formatFn ? formatFn(value) : value;
    
    valElem.classList.remove('text-warning', 'text-alert');
    fillElem.classList.remove('fill-warning', 'fill-alert');
    statusElem.classList.remove('status-good', 'status-warning', 'status-alert');
    
    if(newState === 'alert') {
        valElem.classList.add('text-alert');
        fillElem.classList.add('fill-alert');
        statusElem.classList.add('status-alert');
    } else if (newState === 'warning') {
        valElem.classList.add('text-warning');
        fillElem.classList.add('fill-warning');
        statusElem.classList.add('status-warning');
    } else {
        statusElem.classList.add('status-good');
    }
    
    fillElem.style.width = `${Math.min(100, Math.max(0, percentValue))}%`;
    statusElem.innerText = details.text;
    
    const oldState = previousStates[metricName];
    if (newState !== oldState) {
        const metricChinese = {
            'airTemp': '空气温度', 'airHum': '空气湿度', 'soilMoisture': '土壤湿度',
            'light': '光照强度', 'co2': 'CO2 浓度', 'ph': '土壤 pH 值'
        }[metricName] || metricName;

        if (newState === 'alert' && oldState !== 'alert') {
            showToast(`⚠️ ${metricChinese} 异常警报!`, `当前数值 ${value}，${details.text.split('·')[0].trim()}！`, 'alert');
            if(typeof addLog === 'function') addLog(`[传感器异常] ${metricChinese} 超出危险阈值! 当前数值: ${value}`, 'error');
        } else if (newState === 'warning' && oldState === 'good') {
            showToast(`⚠️ ${metricChinese} 状态警告`, `当前数值 ${value}，${details.text.split('·')[0].trim()}。`, 'warning');
            if(typeof addLog === 'function') addLog(`[传感器警告] ${metricChinese} 偏离适宜范围. 当前数值: ${value}`, 'warn');
        } else if (newState === 'good' && oldState !== 'good') {
            if(typeof addLog === 'function') addLog(`[状态恢复] ${metricChinese} 已恢复正常. 当前数值: ${value}`, 'info');
        }
        previousStates[metricName] = newState;
    }
}

// ---------- 辅助函数：更新 UI（基于真实数据）----------
function updateUI(data) {
    const { temp: airTemp, air_humi: airHum, soil_humi: soilMoisture, light, ph, co2 } = data;
    
    updateMetricUI('ph', ph, pHValueEl, pHFill, pHStatus, ph !== undefined ? (ph / 14) * 100 : 0, v => v.toFixed(1));
    updateMetricUI('co2', co2, co2ValueEl, co2Fill, co2Status, co2 !== undefined ? (co2 / 2000) * 100 : 0, v => Math.round(v));
    updateMetricUI('soilMoisture', soilMoisture, moistureValueEl, moistureFill, moistureStatus, soilMoisture !== undefined ? soilMoisture : 0, v => Math.round(v));
    updateMetricUI('light', light, lightValueEl, lightFill, lightStatus, light !== undefined ? (light / 15000) * 100 : 0, v => Math.round(v).toLocaleString());
    updateMetricUI('airTemp', airTemp, airTempValueEl, tempFill, tempStatus, airTemp !== undefined ? ((airTemp + 10) / 55) * 100 : 0, v => v.toFixed(1));
    updateMetricUI('airHum', airHum, airHumValueEl, airHumFill, airHumStatus, airHum !== undefined ? airHum : 0, v => Math.round(v));
}

// ---------- 统计数据 (Stats) ----------
async function fetchStats() {
    try {
        const response = await fetch('/api/stats');
        if (!response.ok) return;
        const data = await response.json();
        if (data.temp) {
            // pH
            document.getElementById('cardAvgPh').innerText = data.ph.avg;
            document.getElementById('cardMaxPh').innerText = data.ph.max;
            document.getElementById('cardMinPh').innerText = data.ph.min;
            // CO2
            document.getElementById('cardAvgCo2').innerText = data.co2.avg;
            document.getElementById('cardMaxCo2').innerText = data.co2.max;
            document.getElementById('cardMinCo2').innerText = data.co2.min;
            // Soil Moisture
            document.getElementById('cardAvgSoil').innerText = data.soil_humi.avg;
            document.getElementById('cardMaxSoil').innerText = data.soil_humi.max;
            document.getElementById('cardMinSoil').innerText = data.soil_humi.min;
            // Light
            document.getElementById('cardAvgLight').innerText = data.light.avg;
            document.getElementById('cardMaxLight').innerText = data.light.max;
            document.getElementById('cardMinLight').innerText = data.light.min;
            // Air Temp
            document.getElementById('cardAvgTemp').innerText = data.temp.avg;
            document.getElementById('cardMaxTemp').innerText = data.temp.max;
            document.getElementById('cardMinTemp').innerText = data.temp.min;
            // Air Hum
            document.getElementById('cardAvgHum').innerText = data.air_humi.avg;
            document.getElementById('cardMaxHum').innerText = data.air_humi.max;
            document.getElementById('cardMinHum').innerText = data.air_humi.min;
        }
    } catch (err) {
        console.error('获取统计数据失败:', err);
    }
}

// ---------- 从后端获取最新数据 ----------
async function fetchLatestAndUpdate() {
    try {
        const response = await fetch('/api/latest');
        if (!response.ok) {
            console.warn('暂无数据');
            return;
        }
        const data = await response.json();
        if (data.error) {
            console.warn(data.error);
            return;
        }
        updateUI(data);
    } catch (err) {
        console.error('获取最新数据失败:', err);
    }
}

// ---------- 手动刷新 ----------
function manualRefresh() {
    fetchLatestAndUpdate();
    fetchStats();
    const btn = document.getElementById('manualRefreshBtn');
    const orig = btn.innerHTML;
    btn.innerHTML = '✅ 已同步数据库';
    setTimeout(() => btn.innerHTML = orig, 800);
}

// ---------- 时钟 ----------
function updateClock() {
    const d = new Date();
    document.getElementById('liveClock').innerText = `${d.getFullYear()}/${String(d.getMonth()+1).padStart(2,'0')}/${String(d.getDate()).padStart(2,'0')} ${String(d.getHours()).padStart(2,'0')}:${String(d.getMinutes()).padStart(2,'0')}:${String(d.getSeconds()).padStart(2,'0')}`;
}

// ---------- 模态框图表功能 ----------
let currentChart = null;

const fieldMapping = {
    ph: 'ph',
    co2: 'co2',
    soilMoisture: 'soil_humi',
    light: 'light',
    airTemp: 'temp',
    airHum: 'air_humi'
};
const paramConfig = {
    ph: { name: '土壤 pH 值', unit: '', icon: '🧪', yLabel: 'pH值', color: '#4c8b3c' },
    co2: { name: 'CO₂ 浓度', unit: 'ppm', icon: '💨', yLabel: '浓度 (ppm)', color: '#607d8b' },
    soil_humi: { name: '土壤湿度', unit: '%', icon: '💧', yLabel: '相对湿度 (%)', color: '#2196f3' },
    light: { name: '光照强度', unit: 'lux', icon: '☀️', yLabel: '光照 (lux)', color: '#ff9800' },
    temp: { name: '空气温度', unit: '°C', icon: '🌡️', yLabel: '温度 (°C)', color: '#f44336' },
    air_humi: { name: '空气湿度', unit: '%', icon: '🌧️', yLabel: '相对湿度 (%)', color: '#03a9f4' }
};

function getSelectedMetrics() {
    const checkboxes = document.querySelectorAll('#metricCheckboxes input[type="checkbox"]:checked');
    return Array.from(checkboxes).map(cb => cb.value);
}

async function renderChartFromAPI() {
    const canvas = document.getElementById('modalChartCanvas');
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    
    const selectedFields = getSelectedMetrics();
    if (selectedFields.length === 0) {
        if (currentChart) currentChart.destroy();
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        return;
    }

    const timeUnit = document.getElementById('modalTimeUnit').value;
    const chartType = document.getElementById('modalChartType').value;
    
    let url = `/api/trend?params=${selectedFields.join(',')}`;
    
    if (timeUnit === 'custom') {
        const start = document.getElementById('customStartDate').value;
        const end = document.getElementById('customEndDate').value;
        if (!start) {
            alert("请选择开始时间");
            return;
        }
        url += `&start=${start}`;
        if (end) url += `&end=${end}`;
    } else {
        url += `&unit=${timeUnit}`;
    }

    try {
        const resp = await fetch(url);
        if (!resp.ok) throw new Error('trend api error');
        const data = await resp.json();

        if (currentChart) currentChart.destroy();

        const datasets = [];
        const yAxes = {};
        
        selectedFields.forEach((field, index) => {
            const cfg = paramConfig[field];
            const axisId = `y${index === 0 ? '' : '1'}`;
            
            datasets.push({
                label: `${cfg.name} (${cfg.unit})`,
                data: data.datasets[field],
                borderColor: cfg.color,
                backgroundColor: chartType === 'line' ? cfg.color + '33' : cfg.color,
                borderWidth: 2,
                tension: 0.3,
                fill: chartType === 'line',
                pointBackgroundColor: cfg.color,
                yAxisID: axisId
            });

            yAxes[axisId] = {
                type: 'linear',
                display: true,
                position: index === 0 ? 'left' : 'right',
                title: { display: true, text: cfg.yLabel },
                grid: { drawOnChartArea: index === 0 } // 只画一次网格
            };
        });

        currentChart = new Chart(ctx, {
            type: chartType,
            data: {
                labels: data.labels,
                datasets: datasets
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: { legend: { position: 'top' } },
                scales: yAxes,
                animation: { duration: 0 } // SSE更新时无动画更顺滑
            }
        });
    } catch (err) {
        console.error('加载趋势数据失败:', err);
        if (currentChart) currentChart.destroy();
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        ctx.font = '16px sans-serif';
        ctx.fillStyle = 'red';
        ctx.fillText('无法加载历史数据', 20, 50);
    }
}

async function openModal(dataType) {
    const dbField = fieldMapping[dataType];
    
    // 初始化 Checkbox
    const checkboxes = document.querySelectorAll('#metricCheckboxes input[type="checkbox"]');
    checkboxes.forEach(cb => {
        cb.checked = (cb.value === dbField);
        cb.disabled = false;
    });

    const cfg = paramConfig[dbField];
    document.getElementById('modalIcon').innerText = cfg.icon || '📊';
    document.getElementById('modalTitle').innerHTML = `历史趋势`;

    document.getElementById('chartModal').style.display = 'flex';
    await renderChartFromAPI();
}

function closeModal() {
    document.getElementById('chartModal').style.display = 'none';
    if (currentChart) currentChart.destroy();
}

function handleCheckboxLimit() {
    const checkboxes = document.querySelectorAll('#metricCheckboxes input[type="checkbox"]');
    const checkedCount = document.querySelectorAll('#metricCheckboxes input[type="checkbox"]:checked').length;
    checkboxes.forEach(cb => {
        if (!cb.checked && checkedCount >= 2) cb.disabled = true;
        else cb.disabled = false;
    });
}

function exportCsv() {
    const selectedFields = getSelectedMetrics();
    if (selectedFields.length === 0) return alert("请先选择指标");
    
    const timeUnit = document.getElementById('modalTimeUnit').value;
    let url = `/api/export?params=${selectedFields.join(',')}`;
    
    if (timeUnit === 'custom') {
        const start = document.getElementById('customStartDate').value;
        const end = document.getElementById('customEndDate').value;
        if (!start) return alert("请选择开始时间");
        url += `&start=${start}`;
        if (end) url += `&end=${end}`;
    } else {
        const now = new Date();
        let start = new Date();
        if (timeUnit === 'hour') start.setHours(start.getHours() - 24);
        else if (timeUnit === 'day') start.setDate(start.getDate() - 7);
        else if (timeUnit === 'week') start.setDate(start.getDate() - 56);
        else if (timeUnit === 'month') start.setFullYear(start.getFullYear() - 1);
        else if (timeUnit === 'year') start.setFullYear(start.getFullYear() - 5);
        
        // 转换为本地时区的格式 (YYYY-MM-DDTHH:mm:ss)
        const formatLocal = (d) => new Date(d.getTime() - d.getTimezoneOffset() * 60000).toISOString().split('.')[0];
        url += `&start=${formatLocal(start)}&end=${formatLocal(now)}`;
    }
    
    window.open(url, '_blank');
}

function exportAllCsv() {
    const allFields = ['ph', 'co2', 'soil_humi', 'light', 'temp', 'air_humi'];
    const url = `/api/export?params=${allFields.join(',')}`;
    window.open(url, '_blank');
}

// ---------- 注册事件与启动 ----------
document.addEventListener('DOMContentLoaded', () => {
    fetchLatestAndUpdate();
    fetchStats();
    
    // 建立 SSE 长连接，监听服务器推送
    const evtSource = new EventSource('/api/stream');
    
    evtSource.onopen = function() {
        if(typeof addLog === 'function') addLog('已成功连接到服务器实时数据流 (SSE).', 'info');
    };
    
    evtSource.onerror = function() {
        if(typeof addLog === 'function') addLog('网络连接已断开，正在尝试重新连接...', 'error');
    };

    evtSource.onmessage = function(event) {
        try {
            const data = JSON.parse(event.data);
            if(typeof addLog === 'function') addLog(`收到传感器数据: 温度 ${data.temp}°C, 湿度 ${data.air_humi}%, 光照 ${data.light}lx...`, 'info');
            updateUI(data);
            
            // 收到最新传感数据的同时，触发一次统计数据的刷新
            fetchStats();
            
            // 如果图表正在显示，且处于“实时”模式，流式更新图表
            const timeUnit = document.getElementById('modalTimeUnit').value;
            if (document.getElementById('chartModal').style.display === 'flex' && currentChart && timeUnit === 'live') {
                const nowStr = new Date().toLocaleTimeString([], {hour: '2-digit', minute:'2-digit', second:'2-digit'});
                currentChart.data.labels.push(nowStr);
                
                const selectedFields = getSelectedMetrics();
                selectedFields.forEach((field, index) => {
                    const val = data[field];
                    if(currentChart.data.datasets[index]) {
                        currentChart.data.datasets[index].data.push(val);
                    }
                });
                
                if (currentChart.data.labels.length > 60) {
                    currentChart.data.labels.shift();
                    currentChart.data.datasets.forEach(dataset => dataset.data.shift());
                }
                
                currentChart.update();
            }
        } catch(e) {
            console.error("解析 SSE 数据失败", e);
        }
    };
    evtSource.onerror = function(err) {
        console.error("SSE 连接出错，浏览器会自动尝试重连", err);
    };

    setInterval(updateClock, 1000);
    document.getElementById('manualRefreshBtn').addEventListener('click', manualRefresh);
    document.getElementById('exportAllCsvBtn').addEventListener('click', exportAllCsv);
    updateClock();

    // 卡片点击
    document.querySelectorAll('.card').forEach(card => {
        card.addEventListener('click', (e) => {
            const type = card.getAttribute('data-type');
            if (type) openModal(type);
        });
    });

    // 模态框关闭
    document.getElementById('closeModalBtn').addEventListener('click', closeModal);
    window.addEventListener('click', (e) => {
        const modal = document.getElementById('chartModal');
        if (e.target === modal) closeModal();
    });

    // UI 控制项改变
    document.getElementById('modalTimeUnit').addEventListener('change', (e) => {
        document.getElementById('customDateGroup').style.display = e.target.value === 'custom' ? 'flex' : 'none';
        if(e.target.value !== 'custom') renderChartFromAPI();
    });
    
    document.getElementById('modalChartType').addEventListener('change', renderChartFromAPI);
    document.getElementById('applyCustomDateBtn').addEventListener('click', renderChartFromAPI);
    document.getElementById('exportCsvBtn').addEventListener('click', exportCsv);
    
    document.querySelectorAll('#metricCheckboxes input[type="checkbox"]').forEach(cb => {
        cb.addEventListener('change', () => {
            handleCheckboxLimit();
            renderChartFromAPI();
        });
    });
});
// ---------- 系统日志面板 ----------
let systemLogs = [];

function addLog(message, level='info') {
    const timeStr = new Date().toLocaleTimeString('zh-CN', {hour12: false});
    const logObj = { time: timeStr, message, level };
    systemLogs.push(logObj);
    
    // 最多保留 1000 条
    if (systemLogs.length > 1000) systemLogs.shift();
    
    renderLog(logObj);
}

function renderLog(log) {
    const filter = document.getElementById('logLevelFilter');
    if (filter && filter.value !== 'all' && filter.value !== log.level) return;
    
    const terminal = document.getElementById('logTerminal');
    if (!terminal) return;
    
    const entry = document.createElement('div');
    entry.className = `log-entry log-${log.level}`;
    
    let prefix = '[INFO]  🟢';
    if (log.level === 'warn') prefix = '[WARN]  🟡';
    if (log.level === 'error') prefix = '[ERROR] 🔴';
    
    entry.innerHTML = `<span class="log-time">[${log.time}]</span> <span class="log-msg">${prefix} ${log.message}</span>`;
    terminal.appendChild(entry);
    
    // 自动滚动到底部
    terminal.scrollTop = terminal.scrollHeight;
}

function clearLogs() {
    systemLogs = [];
    const terminal = document.getElementById('logTerminal');
    if (terminal) terminal.innerHTML = '';
    addLog('日志已清空', 'info');
}

document.getElementById('logLevelFilter')?.addEventListener('change', () => {
    const terminal = document.getElementById('logTerminal');
    if (terminal) terminal.innerHTML = '';
    systemLogs.forEach(renderLog);
});

function exportLogs() {
    if (systemLogs.length === 0) return alert('当前没有日志可导出');
    let content = "=== Intelligent Farm System Logs ===\n";
    content += `导出时间: ${new Date().toLocaleString('zh-CN')}\n\n`;
    
    systemLogs.forEach(log => {
        let prefix = '[INFO] ';
        if (log.level === 'warn') prefix = '[WARN] ';
        if (log.level === 'error') prefix = '[ERROR]';
        content += `[${log.time}] ${prefix} ${log.message}\n`;
    });
    
    const blob = new Blob([content], { type: 'text/plain;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `farm_system_log_${new Date().getTime()}.txt`;
    a.click();
    URL.revokeObjectURL(url);
}
