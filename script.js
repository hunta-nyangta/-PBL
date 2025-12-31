// Global variables
let luxChart, psmChart, correlationChart;
const MAX_DATA_POINTS = 100;
let dataLog = [];
let startTime;

// Serial related
let port;
let reader;
let keepReading = true;

const colors = {
    blue: '#0ea5e9',
    blueAlpha: 'rgba(14, 165, 233, 0.1)',
    green: '#10b981',
    red: '#ef4444',
    purple: '#8b5cf6',
    white: '#f0f2f5'
};

document.addEventListener('DOMContentLoaded', () => {
    initCharts();
    updateTimestamp();
    setInterval(updateTimestamp, 1000);

    document.getElementById('export-csv').addEventListener('click', exportToCSV);
    document.getElementById('connect-serial').addEventListener('click', connectSerial);
    document.getElementById('send-target').addEventListener('click', sendTarget);

    // Sync slider and input
    const slider = document.getElementById('target-slider');
    const input = document.getElementById('target-input');

    slider.addEventListener('input', (e) => {
        input.value = e.target.value;
    });

    input.addEventListener('input', (e) => {
        slider.value = e.target.value;
    });
});

async function sendTarget() {
    const targetVal = document.getElementById('target-input').value;
    if (!targetVal) return;

    if (!port || !port.writable) {
        alert("기기가 연결되어 있지 않습니다. 먼저 기기 연결을 해주세요.");
        return;
    }

    try {
        const encoder = new TextEncoder();
        const writer = port.writable.getWriter();
        const data = `T${targetVal}\n`;
        await writer.write(encoder.encode(data));
        writer.releaseLock();

        // Visual feedback
        const btn = document.getElementById('send-target');
        const originalText = btn.innerText;
        btn.innerText = "OK";
        btn.style.background = colors.green;
        setTimeout(() => {
            btn.innerText = originalText;
            btn.style.background = '';
        }, 1000);
    } catch (err) {
        console.error("Write Error:", err);
        alert("데이터 전송 중 오류가 발생했습니다.");
    }
}

async function connectSerial() {
    if (!("serial" in navigator)) {
        alert("이 브라우저는 Web Serial API를 지원하지 않습니다. Chrome 혹은 Edge를 사용해주세요.");
        return;
    }

    try {
        port = await navigator.serial.requestPort();
        await port.open({ baudRate: 115200 });

        const btn = document.getElementById('connect-serial');
        btn.innerHTML = `ONLINE`;
        btn.style.background = colors.green;
        btn.style.borderColor = colors.green;

        const statusDiv = document.querySelector('#status-indicator .value');
        statusDiv.innerText = 'CONNECTED';
        statusDiv.style.color = colors.green;

        startTime = Date.now();
        readLoop();
    } catch (err) {
        console.error("Serial error:", err);
        alert("시리얼 연결에 실패했습니다.");
    }
}

async function readLoop() {
    const textDecoder = new TextDecoderStream();
    const readerStream = port.readable.pipeTo(textDecoder.writable);
    reader = textDecoder.readable.getReader();

    let buffer = "";

    try {
        while (keepReading) {
            const { value, done } = await reader.read();
            if (done) break;

            buffer += value;
            const lines = buffer.split(/\r?\n/);
            buffer = lines.pop();

            for (const line of lines) {
                const cleanLine = line.trim();
                if (cleanLine) processIncomingData(cleanLine);
            }
        }
    } catch (err) {
        console.error("Read Error:", err);
    } finally {
        reader.releaseLock();
    }
}

function processIncomingData(line) {
    const data = line.split(',').map(item => item.trim());

    if (data.length >= 5) {
        try {
            const t_sec = parseFloat(data[0]) / 1000.0;
            const tgt = parseFloat(data[1]);
            const raw = parseFloat(data[2]);
            const filt = parseFloat(data[3]);
            const psm = parseFloat(data[4]);
            const kp = data[5] ? parseFloat(data[5]) : 0;

            if (isNaN(t_sec) || isNaN(tgt)) return;

            const entry = {
                time: t_sec.toFixed(2),
                target: tgt,
                raw: raw.toFixed(1),
                filtered: filt.toFixed(1),
                psm: Math.round(psm),
                kp: kp
            };

            dataLog.push(entry);
            if (dataLog.length > 2000) dataLog.shift();

            updateUI(entry);
            updateCharts(entry);
        } catch (e) {
            console.warn("Parse error", e);
        }
    }
}

