/* ============================================================
   dashboard.js — Turbofan Engine Analytics Dashboard
   Priscilla Nzula · github.com/priscillanzula
   All chart data sourced from NASA CMAPSS FD001
   ============================================================ */

// Set generated timestamp in header
document.getElementById('ts').textContent =
  'Generated ' + new Date().toLocaleDateString('en-GB', {
    day: 'numeric', month: 'short', year: 'numeric'
  });

// ── SHARED CHART DEFAULTS ──────────────────────────────────────
const gridColor = 'rgba(255,255,255,0.05)';
const tickColor = '#6b7280';
const base = {
  responsive: true,
  maintainAspectRatio: false,
  plugins: { legend: { display: false } }
};

// ── 1. FLEET HEALTH DONUT ─────────────────────────────────────
new Chart(document.getElementById('c-donut'), {
  type: 'doughnut',
  data: {
    labels: ['Danger', 'Warning', 'Healthy'],
    datasets: [{
      data: [25, 20, 55],
      backgroundColor: ['#f04444', '#f5a623', '#3ecf8e'],
      borderWidth: 0,
      hoverOffset: 6
    }]
  },
  options: {
    ...base,
    cutout: '68%',
    plugins: { legend: { display: false } }
  }
});

// ── 2. RUL DISTRIBUTION BAR ───────────────────────────────────
// Bins: 0-15 (danger), 15-30 (danger), 30-80 (warning), 80+ (healthy)
new Chart(document.getElementById('c-rul-dist'), {
  type: 'bar',
  data: {
    labels: ['0–15', '15–30', '30–45', '45–60', '60–80', '80–100', '100–120', '120–145'],
    datasets: [{
      data: [9, 16, 3, 11, 6, 21, 21, 13],
      backgroundColor: [
        '#f04444', '#f04444',
        '#f5a623', '#f5a623', '#f5a623',
        '#3ecf8e', '#3ecf8e', '#3ecf8e'
      ],
      borderRadius: 4,
      borderSkipped: false
    }]
  },
  options: {
    ...base,
    scales: {
      x: {
        ticks: { color: tickColor, font: { size: 10 } },
        grid:  { display: false }
      },
      y: {
        ticks: { color: tickColor, font: { size: 10 }, stepSize: 5 },
        grid:  { color: gridColor },
        title: { display: true, text: 'engines', color: tickColor, font: { size: 10 } }
      }
    }
  }
});

// ── 3. ENGINE LIFESPAN HISTOGRAM ──────────────────────────────
// Distribution of total cycles survived — 100 training engines
new Chart(document.getElementById('c-life'), {
  type: 'bar',
  data: {
    labels: ['125–150','150–175','175–200','200–225','225–250','250–275','275–300','300–325','325–350','350–375'],
    datasets: [{
      data: [6, 19, 27, 22, 9, 6, 7, 1, 2, 1],
      backgroundColor: '#4f9cf9',
      borderRadius: 4,
      borderSkipped: false
    }]
  },
  options: {
    ...base,
    scales: {
      x: {
        ticks: { color: tickColor, font: { size: 9 }, maxRotation: 45 },
        grid:  { display: false }
      },
      y: {
        ticks: { color: tickColor, font: { size: 10 }, stepSize: 5 },
        grid:  { color: gridColor },
        title: { display: true, text: 'engines', color: tickColor, font: { size: 10 } }
      }
    }
  }
});

// ── 4. SENSOR CORRELATION HORIZONTAL BAR ──────────────────────
// Absolute Pearson r with RUL — colour-coded by strength
// Red ≥ 0.65 | Amber 0.55–0.65 | Blue 0.40–0.55 | Gray < 0.40
new Chart(document.getElementById('c-corr'), {
  type: 'bar',
  data: {
    labels: [
      'sensor_11','sensor_4','sensor_12','sensor_7',
      'sensor_15','sensor_21','sensor_20','sensor_2','sensor_17','sensor_3',
      'sensor_8','sensor_13','sensor_9','sensor_14','sensor_6'
    ],
    datasets: [{
      data: [0.696,0.679,0.672,0.657,0.643,0.636,0.629,0.607,0.606,0.585,0.564,0.563,0.390,0.307,0.128],
      backgroundColor: [
        '#f04444','#f04444','#f04444','#f04444',
        '#f5a623','#f5a623','#f5a623','#f5a623','#f5a623','#f5a623',
        '#4f9cf9','#4f9cf9',
        '#6b7280','#6b7280','#6b7280'
      ],
      borderRadius: 3,
      borderSkipped: false
    }]
  },
  options: {
    ...base,
    indexAxis: 'y',
    scales: {
      x: {
        min: 0, max: 0.8,
        ticks: { color: tickColor, font: { size: 10 } },
        grid:  { color: gridColor }
      },
      y: {
        ticks: { color: tickColor, font: { size: 10 } },
        grid:  { display: false }
      }
    }
  }
});

