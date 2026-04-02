# Stock Data Intelligence Dashboard

A mini financial data platform built with FastAPI, SQLite, and Chart.js — fetching real NSE stock data for 8 major Indian companies.

## Features

- **Real NSE data** via yfinance — RELIANCE, TCS, INFY, HDFCBANK, ICICIBANK, WIPRO, TATAMOTORS, BAJFINANCE
- **Calculated metrics** — Daily Return, 7-Day MA, 30-Day MA, Volatility Score, 52-Week High/Low
- **REST API** with Swagger docs at `/docs`
- **Comparison endpoint** — normalised performance + correlation between any two stocks
- **Custom sentiment score** — composite metric combining momentum, volatility, and trend signals
- **Top Gainers/Losers** — ranked over configurable time window
- **Interactive dashboard** — period filters, company selector, live charts

## Setup

```bash
# Clone and install
pip install -r requirements.txt

# Run (seeds database automatically on first start, ~30 seconds)
uvicorn main:app --reload --port 8000
```

Open `http://localhost:8000` for the dashboard.  
Open `http://localhost:8000/docs` for the Swagger API documentation.

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/companies` | All tracked companies with latest price |
| GET | `/data/{symbol}?days=30` | OHLCV + metrics for N days |
| GET | `/summary/{symbol}` | 52-week stats, volatility, momentum |
| GET | `/compare?symbol1=TCS&symbol2=INFY&days=30` | Normalised comparison + correlation |
| GET | `/gainers?days=7` | Top 3 gainers and losers |
| GET | `/sentiment/{symbol}` | Composite AI sentiment score (0–100) |

## Custom Metrics

**Volatility Score** — Annualised standard deviation of daily returns over a 7-day rolling window. Higher = more volatile.

**Momentum Score** — Percentage price change over the last 30 trading days. Positive = uptrend.

**Sentiment Score (0–100)** — Composite metric built from:
- Momentum component (0–50): maps 30-day return to a score
- Stability component (0–30): lower volatility scores higher
- Trend component (0–20): close price above 7-day MA = bullish signal

## Data Flow

```
yfinance (Yahoo Finance) → Python/Pandas cleaning → SQLite → FastAPI → Chart.js dashboard
```

Data is seeded on startup and stored locally. Restart the server to refresh data.

## Tech Stack

- **Backend**: FastAPI (Python)
- **Database**: SQLite (easily swappable to PostgreSQL — change DB_PATH to connection string)
- **Data**: yfinance, Pandas, NumPy
- **Frontend**: Vanilla JS + Chart.js
- **Docs**: FastAPI Swagger (auto-generated at /docs)