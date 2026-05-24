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

// ---------- 侧边栏与页眉额外 DOM 绑定 ----------
const systemStatusDot = document.getElementById('systemStatusDot');
const systemStatusText = document.getElementById('systemStatusText');
const uploadStatusVal = document.getElementById('uploadStatusVal');
const glanceErrorCount = document.getElementById('glanceErrorCount');

// ---------- 状态标记防高频刷屏 ----------
const previousStates = {
    ph: 'good', co2: 'good', soilMoisture: 'good',
    light: 'good', airTemp: 'good', airHum: 'good'
};

// ---------- 传感器数值跳跃脉冲微动效 ----------
function triggerHeartbeatPulse(element) {
    if (!element) return;
    element.classList.remove('pulse-active');
    void element.offsetWidth; // 触发强制重绘
    element.classList.add('pulse-active');
}

// ---------- 漂亮的非阻塞 Toast 消息框 ----------
function showToast(title, message, type = 'alert') {
    const container = document.getElementById('toastContainer');
    if (!container) return;

    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;

    let icon = '🟢';
    if (type === 'alert') icon = '🔴';
    else if (type === 'warning') icon = '🟡';

    toast.innerHTML = `
        <div class="toast-icon" aria-hidden="true">${icon}</div>
        <div class="toast-content">
            <div class="toast-title">${title}</div>
            <div class="toast-desc">${message}</div>
        </div>
    `;

    container.appendChild(toast);

    // 平滑移除
    setTimeout(() => {
        toast.classList.add('hiding');
        toast.addEventListener('animationend', () => {
            toast.remove();
        });
    }, 4500);
}

// ---------- 分析传感器区间状态 ----------
function getStatusDetails(value, metric) {
    let state = 'good';
    let text = '';

    switch (metric) {
        case 'airTemp':
            if (value < 10) { state = 'alert'; text = '低温 · 防寒冻'; }
            else if (value < 18) { state = 'warning'; text = '偏凉 · 注意保温'; }
            else if (value <= 28) { state = 'good'; text = '舒适 · 生长旺盛'; }
            else if (value <= 35) { state = 'warning'; text = '偏热 · 适当通风'; }
            else { state = 'alert'; text = '高温 · 防热害'; }
            break;
        case 'airHum':
            if (value < 30) { state = 'alert'; text = '干燥 · 增湿'; }
            else if (value < 45) { state = 'warning'; text = '偏干 · 注意'; }
            else if (value <= 75) { state = 'good'; text = '适宜 · 健康'; }
            else if (value <= 85) { state = 'warning'; text = '偏湿 · 注意排湿'; }
            else { state = 'alert'; text = '过湿 · 防病害'; }
            break;
        case 'soilMoisture':
            if (value < 30) { state = 'alert'; text = '干旱 · 立即灌溉'; }
            else if (value < 40) { state = 'warning'; text = '偏干 · 准备灌溉'; }
            else if (value <= 70) { state = 'good'; text = '适宜 · 墒情良好'; }
            else if (value <= 80) { state = 'warning'; text = '偏湿 · 注意'; }
            else { state = 'alert'; text = '过湿 · 排水防涝'; }
            break;
        case 'light':
            if (value < 2000) { state = 'alert'; text = '光照极低 · 补光'; }
            else if (value < 3000) { state = 'warning'; text = '光照不足 · 补光'; }
            else if (value <= 10000) { state = 'good'; text = '光强适宜 · 健康'; }
            else if (value <= 12000) { state = 'warning'; text = '偏强 · 注意'; }
            else { state = 'alert'; text = '光强过强 · 遮阴'; }
            break;
        case 'co2':
            if (value < 300) { state = 'alert'; text = '浓度极低 · 光合停滞'; }
            else if (value < 400) { state = 'warning'; text = '偏低 · 光合减弱'; }
            else if (value <= 800) { state = 'good'; text = '正常 · 生长佳'; }
            else if (value <= 1000) { state = 'warning'; text = '偏高 · 注意'; }
            else { state = 'alert'; text = '过高 · 注意通风'; }
            break;
        case 'ph':
            if (value < 5.5) { state = 'alert'; text = '极酸 · 需改良'; }
            else if (value < 6.0) { state = 'warning'; text = '偏酸性 · 注意调节'; }
            else if (value <= 7.5) { state = 'good'; text = '中性 · 适宜'; }
            else if (value <= 8.0) { state = 'warning'; text = '偏碱性 · 注意调节'; }
            else { state = 'alert'; text = '极碱 · 需改良'; }
            break;
    }
    return { state, text };
}