// ── 5. FEATURE IMPORTANCE HORIZONTAL BAR ──────────────────────
// Random Forest Gini importance — top 8 features (as percentages)
new Chart(document.getElementById('c-imp'), {
  type: 'bar',
  data: {
    labels: [
      'cycle_ratio',
      's7_roll_avg','s2_roll_avg','s2_roll_std',
      's12_roll_std','s12_roll_avg','s11_roll_avg','s7_roll_std'
    ],
    datasets: [{
      data: [94.54, 0.650, 0.601, 0.552, 0.516, 0.503, 0.499, 0.497],
      backgroundColor: [
        '#a78bfa',
        '#3ecf8e','#3ecf8e','#3ecf8e','#3ecf8e','#3ecf8e','#3ecf8e','#3ecf8e'
      ],
      borderRadius: 3,
      borderSkipped: false
    }]
  },
  options: {
    ...base,
    indexAxis: 'y',
    scales: {
      x: {
        ticks: {
          color: tickColor,
          font: { size: 10 },
          callback: v => v.toFixed(1) + '%'
        },
        grid: { color: gridColor }
      },
      y: {
        ticks: { color: tickColor, font: { size: 10 } },
        grid:  { display: false }
      }
    },
    plugins: {
      legend: { display: false },
      tooltip: {
        callbacks: {
          label: ctx => ' ' + ctx.parsed.x.toFixed(3) + '%'
        }
      }
    }
  }
});

// ── 6. SENSOR DEGRADATION LINE CHART ──────────────────────────
// Average sensor readings at each life stage (0–100%) across 100 engines
// sensor_2 & sensor_11 increase with age; sensor_7 & sensor_12 decrease
new Chart(document.getElementById('c-degrade'), {
  type: 'line',
  data: {
    labels: ['0–20%', '20–40%', '40–60%', '60–80%', '80–100%'],
    datasets: [
      {
        label: 'sensor_2 (LPC temp ↑)',
        data: [642.38, 642.43, 642.53, 642.77, 643.29],
        borderColor: '#f04444',
        backgroundColor: 'transparent',
        tension: 0.4,
        pointRadius: 5,
        pointBackgroundColor: '#f04444'
      },
      {
        label: 'sensor_11 (HPC pressure ↑)',
        data: [47.35, 47.39, 47.46, 47.60, 47.91],
        borderColor: '#4f9cf9',
        backgroundColor: 'transparent',
        tension: 0.4,
        pointRadius: 5,
        pointBackgroundColor: '#4f9cf9',
        yAxisID: 'y2'
      },
      {
        label: 'sensor_7 (HPC outlet ↓)',
        data: [553.96, 553.85, 553.64, 553.19, 552.21],
        borderColor: '#3ecf8e',
        backgroundColor: 'transparent',
        tension: 0.4,
        pointRadius: 5,
        pointBackgroundColor: '#3ecf8e',
        yAxisID: 'y3'
      },
      {
        label: 'sensor_12 (fuel flow ↓)',
        data: [521.92, 521.83, 521.64, 521.26, 520.43],
        borderColor: '#f5a623',
        backgroundColor: 'transparent',
        tension: 0.4,
        pointRadius: 5,
        pointBackgroundColor: '#f5a623',
        yAxisID: 'y4'
      }
    ]
  },
  options: {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        display: true,
        position: 'top',
        labels: { color: '#9ca3af', font: { size: 11 }, boxWidth: 12, padding: 16 }
      }
    },
    scales: {
      x:  { ticks: { color: tickColor, font: { size: 11 } }, grid: { color: gridColor } },
      y:  { position: 'left',  display: false },
      y2: { position: 'left',  display: false },
      y3: { position: 'right', display: false },
      y4: { position: 'right', display: false }
    }
  }
});
