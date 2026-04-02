const API = '';
let sym = 'TCS', period = 30;
let priceChart = null, cmpChart = null;
const allSymbols = ['RELIANCE', 'TCS', 'INFY', 'HDFCBANK', 'ICICIBANK', 'WIPRO', 'TATAMOTORS', 'BAJFINANCE'];

// ── Search any NSE symbol ──────────────────────────────────────────────────
let suggestionTimeout = null;

document.addEventListener('DOMContentLoaded', () => {
  const input = document.getElementById('sym-input');
  const suggestionBox = document.getElementById('suggestions');
  const searchMsg = document.getElementById('search-msg');

  // Close suggestions and messages when clicking outside
  document.addEventListener('click', (e) => {
    if (!e.target.closest('.search-wrap')) {
      searchMsg.style.display = 'none';
      suggestionBox.innerHTML = '';
    }
  });

  // Handle input changes for suggestions
  input.addEventListener('input', async () => {
    const val = input.value.trim().toUpperCase();
    suggestionBox.innerHTML = '';

    // Clear suggestions if input is empty or too short
    if (!val || val.length < 2) {
      return;
    }

    try {
      const res = await fetch(`${API}/suggest?q=${val}`);

      if (!res.ok) {
        return;
      }

      const data = await res.json();

      // Clear previous suggestions
      suggestionBox.innerHTML = '';

      // Show suggestions if available
      if (data.suggestions && data.suggestions.length > 0) {
        data.suggestions.forEach(item => {
          const div = document.createElement('div');
          div.className = 'suggestion-item';
          div.textContent = `${item.symbol} — ${item.name}`;

          div.onclick = () => {
            input.value = item.symbol;
            suggestionBox.innerHTML = '';
          };

          suggestionBox.appendChild(div);
        });
      } else {
        // Show "no results" message
        const div = document.createElement('div');
        div.className = 'suggestion-item';
        div.style.color = '#8099b0';
        div.style.fontStyle = 'italic';
        div.textContent = 'No matching symbols found';
        suggestionBox.appendChild(div);
      }
    } catch (error) {
      console.error('Error fetching suggestions:', error);
    }
  });

  // Initialize the app
  loadCompanies();
});

async function searchSymbol() {
  const input = document.getElementById('sym-input');
  const suggestionBox = document.getElementById('suggestions');
  const btn = document.getElementById('search-btn');
  const msg = document.getElementById('search-msg');
  const q = input.value.replace(/\s+/g, '').toUpperCase();

  if (!q) return;

  // Clear suggestions when searching
  suggestionBox.innerHTML = '';

  btn.disabled = true;
  btn.textContent = 'Fetching…';
  msg.style.display = 'block';
  msg.style.color = '#8099b0';
  msg.textContent = `Fetching ${q} from Yahoo Finance NSE…`;

  // Clear any existing auto-hide timeout
  if (suggestionTimeout) {
    clearTimeout(suggestionTimeout);
  }

  try {
    const res = await fetch(`${API}/search?q=${q}`);
    const data = await res.json();

    if (!res.ok) {
      msg.style.color = '#ef4444';
      msg.textContent = data.detail || 'Symbol not found';

      // Auto-hide error message after 4 seconds
      suggestionTimeout = setTimeout(() => {
        msg.style.display = 'none';
      }, 4000);
      return;
    }

    msg.style.color = '#22c55e';
    msg.textContent = `✓ ${data.name} — ₹${data.latest_close} (${data.daily_change >= 0 ? '+' : ''}${data.daily_change}%)`;

    if (!allSymbols.includes(q)) {
      allSymbols.push(q);
      addCompanyCard(data);
    }

    // Auto-hide success message after 2.5 seconds and clear input
    suggestionTimeout = setTimeout(() => {
      msg.style.display = 'none';
      input.value = '';
    }, 2500);

    selectCompany(q);
  } catch (e) {
    msg.style.color = '#ef4444';
    msg.textContent = 'Network error - please try again';

    // Auto-hide error message after 4 seconds
    suggestionTimeout = setTimeout(() => {
      msg.style.display = 'none';
    }, 4000);
  } finally {
    btn.disabled = false;
    btn.textContent = 'Fetch →';
  }
}