// ---------- UI 数值绘制更新器 ----------
function updateMetricUI(metricName, value, valElem, fillElem, statusElem, percentValue, formatFn) {
    if (value === undefined || value === null) return;

    const details = getStatusDetails(value, metricName);
    const newState = details.state;

    const oldText = valElem.innerText;
    const newText = formatFn ? formatFn(value) : value;
    valElem.innerText = newText;
    if (oldText !== newText && oldText !== '--') {
        triggerHeartbeatPulse(valElem);
    }

    valElem.classList.remove('text-warning', 'text-alert');
    fillElem.classList.remove('fill-warning', 'fill-alert');
    statusElem.classList.remove('status-good', 'status-warning', 'status-alert');

    if (newState === 'alert') {
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

    const strokeDashoffset = 263.9 - (263.9 * Math.min(100, Math.max(0, percentValue)) / 100);
    fillElem.style.strokeDashoffset = strokeDashoffset;
    statusElem.innerText = details.text;

    const oldState = previousStates[metricName];
    if (newState !== oldState) {
        const metricChinese = {
            'airTemp': '空气温度', 'airHum': '空气湿度', 'soilMoisture': '土壤湿度',
            'light': '光照强度', 'co2': 'CO2 浓度', 'ph': '土壤 pH 值'
        }[metricName] || metricName;

        if (newState === 'alert' && oldState !== 'alert') {
            showToast(`⚠️ ${metricChinese} 异常警报!`, `当前监测值 ${value}，${details.text.split('·')[0].trim()}！`, 'alert');
            addLog(`[异常告警] ${metricChinese} 超出危险区间! 最新数据: ${value}`, 'error');
        } else if (newState === 'warning' && oldState === 'good') {
            showToast(`⚠️ ${metricChinese} 偏离范围`, `当前监测值 ${value}，${details.text.split('·')[0].trim()}。`, 'warning');
            addLog(`[环境警告] ${metricChinese} 偏离舒适区间. 最新数据: ${value}`, 'warn');
        } else if (newState === 'good' && oldState !== 'good') {
            addLog(`[状态恢复] ${metricChinese} 已重新归于舒适区间. 当前数值: ${value}`, 'info');
        }
        previousStates[metricName] = newState;
    }
}

// ---------- UI 全局数据装载 ----------
function updateUI(data) {
    const { temp: airTemp, air_humi: airHum, soil_humi: soilMoisture, light, ph, co2 } = data;

    updateMetricUI('ph', ph, pHValueEl, pHFill, pHStatus, ph !== undefined ? (ph / 14) * 100 : 0, v => v.toFixed(1));
    updateMetricUI('co2', co2, co2ValueEl, co2Fill, co2Status, co2 !== undefined ? (co2 / 2000) * 100 : 0, v => Math.round(v));
    updateMetricUI('soilMoisture', soilMoisture, moistureValueEl, moistureFill, moistureStatus, soilMoisture !== undefined ? soilMoisture : 0, v => v.toFixed(1));
    updateMetricUI('light', light, lightValueEl, lightFill, lightStatus, light !== undefined ? (light / 15000) * 100 : 0, v => v.toFixed(1));
    updateMetricUI('airTemp', airTemp, airTempValueEl, tempFill, tempStatus, airTemp !== undefined ? ((airTemp + 10) / 55) * 100 : 0, v => v.toFixed(1));
    updateMetricUI('airHum', airHum, airHumValueEl, airHumFill, airHumStatus, airHum !== undefined ? airHum : 0, v => v.toFixed(1));
}

// ---------- 拉取全局 24h 统计 ----------
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
        console.error('统计加载失败:', err);
    }
}

