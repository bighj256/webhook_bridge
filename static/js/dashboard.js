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

    pHValueEl.innerText = ph.toFixed(1);
    co2ValueEl.innerText = Math.round(co2);
    moistureValueEl.innerText = Math.round(soilMoisture);
    lightValueEl.innerText = Math.round(light).toLocaleString();
    airTempValueEl.innerText = airTemp.toFixed(1);
    airHumValueEl.innerText = Math.round(airHum);

    pHFill.style.width = `${Math.min(100, (ph / 14) * 100)}%`;
    co2Fill.style.width = `${Math.min(100, (co2 / 2000) * 100)}%`;
    moistureFill.style.width = `${Math.min(100, Math.max(0, soilMoisture))}%`;
    lightFill.style.width = `${Math.min(100, (light / 15000) * 100)}%`;
    let tempPercent = ((airTemp + 10) / 55) * 100;
    tempPercent = Math.min(100, Math.max(0, tempPercent));
    tempFill.style.width = `${tempPercent}%`;
    airHumFill.style.width = `${Math.min(100, Math.max(0, airHum))}%`;

    // pH 状态
    let pHText = ph < 6.0 ? '偏酸性' : (ph <= 7.5 ? '中性 · 适宜' : '偏碱性');
    pHStatus.innerText = pHText + (ph < 6.0 ? ' · 注意调节' : (ph > 7.5 ? ' · 需改良' : ''));
    pHStatus.className = `status-badge ${ph < 6.0 || ph > 7.5 ? 'status-warning' : 'status-good'}`;

    // CO₂
    let co2Text = co2 < 400 ? '偏低 · 光合减弱' : (co2 <= 800 ? '正常 · 生长佳' : '偏高 · 注意通风');
    co2Status.innerText = co2Text;
    co2Status.className = `status-badge ${co2 < 400 ? 'status-warning' : (co2 > 800 ? 'status-alert' : 'status-good')}`;

    // 土壤湿度
    let moistText = soilMoisture < 30 ? '干旱 · 立即灌溉' : (soilMoisture <= 70 ? '适宜 · 墒情良好' : '过湿 · 注意排水');
    moistureStatus.innerText = moistText;
    moistureStatus.className = `status-badge ${soilMoisture < 30 ? 'status-alert' : (soilMoisture > 70 ? 'status-warning' : 'status-good')}`;

    // 光照
    let lightText = light < 2000 ? '光照不足 · 补光' : (light <= 10000 ? '光强适宜 · 健康' : '光强过强 · 遮阴');
    lightStatus.innerText = lightText;
    lightStatus.className = `status-badge ${light < 2000 ? 'status-alert' : (light > 10000 ? 'status-warning' : 'status-good')}`;

    // 温度
    let tempText = airTemp < 10 ? '低温 · 防寒冻' : (airTemp < 18 ? '偏凉 · 注意保温' : (airTemp <= 28 ? '舒适 · 生长旺盛' : (airTemp <= 35 ? '偏热 · 适当通风' : '高温 · 防热害')));
    tempStatus.innerText = tempText;
    tempStatus.className = `status-badge ${airTemp < 10 || airTemp > 35 ? 'status-alert' : (airTemp < 18 || airTemp > 28 ? 'status-warning' : 'status-good')}`;

    // 空气湿度
    let humText = airHum < 30 ? '干燥 · 增湿' : (airHum < 45 ? '偏干 · 注意' : (airHum <= 75 ? '适宜 · 健康' : '过高 · 防病害'));
    airHumStatus.innerText = humText;
    airHumStatus.className = `status-badge ${airHum < 30 ? 'status-alert' : (airHum > 75 ? 'status-warning' : (airHum < 45 ? 'status-warning' : 'status-good'))}`;
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

// ---------- 模态框图表功能（真实数据）----------
let currentChart = null;
let currentDataType = 'ph';      // 前端卡片类型
let currentDbField = 'ph';       // 数据库字段名