function addCompanyCard(c) {
  const list = document.getElementById('company-list');
  const d = document.createElement('div');
  d.className = 'company-card';
  d.id = `card-${c.symbol}`;
  d.onclick = () => selectCompany(c.symbol);
  d.innerHTML = `
    <div class="company-name">${c.name}</div>
    <div class="company-symbol">${c.symbol}</div>
    <div class="company-price ${c.daily_change >= 0 ? 'up' : 'down'}">
      ₹${c.latest_close?.toLocaleString('en-IN')}
      <span style="font-size:.7rem">${c.daily_change >= 0 ? '▲' : '▼'} ${Math.abs(c.daily_change)}%</span>
    </div>`;
  list.appendChild(d);
}

// ── Load sidebar ───────────────────────────────────────────────────────────
async function loadCompanies() {
  const res = await fetch(`${API}/companies`);
  const data = await res.json();
  const list = document.getElementById('company-list');
  list.innerHTML = data.companies.map(c => `
    <div class="company-card" id="card-${c.symbol}" onclick="selectCompany('${c.symbol}')">
      <div class="company-name">${c.name}</div>
      <div class="company-symbol">${c.symbol} · ${c.sector}</div>
      <div class="company-price ${c.daily_change >= 0 ? 'up' : 'down'}">
        ₹${c.latest_close.toLocaleString('en-IN')}
        <span style="font-size:.7rem">${c.daily_change >= 0 ? '▲' : '▼'} ${Math.abs(c.daily_change)}%</span>
      </div>
    </div>`).join('');
  selectCompany('TCS');
}

async function selectCompany(s) {
  document.querySelectorAll('.company-card').forEach(e => e.classList.remove('active'));
  document.getElementById(`card-${s}`)?.classList.add('active');
  sym = s;
  await renderMain(s, period);
}