// ---------- 拉取单次最新数值 ----------
async function fetchLatestAndUpdate() {
    try {
        const response = await fetch('/api/latest');
        if (!response.ok) return;
        const data = await response.json();
        if (data.error) return;
        updateUI(data);
    } catch (err) {
        console.error('拉取最新数值失败:', err);
    }
}

// ---------- 手动一键强拉刷新 ----------
function manualRefresh() {
    fetchLatestAndUpdate();
    fetchStats();

    // 强制触发全部卡片跳跃动画
    triggerHeartbeatPulse(pHValueEl);
    triggerHeartbeatPulse(co2ValueEl);
    triggerHeartbeatPulse(moistureValueEl);
    triggerHeartbeatPulse(lightValueEl);
    triggerHeartbeatPulse(airTempValueEl);
    triggerHeartbeatPulse(airHumValueEl);

    const btn = document.getElementById('manualRefreshBtn');
    const orig = btn.innerHTML;
    btn.innerHTML = '✅ 已校正最新数据';
    setTimeout(() => btn.innerHTML = orig, 1200);
}

// ---------- 国际化实时时钟同步 ----------
const clockFormatter = new Intl.DateTimeFormat('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
    hour12: false
});

function updateClock() {
    const d = new Date();
    document.getElementById('liveClock').innerText = clockFormatter.format(d).replace(/\//g, '/');
}

// ---------- Chart.js 核心图表逻辑 ----------
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
    ph: { name: '土壤 pH 值', unit: '', icon: '🧪', yLabel: 'pH值', color: '#c084fc' },
    co2: { name: 'CO₂ 浓度', unit: 'ppm', icon: '💨', yLabel: '浓度 (ppm)', color: '#34d399' },
    soil_humi: { name: '土壤湿度', unit: '%', icon: '💧', yLabel: '相对湿度 (%)', color: '#60a5fa' },
    light: { name: '光照强度', unit: 'lux', icon: '☀️', yLabel: '光照 (lux)', color: '#fbbf24' },
    temp: { name: '空气温度', unit: '°C', icon: '🌡️', yLabel: '温度 (°C)', color: '#f87171' },
    air_humi: { name: '空气湿度', unit: '%', icon: '🌧️', yLabel: '相对湿度 (%)', color: '#22d3ee' }
};

function getSelectedMetrics() {
    const checkboxes = document.querySelectorAll('#metricCheckboxes input[type="checkbox"]:checked');
    return Array.from(checkboxes).map(cb => cb.value);
}