const fieldMapping = {
    ph: 'ph',
    co2: 'co2',
    soilMoisture: 'soil_humi',
    light: 'light',
    airTemp: 'temp',
    airHum: 'air_humi'
};
const paramConfig = {
    ph: { name: '土壤 pH 值', unit: '', icon: '🧪', yLabel: 'pH值' },
    co2: { name: 'CO₂ 浓度', unit: 'ppm', icon: '💨', yLabel: '浓度 (ppm)' },
    soilMoisture: { name: '土壤湿度', unit: '%', icon: '💧', yLabel: '相对湿度 (%)' },
    light: { name: '光照强度', unit: 'lux', icon: '☀️', yLabel: '光照 (lux)' },
    airTemp: { name: '空气温度', unit: '°C', icon: '🌡️', yLabel: '温度 (°C)' },
    airHum: { name: '空气湿度', unit: '%', icon: '🌧️', yLabel: '相对湿度 (%)' }
};

async function renderChartFromAPI(dbField, timeUnit, chartType) {
    const canvas = document.getElementById('modalChartCanvas');
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (currentChart) currentChart.destroy();

    try {
        const url = `/api/trend/${dbField}?unit=${timeUnit}`;
        const resp = await fetch(url);
        if (!resp.ok) throw new Error('trend api error');
        const { labels, values } = await resp.json();

        const cfg = Object.values(paramConfig).find((_, idx) => Object.keys(paramConfig)[idx] === currentDataType) || paramConfig.ph;
        currentChart = new Chart(ctx, {
            type: chartType,
            data: {
                labels: labels,
                datasets: [{
                    label: `${cfg.name} (${cfg.unit})`,
                    data: values,
                    borderColor: '#4c8b3c',
                    backgroundColor: chartType === 'line' ? 'rgba(76, 139, 60, 0.1)' : '#5fad41',
                    borderWidth: 2,
                    tension: 0.3,
                    fill: chartType === 'line',
                    pointBackgroundColor: '#2d5720'
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: true,
                plugins: { legend: { position: 'top' } },
                scales: { y: { title: { display: true, text: cfg.yLabel } } }
            }
        });
    } catch (err) {
        console.error('加载趋势数据失败:', err);
        // 显示错误信息在 canvas 上
        if (currentChart) currentChart.destroy();
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        ctx.font = '16px sans-serif';
        ctx.fillStyle = 'red';
        ctx.fillText('无法加载历史数据', 20, 50);
    }
}

async function openModal(dataType) {
    currentDataType = dataType;
    const dbField = fieldMapping[dataType];
    currentDbField = dbField;
    const cfg = paramConfig[dataType];
    document.getElementById('modalIcon').innerText = cfg.icon;
    document.getElementById('modalTitle').innerHTML = `${cfg.name} 历史趋势`;

    const timeUnit = document.getElementById('modalTimeUnit').value;
    const chartType = document.getElementById('modalChartType').value;
    await renderChartFromAPI(dbField, timeUnit, chartType);
    document.getElementById('chartModal').style.display = 'flex';
}

function closeModal() {
    document.getElementById('chartModal').style.display = 'none';
    if (currentChart) currentChart.destroy();
}

// 单位/图表变化时重新加载
async function onModalControlChange() {
    if (document.getElementById('chartModal').style.display !== 'flex') return;
    const timeUnit = document.getElementById('modalTimeUnit').value;
    const chartType = document.getElementById('modalChartType').value;
    await renderChartFromAPI(currentDbField, timeUnit, chartType);
}

// ---------- 注册事件与启动 ----------
document.addEventListener('DOMContentLoaded', () => {
    fetchLatestAndUpdate();
    setInterval(fetchLatestAndUpdate, 5000);
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

    document.getElementById('modalTimeUnit').addEventListener('change', onModalControlChange);
    document.getElementById('modalChartType').addEventListener('change', onModalControlChange);
});