async function renderMain(s, days) {
  document.getElementById('main-panel').innerHTML = `<div class="loading">Loading ${s}…</div>`;
  const [stock, summary, sent, gain] = await Promise.all([
    fetch(`${API}/data/${s}?days=${days}`).then(r => r.json()),
    fetch(`${API}/summary/${s}`).then(r => r.json()),
    fetch(`${API}/sentiment/${s}`).then(r => r.json()),
    fetch(`${API}/gainers?days=7`).then(r => r.json()),
  ]);

  const chg = stock.data?.[stock.data.length - 1]?.daily_return ?? 0;
  const sel = allSymbols;

  document.getElementById('main-panel').innerHTML = `
    <div class="tab-row">
      <div class="tab active" onclick="switchTab('analytics',this)">Analytics</div>
      <div class="tab" onclick="switchTab('compare',this)">Compare</div>
    </div>

    <div id="tab-analytics">
      <div class="top-row">
        <div class="stat-card">
          <div class="stat-label">Latest Close</div>
          <div class="stat-value">₹${(summary.latest_close || 0).toLocaleString('en-IN')}</div>
          <div class="stat-sub ${chg >= 0 ? 'up' : 'down'}">${chg >= 0 ? '▲' : '▼'} ${Math.abs(chg).toFixed(2)}% today</div>
        </div>
        <div class="stat-card">
          <div class="stat-label">52-Week High / Low</div>
          <div class="stat-value up">₹${(stock.w52_high || 0).toLocaleString('en-IN')}</div>
          <div class="stat-sub down">Low: ₹${(stock.w52_low || 0).toLocaleString('en-IN')}</div>
        </div>
        <div class="stat-card">
          <div class="stat-label">MA 7 / MA 30</div>
          <div class="stat-value">₹${(summary.ma7 || 0).toLocaleString('en-IN')}</div>
          <div class="stat-sub">30D: ₹${(summary.ma30 || 0).toLocaleString('en-IN')}</div>
        </div>
        <div class="stat-card">
          <div class="stat-label">Avg Volume</div>
          <div class="stat-value">${((summary.avg_volume || 0) / 1e6).toFixed(2)}M</div>
          <div class="stat-sub">${summary.total_trading_days || 0} trading days</div>
        </div>
      </div>

      <div class="chart-section">
        <div class="chart-header">
          <div class="chart-title">Closing Price — ${summary.name || s} <span style="color:#22c55e;font-size:.7rem;margin-left:6px">● Real NSE Data</span></div>
          <div class="period-btns">
            ${[7, 30, 90, 180, 365].map(d => `<div class="period-btn ${days === d ? 'active' : ''}" onclick="changePeriod(${d})">${d === 365 ? '1Y' : d === 180 ? '6M' : d === 90 ? '3M' : d === 30 ? '1M' : '7D'}</div>`).join('')}
          </div>
        </div>
        <div class="chart-wrap"><canvas id="priceChart"></canvas></div>
      </div>

      <div class="sentiment-row">
        <div class="sentiment-card">
          <div class="stat-label">AI Sentiment Score</div>
          <div class="sentiment-score">${sent.sentiment_score}</div>
          <div class="stat-sub ${sent.label.toLowerCase()}" style="font-size:.85rem;font-weight:700;margin-top:4px">${sent.label}</div>
          <div class="stat-sub" style="margin-top:6px">
            Momentum ${sent.components.momentum_score} · Stability ${sent.components.stability_score} · Trend ${sent.components.trend_score}
          </div>
        </div>
        <div class="sentiment-card">
          <div class="stat-label">Performance Metrics</div>
          <div style="margin-top:10px;display:flex;flex-direction:column;gap:8px">
            ${[
      ['Volatility', summary.volatility ?? 'N/A', ''],
      ['Momentum (30D)', `${(summary.momentum ?? 0).toFixed(2)}%`, (summary.momentum ?? 0) >= 0 ? 'up' : 'down'],
      ['Avg Close (1Y)', `₹${(summary.avg_close || 0).toLocaleString('en-IN')}`, ''],
    ].map(([l, v, c]) => `<div style="display:flex;justify-content:space-between;font-size:.8rem">
              <span style="color:#4a6080">${l}</span><span class="${c}">${v}</span></div>`).join('')}
          </div>
        </div>
      </div>

      <div class="gl-row">
        <div class="gl-card">
          <div class="gl-title" style="color:#22c55e">▲ Top Gainers (7D)</div>
          ${gain.top_gainers.map(g => `<div class="gl-item" onclick="selectCompany('${g.symbol}')">
            <span>${g.name}</span><span class="up">+${g.change_pct}%</span></div>`).join('')}
        </div>
        <div class="gl-card">
          <div class="gl-title" style="color:#ef4444">▼ Top Losers (7D)</div>
          ${gain.top_losers.map(g => `<div class="gl-item" onclick="selectCompany('${g.symbol}')">
            <span>${g.name}</span><span class="down">${g.change_pct}%</span></div>`).join('')}
        </div>
      </div>
    </div>

    <div id="tab-compare" style="display:none">
      <div class="chart-section">
        <div class="chart-header"><div class="chart-title">Compare Two Stocks (Normalised to 100)</div></div>
        <div class="compare-inputs">
          <select id="c1">${sel.map(s2 => `<option ${s2 === s ? 'selected' : ''}>${s2}</option>`).join('')}</select>
          <select id="c2">${sel.map(s2 => `<option ${s2 === 'INFY' ? 'selected' : ''}>${s2}</option>`).join('')}</select>
          <select id="cdays"><option value="30">30D</option><option value="90">90D</option><option value="180">180D</option></select>
          <button onclick="runCompare()">Compare →</button>
        </div>
        <div class="chart-wrap"><canvas id="cmpChart"></canvas></div>
        <div id="cmp-stats" style="margin-top:10px"></div>
      </div>
    </div>
  `;

  // Draw price chart
  const dates = stock.data.map(d => d.date);
  const closes = stock.data.map(d => d.close);
  const ma7s = stock.data.map(d => d.ma7);
  const lastDate = new Date(dates[dates.length - 1]);
  const predDates = [1, 2, 3, 4, 5].map(i => {
    const d = new Date(lastDate); d.setDate(d.getDate() + i); return d.toISOString().slice(0, 10);
  });
  const padClose = [...closes, ...stock.prediction.map(() => null)];
  const padPred = [...closes.map(() => null), closes[closes.length - 1], ...(stock.prediction || [])];
  const allDates = [...dates, ...predDates];

  if (priceChart) priceChart.destroy();
  priceChart = new Chart(document.getElementById('priceChart'), {
    type: 'line',
    data: {
      labels: allDates,
      datasets: [
        { label: 'Close', data: padClose, borderColor: '#4a9eff', backgroundColor: 'rgba(74,158,255,.08)', fill: true, tension: .3, pointRadius: 0, borderWidth: 2 },
        { label: '7-Day MA', data: [...ma7s, ...stock.prediction.map(() => null)], borderColor: '#f59e0b', borderDash: [5, 4], tension: .3, pointRadius: 0, borderWidth: 1.5 },
        { label: 'Prediction', data: padPred, borderColor: '#a855f7', borderDash: [3, 3], tension: .1, pointRadius: 3, borderWidth: 1.5, pointBackgroundColor: '#a855f7' },
      ],
    },
    options: {
      responsive: true, maintainAspectRatio: false,
      interaction: { mode: 'index', intersect: false },
      plugins: {
        legend: { labels: { color: '#8099b0', font: { size: 11 } } },
        tooltip: {
          backgroundColor: '#1e2a3a', titleColor: '#c8d8f0', bodyColor: '#8099b0', borderColor: '#2a3a50', borderWidth: 1,
          callbacks: { label: ctx => ` ${ctx.dataset.label}: ₹${ctx.parsed.y?.toLocaleString('en-IN') ?? '—'}` }
        },
      },
      scales: {
        x: { ticks: { color: '#4a6080', maxTicksLimit: 8, font: { size: 10 } }, grid: { color: '#1e2a3a' } },
        y: { ticks: { color: '#4a6080', font: { size: 10 }, callback: v => '₹' + v.toLocaleString('en-IN') }, grid: { color: '#1e2a3a' } },
      },
    },
  });
}