// ---------- Widescreen Crosshair Plugin with Hover Acrylic Card ----------
const widescreenCrosshair = {
    id: 'widescreenCrosshair',
    afterEvent(chart, args) {
        const { event } = args;
        const isMouseMove = event.type === 'mousemove';
        const isMouseLeave = event.type === 'mouseout' || event.type === 'mouseleave';

        if (isMouseMove) {
            chart.crosshair = {
                x: event.x,
                y: event.y,
                active: true
            };
            chart.draw();
        } else if (isMouseLeave) {
            chart.crosshair = {
                x: null,
                y: null,
                active: false
            };
            chart.draw();
        }
    },
    afterDraw(chart) {
        if (!chart.crosshair || !chart.crosshair.active || chart.crosshair.x === null) {
            return;
        }

        const { ctx, chartArea: { top, bottom, left, right }, scales } = chart;
        const { x, y } = chart.crosshair;

        // Only draw inside the actual chart plot area
        if (x < left || x > right || y < top || y > bottom) return;

        ctx.save();

        const isLight = document.body.classList.contains('light-theme');

        // 1. Get corresponding X scale index and time label
        const xScale = scales.x;
        const xIndex = xScale.getValueForPixel(x);

        if (xIndex === undefined || xIndex < 0 || xIndex >= chart.data.labels.length) {
            ctx.restore();
            return;
        }

        const timeLabel = chart.data.labels[xIndex];
        const snappedX = xScale.getPixelForValue(xIndex);

        // 2. Draw vertical and horizontal dashed crosshairs
        ctx.strokeStyle = isLight ? 'rgba(71, 85, 105, 0.35)' : 'rgba(148, 163, 184, 0.35)';
        ctx.lineWidth = 1.2;
        ctx.setLineDash([5, 5]);

        // Vertical dashed line snapped to data point column
        ctx.beginPath();
        ctx.moveTo(snappedX, top);
        ctx.lineTo(snappedX, bottom);
        ctx.stroke();

        // Horizontal dashed line matching cursor's Y value
        ctx.beginPath();
        ctx.moveTo(left, y);
        ctx.lineTo(right, y);
        ctx.stroke();

        // 3. Collect active sensor reading values for Y-axis information
        const points = [];
        chart.data.datasets.forEach((dataset) => {
            const val = dataset.data[xIndex];
            if (val !== undefined && val !== null) {
                const yScale = scales[dataset.yAxisID || 'y'];
                const yPixel = yScale.getPixelForValue(val);
                points.push({
                    label: dataset.label,
                    value: val,
                    color: dataset.borderColor || '#10b981',
                    yPixel: yPixel
                });
            }
        });

        // 4. Highlight points on curves with glowing circle indicators
        ctx.setLineDash([]); // solid lines
        points.forEach(pt => {
            ctx.fillStyle = pt.color;
            ctx.strokeStyle = '#ffffff';
            ctx.lineWidth = 2;
            ctx.beginPath();
            ctx.arc(snappedX, pt.yPixel, 6, 0, 2 * Math.PI);
            ctx.fill();
            ctx.stroke();
        });

        if (points.length === 0) {
            ctx.restore();
            return;
        }

        // 5. Draw the beautiful floating glassmorphic tooltip card
        const tooltipWidth = 190;
        const lineHeight = 22;
        const padding = 12;
        const headerHeight = 24;
        const tooltipHeight = headerHeight + (points.length * lineHeight) + padding * 2;

        // Auto position card safely within chart area
        let tooltipX = x + 15;
        let tooltipY = y - tooltipHeight / 2;

        if (tooltipX + tooltipWidth > right) {
            tooltipX = x - tooltipWidth - 15;
        }
        if (tooltipY < top) {
            tooltipY = top + 5;
        }
        if (tooltipY + tooltipHeight > bottom) {
            tooltipY = bottom - tooltipHeight - 5;
        }

        // Card styling: acrylic translucent look
        ctx.fillStyle = isLight ? 'rgba(255, 255, 255, 0.96)' : 'rgba(8, 20, 13, 0.96)';
        ctx.strokeStyle = isLight ? '#cbd5e1' : 'rgba(16, 185, 129, 0.3)';
        ctx.lineWidth = 1.5;
        
        ctx.beginPath();
        if (ctx.roundRect) {
            ctx.roundRect(tooltipX, tooltipY, tooltipWidth, tooltipHeight, 10);
        } else {
            ctx.rect(tooltipX, tooltipY, tooltipWidth, tooltipHeight);
        }
        ctx.fill();
        ctx.stroke();

        // Time axis header
        ctx.font = "bold 11px 'Outfit', sans-serif";
        ctx.fillStyle = isLight ? '#475569' : '#34d399';
        ctx.fillText(`🕒 时间: ${timeLabel}`, tooltipX + padding, tooltipY + padding + 10);

        // Divider
        ctx.strokeStyle = isLight ? 'rgba(0, 0, 0, 0.08)' : 'rgba(255, 255, 255, 0.08)';
        ctx.lineWidth = 1;
        ctx.beginPath();
        ctx.moveTo(tooltipX + padding, tooltipY + padding + 16);
        ctx.lineTo(tooltipX + tooltipWidth - padding, tooltipY + padding + 16);
        ctx.stroke();

        // Display dataset metrics and values
        let currentY = tooltipY + padding + headerHeight + 8;
        points.forEach(pt => {
            // Visual indicator dot
            ctx.fillStyle = pt.color;
            ctx.beginPath();
            ctx.arc(tooltipX + padding + 5, currentY + 4, 3.5, 0, 2 * Math.PI);
            ctx.fill();

            // Label and Value text
            ctx.font = "600 11px 'Plus Jakarta Sans', sans-serif";
            ctx.fillStyle = isLight ? '#334155' : '#e2e8f0';
            
            const displayName = pt.label.split(' ')[0];
            const text = `${displayName}: ${pt.value}`;
            ctx.fillText(text, tooltipX + padding + 14, currentY + 8);

            currentY += lineHeight;
        });

        ctx.restore();
    }
};