function initCharts() {
    const ctxLux = document.getElementById('luxChart').getContext('2d');
    const ctxPsm = document.getElementById('psmChart').getContext('2d');
    const ctxCorr = document.getElementById('correlationChart').getContext('2d');

    Chart.defaults.color = '#94a3b8';
    Chart.defaults.font.family = "'Outfit', sans-serif";

    luxChart = new Chart(ctxLux, {
        type: 'line',
        data: {
            labels: [],
            datasets: [
                { label: 'Target', data: [], borderColor: colors.red, borderDash: [5, 5], pointRadius: 0, fill: false },
                { label: 'Raw Lux', data: [], borderColor: 'rgba(14, 165, 233, 0.3)', borderWidth: 1, pointRadius: 0, fill: false },
                { label: 'Filtered Lux', data: [], borderColor: colors.blue, borderWidth: 3, pointRadius: 0, fill: true, backgroundColor: colors.blueAlpha }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            animation: false,
            scales: {
                y: { beginAtZero: true, grid: { color: 'rgba(255,255,255,0.05)' } },
                x: { grid: { display: false } }
            }
        }
    });

    psmChart = new Chart(ctxPsm, {
        type: 'line',
        data: {
            labels: [],
            datasets: [{ label: 'PSM Level', data: [], borderColor: colors.green, backgroundColor: 'rgba(16, 185, 129, 0.1)', borderWidth: 2, pointRadius: 0, fill: true }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            animation: false,
            scales: {
                y: { beginAtZero: true, grid: { color: 'rgba(255,255,255,0.05)' } },
                x: { grid: { display: false } }
            }
        }
    });

    correlationChart = new Chart(ctxCorr, {
        type: 'scatter',
        data: { datasets: [{ label: 'Correlation', data: [], backgroundColor: colors.purple, pointRadius: 3 }] },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                x: { title: { display: true, text: 'PSM Level' }, grid: { color: 'rgba(255,255,255,0.05)' } },
                y: { title: { display: true, text: 'Filtered Lux' }, grid: { color: 'rgba(255,255,255,0.05)' } }
            }
        }
    });
}

function updateUI(data) {
    document.getElementById('stat-target').innerText = data.target;
    document.getElementById('stat-lux').innerText = data.filtered;
    document.getElementById('stat-psm').innerText = data.psm;
    document.getElementById('uptime').innerText = `${data.time}s active`;
}

function updateCharts(data) {
    luxChart.data.labels.push(data.time);
    luxChart.data.datasets[0].data.push(data.target);
    luxChart.data.datasets[1].data.push(data.raw);
    luxChart.data.datasets[2].data.push(data.filtered);
    if (luxChart.data.labels.length > MAX_DATA_POINTS) {
        luxChart.data.labels.shift();
        luxChart.data.datasets.forEach(ds => ds.data.shift());
    }
    luxChart.update('none');

    psmChart.data.labels.push(data.time);
    psmChart.data.datasets[0].data.push(data.psm);
    if (psmChart.data.labels.length > MAX_DATA_POINTS) {
        psmChart.data.labels.shift();
        psmChart.data.datasets[0].data.shift();
    }
    psmChart.update('none');

    if (dataLog.length % 5 === 0) {
        correlationChart.data.datasets[0].data.push({ x: data.psm, y: data.filtered });
        if (correlationChart.data.datasets[0].data.length > 100) correlationChart.data.datasets[0].data.shift();
        correlationChart.update('none');
    }
}

function exportToCSV() {
    if (dataLog.length === 0) return alert('데이터가 없습니다.');
    const headers = ["Time_ms", "Target", "Raw_Lux", "Filtered_Lux", "PSM_Level", "Gain_Kp"];
    const rows = dataLog.map(d => [parseFloat(d.time) * 1000, d.target, d.raw, d.filtered, d.psm, d.kp]);
    let csvContent = "data:text/csv;charset=utf-8," + headers.join(",") + "\n" + rows.map(e => e.join(",")).join("\n");
    const link = document.createElement("a");
    link.href = encodeURI(csvContent);
    link.download = `lux_log_${Date.now()}.csv`;
    link.click();
}

function updateTimestamp() {
    document.getElementById('current-timestamp').innerText = `실시간 모니터링 | ${new Date().toLocaleString()}`;
}