async function runCompare() {
  const s1 = document.getElementById('c1').value;
  const s2 = document.getElementById('c2').value;
  const d = document.getElementById('cdays').value;
  const res = await fetch(`${API}/compare?symbol1=${s1}&symbol2=${s2}&days=${d}`);
  const data = await res.json();
  const labels = data.normalised_history.map(h => h.date);
  const d1 = data.normalised_history.map(h => h[s1]);
  const d2 = data.normalised_history.map(h => h[s2]);
  if (cmpChart) cmpChart.destroy();
  cmpChart = new Chart(document.getElementById('cmpChart'), {
    type: 'line',
    data: {
      labels, datasets: [
        { label: s1, data: d1, borderColor: '#4a9eff', tension: .3, pointRadius: 0, borderWidth: 2 },
        { label: s2, data: d2, borderColor: '#f59e0b', tension: .3, pointRadius: 0, borderWidth: 2 },
      ]
    },
    options: {
      responsive: true, maintainAspectRatio: false,
      plugins: {
        legend: { labels: { color: '#8099b0' } },
        tooltip: { backgroundColor: '#1e2a3a', titleColor: '#c8d8f0', bodyColor: '#8099b0' }
      },
      scales: {
        x: { ticks: { color: '#4a6080', maxTicksLimit: 8, font: { size: 10 } }, grid: { color: '#1e2a3a' } },
        y: { ticks: { color: '#4a6080' }, grid: { color: '#1e2a3a' } },
      },
    },
  });
  const p = data.performance;
  document.getElementById('cmp-stats').innerHTML = `
    <div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:10px;margin-top:8px">
      <div class="stat-card"><div class="stat-label">${s1}</div>
        <div class="stat-value ${p[s1].return_pct >= 0 ? 'up' : 'down'}">${p[s1].return_pct >= 0 ? '+' : ''}${p[s1].return_pct}%</div>
        <div class="stat-sub">₹${p[s1].start} → ₹${p[s1].end}</div></div>
      <div class="stat-card"><div class="stat-label">${s2}</div>
        <div class="stat-value ${p[s2].return_pct >= 0 ? 'up' : 'down'}">${p[s2].return_pct >= 0 ? '+' : ''}${p[s2].return_pct}%</div>
        <div class="stat-sub">₹${p[s2].start} → ₹${p[s2].end}</div></div>
      <div class="stat-card"><div class="stat-label">Correlation</div>
        <div class="stat-value" style="font-size:1.1rem">${data.correlation}</div>
        <div class="stat-sub">${data.interpretation}</div></div>
    </div>`;
}

function switchTab(tab, el) {
  document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
  el.classList.add('active');
  document.getElementById('tab-analytics').style.display = tab === 'analytics' ? '' : 'none';
  document.getElementById('tab-compare').style.display = tab === 'compare' ? '' : 'none';
}

function changePeriod(d) { period = d; renderMain(sym, d); }