async function renderChartFromAPI() {
    const canvas = document.getElementById('modalChartCanvas');
    if (!canvas) return;
    const ctx = canvas.getContext('2d');

    const isLight = document.body.classList.contains('light-theme');
    const labelColor = isLight ? '#334155' : '#a3b8cc';
    const tickColor = isLight ? '#475569' : '#64748b';
    const gridColor = isLight ? 'rgba(0, 0, 0, 0.05)' : 'rgba(255, 255, 255, 0.03)';
    const xGridColor = isLight ? 'rgba(0, 0, 0, 0.03)' : 'rgba(255, 255, 255, 0.02)';
    const tooltipBg = isLight ? 'rgba(255, 255, 255, 0.98)' : 'rgba(12, 30, 20, 0.95)';
    const tooltipTitle = isLight ? '#0f172a' : '#ffffff';
    const tooltipBody = isLight ? '#334155' : '#e2e8f0';
    const tooltipBorder = isLight ? 'rgba(0, 0, 0, 0.08)' : 'rgba(255, 255, 255, 0.08)';

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
            showToast("⚠️ 输入失效", "自定义查询必须选择开始时间与日期", "warning");
            return;
        }
        url += `&start=${start}`;
        if (end) url += `&end=${end}`;
    } else {
        url += `&unit=${timeUnit}`;
    }

    try {
        const resp = await fetch(url);
        if (!resp.ok) throw new Error('Trend API error');
        const data = await resp.json();

        if (currentChart) currentChart.destroy();

        const datasets = [];
        const yAxes = {};

        selectedFields.forEach((field, index) => {
            const cfg = paramConfig[field];
            const axisId = `y${index === 0 ? '' : '1'}`;

            let fillBg = cfg.color + '12';
            if (chartType === 'line') {
                const gradient = ctx.createLinearGradient(0, 0, 0, 320);
                gradient.addColorStop(0, cfg.color + '38');
                gradient.addColorStop(1, cfg.color + '00');
                fillBg = gradient;
            } else {
                fillBg = cfg.color;
            }

            datasets.push({
                label: `${cfg.name} (${cfg.unit})`,
                data: data.datasets[field],
                borderColor: cfg.color,
                backgroundColor: fillBg,
                borderWidth: 2.5,
                tension: 0.35,
                fill: chartType === 'line',
                pointBackgroundColor: cfg.color,
                pointBorderColor: '#ffffff',
                pointBorderWidth: 1.5,
                pointRadius: index === 0 ? 3.5 : 4,
                pointHoverRadius: 6,
                yAxisID: axisId
            });

            yAxes[axisId] = {
                type: 'linear',
                display: true,
                position: index === 0 ? 'left' : 'right',
                title: {
                    display: true,
                    text: cfg.yLabel,
                    color: labelColor,
                    font: { family: "'Plus Jakarta Sans', sans-serif", weight: '700', size: 11 }
                },
                ticks: {
                    color: tickColor,
                    font: { family: "'Plus Jakarta Sans', sans-serif", size: 10, weight: '600' }
                },
                grid: {
                    drawOnChartArea: index === 0,
                    color: gridColor
                }
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
                plugins: {
                    legend: {
                        position: 'top',
                        labels: {
                            color: labelColor,
                            font: { family: "'Plus Jakarta Sans', sans-serif", size: 12, weight: '700' },
                            usePointStyle: true,
                            pointStyle: 'circle',
                            padding: 16
                        }
                    },
                    tooltip: {
                        enabled: false // Disable default tooltip in favor of widescreen custom crosshair box
                    }
                },
                scales: {
                    x: {
                        ticks: {
                            color: tickColor,
                            font: { family: "'Plus Jakarta Sans', sans-serif", size: 10, weight: '600' },
                            maxTicksLimit: 10,
                            maxRotation: 0,
                            minRotation: 0
                        },
                        grid: {
                            color: xGridColor
                        }
                    },
                    ...yAxes
                },
                animation: { duration: 0 }
            },
            plugins: [widescreenCrosshair]
        });
    } catch (err) {
        console.error('渲染趋势图出错:', err);
    }
}

