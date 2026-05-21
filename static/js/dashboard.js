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

// ---------- 辅助函数：更新 UI（基于真实数据）----------
function updateUI(data) {
    const ph = data.ph;
    const co2 = data.co2;
    const soilMoisture = data.soil_humi;
    const light = data.light;
    const airTemp = data.temp;
    const airHum = data.air_humi;

    if(ph !== undefined) pHValueEl.innerText = ph.toFixed(1);
    if(co2 !== undefined) co2ValueEl.innerText = Math.round(co2);
    if(soilMoisture !== undefined) moistureValueEl.innerText = Math.round(soilMoisture);
    if(light !== undefined) lightValueEl.innerText = Math.round(light).toLocaleString();
    if(airTemp !== undefined) airTempValueEl.innerText = airTemp.toFixed(1);
    if(airHum !== undefined) airHumValueEl.innerText = Math.round(airHum);

    if(ph !== undefined) {
        pHFill.style.width = `${Math.min(100, (ph / 14) * 100)}%`;
        let pHText = ph < 6.0 ? '偏酸性' : (ph <= 7.5 ? '中性 · 适宜' : '偏碱性');
        pHStatus.innerText = pHText + (ph < 6.0 ? ' · 注意调节' : (ph > 7.5 ? ' · 需改良' : ''));
        pHStatus.className = `status-badge ${ph < 6.0 || ph > 7.5 ? 'status-warning' : 'status-good'}`;
    }

    if(co2 !== undefined) {
        co2Fill.style.width = `${Math.min(100, (co2 / 2000) * 100)}%`;
        let co2Text = co2 < 400 ? '偏低 · 光合减弱' : (co2 <= 800 ? '正常 · 生长佳' : '偏高 · 注意通风');
        co2Status.innerText = co2Text;
        co2Status.className = `status-badge ${co2 < 400 ? 'status-warning' : (co2 > 800 ? 'status-alert' : 'status-good')}`;
    }

    if(soilMoisture !== undefined) {
        moistureFill.style.width = `${Math.min(100, Math.max(0, soilMoisture))}%`;
        let moistText = soilMoisture < 30 ? '干旱 · 立即灌溉' : (soilMoisture <= 70 ? '适宜 · 墒情良好' : '过湿 · 注意排水');
        moistureStatus.innerText = moistText;
        moistureStatus.className = `status-badge ${soilMoisture < 30 ? 'status-alert' : (soilMoisture > 70 ? 'status-warning' : 'status-good')}`;
    }

    if(light !== undefined) {
        lightFill.style.width = `${Math.min(100, (light / 15000) * 100)}%`;
        let lightText = light < 2000 ? '光照不足 · 补光' : (light <= 10000 ? '光强适宜 · 健康' : '光强过强 · 遮阴');
        lightStatus.innerText = lightText;
        lightStatus.className = `status-badge ${light < 2000 ? 'status-alert' : (light > 10000 ? 'status-warning' : 'status-good')}`;
    }

    if(airTemp !== undefined) {
        let tempPercent = ((airTemp + 10) / 55) * 100;
        tempFill.style.width = `${Math.min(100, Math.max(0, tempPercent))}%`;
        let tempText = airTemp < 10 ? '低温 · 防寒冻' : (airTemp < 18 ? '偏凉 · 注意保温' : (airTemp <= 28 ? '舒适 · 生长旺盛' : (airTemp <= 35 ? '偏热 · 适当通风' : '高温 · 防热害')));
        tempStatus.innerText = tempText;
        tempStatus.className = `status-badge ${airTemp < 10 || airTemp > 35 ? 'status-alert' : (airTemp < 18 || airTemp > 28 ? 'status-warning' : 'status-good')}`;
    }

    if(airHum !== undefined) {
        airHumFill.style.width = `${Math.min(100, Math.max(0, airHum))}%`;
        let humText = airHum < 30 ? '干燥 · 增湿' : (airHum < 45 ? '偏干 · 注意' : (airHum <= 75 ? '适宜 · 健康' : '过高 · 防病害'));
        airHumStatus.innerText = humText;
        airHumStatus.className = `status-badge ${airHum < 30 ? 'status-alert' : (airHum > 75 ? 'status-warning' : (airHum < 45 ? 'status-warning' : 'status-good'))}`;
    }
}

// ---------- 统计数据 (Stats) ----------
async function fetchStats() {
    try {
        const response = await fetch('/api/stats');
        if (!response.ok) return;
        const data = await response.json();
        if (data.temp) {
            document.getElementById('statAvgTemp').innerText = `${data.temp.avg}°C`;
            document.getElementById('statMaxTemp').innerText = `${data.temp.max}°C`;
            document.getElementById('statAvgHum').innerText = `${data.air_humi.avg}%`;
            document.getElementById('statMaxCo2').innerText = `${data.co2.max}ppm`;
            document.getElementById('statMinPh').innerText = `${data.ph.min}`;
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
        url += `&start=${new Date(start).toISOString()}`;
        if (end) url += `&end=${new Date(end).toISOString()}`;
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
        url += `&start=${new Date(start).toISOString()}`;
        if (end) url += `&end=${new Date(end).toISOString()}`;
    } else {
        const now = new Date();
        let start = new Date();
        if (timeUnit === 'hour') start.setHours(start.getHours() - 24);
        else if (timeUnit === 'day') start.setDate(start.getDate() - 7);
        else if (timeUnit === 'week') start.setDate(start.getDate() - 56);
        else if (timeUnit === 'month') start.setFullYear(start.getFullYear() - 1);
        else if (timeUnit === 'year') start.setFullYear(start.getFullYear() - 5);
        url += `&start=${start.toISOString()}&end=${now.toISOString()}`;
    }
    
    window.open(url, '_blank');
}

// ---------- 注册事件与启动 ----------
document.addEventListener('DOMContentLoaded', () => {
    fetchLatestAndUpdate();
    fetchStats();
    
    // 建立 SSE 长连接，监听服务器推送
    const evtSource = new EventSource('/api/stream');
    evtSource.onmessage = function(event) {
        try {
            const data = JSON.parse(event.data);
            updateUI(data);
            
            // 如果图表正在显示，流式更新图表
            if (document.getElementById('chartModal').style.display === 'flex' && currentChart) {
                const nowStr = new Date().toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'});
                currentChart.data.labels.push(nowStr);
                
                const selectedFields = getSelectedMetrics();
                selectedFields.forEach((field, index) => {
                    const val = data[field];
                    currentChart.data.datasets[index].data.push(val);
                });
                
                if (currentChart.data.labels.length > 100) {
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