// ---------- 模态框打开与关闭控制 ----------
async function openModal(dataType) {
    const dbField = fieldMapping[dataType];

    const checkboxes = document.querySelectorAll('#metricCheckboxes input[type="checkbox"]');
    checkboxes.forEach(cb => {
        cb.checked = (cb.value === dbField);
        cb.disabled = false;
    });

    const cfg = paramConfig[dbField];
    document.getElementById('modalIcon').innerText = cfg.icon || '📊';
    document.getElementById('modalTitle').innerHTML = `历史趋势分析`;

    document.getElementById('chartModal').style.display = 'flex';
    document.getElementById('chartModal').focus();
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
    if (selectedFields.length === 0) {
        showToast("⚠️ 导出失败", "请先在指标列表中勾选至少一个环境监测项", "warning");
        return;
    }

    const timeUnit = document.getElementById('modalTimeUnit').value;
    let url = `/api/export?params=${selectedFields.join(',')}`;

    if (timeUnit === 'custom') {
        const start = document.getElementById('customStartDate').value;
        const end = document.getElementById('customEndDate').value;
        if (!start) {
            showToast("⚠️ 导出失败", "自定义导出区间必须选择开始时间与日期", "warning");
            return;
        }
        url += `&start=${start}`;
        if (end) url += `&end=${end}`;
    } else {
        const now = new Date();
        let start = new Date();
        if (timeUnit === 'live') start.setMinutes(start.getMinutes() - 5);
        else if (timeUnit === '30m') start.setMinutes(start.getMinutes() - 30);
        else if (timeUnit === '1h') start.setHours(start.getHours() - 1);
        else if (timeUnit === '6h') start.setHours(start.getHours() - 6);
        else if (timeUnit === '12h') start.setHours(start.getHours() - 12);
        else if (timeUnit === 'hour') start.setHours(start.getHours() - 24);
        else if (timeUnit === 'day') start.setDate(start.getDate() - 7);
        else if (timeUnit === 'week') start.setDate(start.getDate() - 56);
        else if (timeUnit === 'month') start.setFullYear(start.getFullYear() - 1);
        else if (timeUnit === 'year') start.setFullYear(start.getFullYear() - 5);

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

// ---------- SSE 长连接与页面加载初始化 ----------
document.addEventListener('DOMContentLoaded', () => {
    fetchLatestAndUpdate();
    fetchStats();

    const evtSource = new EventSource('/api/stream');

    evtSource.onopen = function () {
        // 更新侧边栏与健康度
        systemStatusDot.style.background = '#34d399';
        systemStatusText.innerText = '实时正常监测';
        uploadStatusVal.innerText = 'SSE Online';
        addLog('已接入智慧温室数据推流层 (SSE)。', 'info');
    };

    evtSource.onerror = function () {
        systemStatusDot.style.background = '#f87171';
        systemStatusText.innerText = '连接已被断开';
        uploadStatusVal.innerText = 'Reconnecting';
        addLog('网络断开，正在尝试重组推流连接…', 'error');
    };

    evtSource.onmessage = function (event) {
        try {
            const data = JSON.parse(event.data);
            addLog(`STM32上报: 温度 ${data.temp}°C | 湿度 ${data.air_humi}% | 土湿 ${data.soil_humi}% | 光强 ${data.light}lx | CO2 ${data.co2}ppm | pH ${data.ph}`, 'info');
            updateUI(data);

            // 如果处于“实时”且 Modal 展开，流式刷新图表
            const timeUnit = document.getElementById('modalTimeUnit').value;
            if (document.getElementById('chartModal').style.display === 'flex' && currentChart && timeUnit === 'live') {
                let timeStr = '';
                if (data.time) {
                    try {
                        const sseTime = new Date(data.time);
                        timeStr = `${String(sseTime.getHours()).padStart(2, '0')}:${String(sseTime.getMinutes()).padStart(2, '0')}:${String(sseTime.getSeconds()).padStart(2, '0')}`;
                    } catch (e) { }
                }
                if (!timeStr) {
                    const d = new Date();
                    timeStr = `${String(d.getHours()).padStart(2, '0')}:${String(d.getMinutes()).padStart(2, '0')}:${String(d.getSeconds()).padStart(2, '0')}`;
                }

                const lastLabel = currentChart.data.labels[currentChart.data.labels.length - 1];
                const selectedFields = getSelectedMetrics();

                if (lastLabel === timeStr) {
                    selectedFields.forEach((field, index) => {
                        const val = data[field];
                        if (currentChart.data.datasets[index]) {
                            currentChart.data.datasets[index].data[currentChart.data.datasets[index].data.length - 1] = val;
                        }
                    });
                } else {
                    currentChart.data.labels.push(timeStr);
                    selectedFields.forEach((field, index) => {
                        const val = data[field];
                        if (currentChart.data.datasets[index]) {
                            currentChart.data.datasets[index].data.push(val);
                        }
                    });
                }

                if (currentChart.data.labels.length > 60) {
                    currentChart.data.labels.shift();
                    currentChart.data.datasets.forEach(dataset => dataset.data.shift());
                }
                currentChart.update();
            }
        } catch (e) {
            console.error("解析 SSE 数据失败", e);
        }
    };

    setInterval(updateClock, 1000);
    setInterval(fetchStats, 30000);

    document.getElementById('manualRefreshBtn').addEventListener('click', manualRefresh);
    document.getElementById('exportAllCsvBtn').addEventListener('click', exportAllCsv);
    updateClock();

    // 卡片点击与键盘触发事件绑定
    document.querySelectorAll('.card').forEach(card => {
        const handler = (e) => {
            const type = card.getAttribute('data-type');
            if (type) openModal(type);
        };
        card.addEventListener('click', handler);
        card.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' || e.key === ' ') {
                e.preventDefault();
                handler(e);
            }
        });
    });

    // 模态框关闭控制
    document.getElementById('closeModalBtn').addEventListener('click', closeModal);
    window.addEventListener('click', (e) => {
        const modal = document.getElementById('chartModal');
        if (e.target === modal) closeModal();
    });

    document.getElementById('modalTimeUnit').addEventListener('change', (e) => {
        document.getElementById('customDateGroup').style.display = e.target.value === 'custom' ? 'flex' : 'none';
        if (e.target.value !== 'custom') renderChartFromAPI();
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

    // ---------- 浅色/深色主题动态 SVG 切换控制 ----------
    const themeBtn = document.getElementById('themeToggleBtn');

    // 初始化主题状态 (默认为深色主题)
    const isLightMode = localStorage.getItem('themeMode') === 'light';
    if (isLightMode) {
        document.body.classList.add('light-theme');
    }

    if (themeBtn) {
        themeBtn.addEventListener('click', () => {
            const currentLight = document.body.classList.toggle('light-theme');
            localStorage.setItem('themeMode', currentLight ? 'light' : 'dark');

            if (currentLight) {
                showToast("☀️ 已切换为浅色模式");
            } else {
                showToast("🌙 已切换为深色模式");
            }

            // 动态刷新历史趋势分析图的网格和标签颜色！
            if (document.getElementById('chartModal') && document.getElementById('chartModal').style.display === 'flex') {
                renderChartFromAPI();
            }
        });
    }
});

// ---------- 系统运行终端控制逻辑 ----------
let systemLogs = [];

function saveLogs() {
    localStorage.setItem('systemLogs', JSON.stringify(systemLogs));
}

function updateLogCounts() {
    const total = systemLogs.length;

    const badgeEl = document.getElementById('logBadgeCount');
    if (badgeEl) badgeEl.innerText = total;

    const countEl = document.getElementById('logCount');
    if (countEl) countEl.innerText = total;

    // 更新顶栏告警数
    const errCount = systemLogs.filter(l => l.level === 'error').length;
    const glanceErr = document.getElementById('glanceErrorCount');
    if (glanceErr) glanceErr.innerText = `${errCount} 条`;
}

function openLogModal() {
    const modal = document.getElementById('logModal');
    if (modal) {
        modal.style.display = 'flex';
        // 自动聚焦到关闭按钮
        document.getElementById('closeLogModalBtn')?.focus();

        // 滚动到终端最底部
        const terminal = document.getElementById('logTerminal');
        if (terminal) {
            terminal.scrollTop = terminal.scrollHeight;
        }
    }
}

function closeLogModal() {
    const modal = document.getElementById('logModal');
    if (modal) modal.style.display = 'none';
}

document.addEventListener('DOMContentLoaded', () => {
    try {
        const saved = localStorage.getItem('systemLogs');
        if (saved) {
            systemLogs = JSON.parse(saved);
            updateLogCounts();

            // 清空默认内容，重新渲染加载的所有日志
            const terminal = document.getElementById('logTerminal');
            if (terminal) terminal.innerHTML = '';
            systemLogs.forEach(renderLog);
        }
    } catch (e) {
        console.error('加载本地运行日志出错', e);
    }

    // 绑定侧边栏按钮和关闭按钮
    document.getElementById('openLogModalBtn')?.addEventListener('click', openLogModal);
    document.getElementById('closeLogModalBtn')?.addEventListener('click', closeLogModal);

    window.addEventListener('click', (e) => {
        const modal = document.getElementById('logModal');
        if (e.target === modal) closeLogModal();
    });

    // 键盘 Esc 关闭支持
    window.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') {
            closeLogModal();
        }
    });

    document.getElementById('exportLogBtn')?.addEventListener('click', exportLogs);
    document.getElementById('clearLogBtn')?.addEventListener('click', clearLogs);

    document.getElementById('logLevelFilter')?.addEventListener('change', () => {
        const terminal = document.getElementById('logTerminal');
        if (terminal) terminal.innerHTML = '';
        systemLogs.forEach(renderLog);
    });
});

const logTimeFormatter = new Intl.DateTimeFormat('zh-CN', {
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
    hour12: false
});

function addLog(message, level = 'info') {
    const timeStr = logTimeFormatter.format(new Date());
    const logObj = { time: timeStr, message, level };
    systemLogs.push(logObj);

    if (systemLogs.length > 1000) systemLogs.shift();

    updateLogCounts();
    renderLog(logObj);
    saveLogs();
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

    terminal.scrollTop = terminal.scrollHeight;
}

function clearLogs() {
    systemLogs = [];
    const terminal = document.getElementById('logTerminal');
    if (terminal) terminal.innerHTML = '';
    updateLogCounts();
    saveLogs();
    addLog('运行终端已成功重置并就绪', 'info');
}

function exportLogs() {
    if (systemLogs.length === 0) {
        showToast("⚠️ 导出失败", "当前日志终端暂无任何数据记录可供导出", "warning");
        return;
    }

    let content = "=== Intelligent Farm System Console Logs ===\n";
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
