# 🚀 StockSense AI — Stock Intelligence Dashboard

A lightweight, full-stack stock analytics platform that turns raw NSE market data into meaningful insights — built using FastAPI, SQLite, and Chart.js.

Designed to simulate a real-world financial data product with clean APIs, intelligent metrics, and an interactive dashboard.

---

## ✨ What this project does

Instead of just showing stock prices, StockSense AI helps you **understand the market**:

* 📈 Track real NSE stock data (powered by Yahoo Finance)
* 🧠 Get AI-inspired sentiment insights
* ⚖️ Compare companies with normalized performance
* 🔍 Discover top gainers & losers
* 📊 Visualize trends with interactive charts

---

## 🧩 Key Features

* **Live NSE Data**
  Covers major companies like RELIANCE, TCS, INFY, HDFCBANK, ICICIBANK, WIPRO, TATAMOTORS, BAJFINANCE

* **Smart Metrics**

  * Daily Returns
  * Moving Averages (7D / 30D)
  * Volatility Score
  * Momentum Tracking
  * 52-week High/Low

* **AI Sentiment Engine**
  A custom scoring system (0–100) combining trend, momentum, and stability

* **Comparison Engine**
  Compare any two stocks with normalized performance + correlation

* **Top Movers**
  Automatically detect best & worst performing stocks

* **Interactive Dashboard**
  Clean UI with filters, charts, and real-time updates

---

## 🛠️ Tech Stack

* **Backend:** FastAPI (Python)
* **Database:** SQLite
* **Data Processing:** Pandas, NumPy, yfinance
* **Frontend:** Vanilla JavaScript + Chart.js
* **Docs:** Swagger UI (`/docs`)

---

## ⚙️ Run Locally (Without Docker)

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Start the server
uvicorn main:app --reload --port 8000
```

👉 Open in browser:

* App → http://localhost:8000
* API Docs → http://localhost:8000/docs

---

## 🐳 Run with Docker (Recommended)

### 1. Build Image

```bash
docker build -t stocksense-ai .
```

### 2. Run Container

```bash
docker run -d -p 8000:8000 stocksense-ai
```

👉 Open:

* http://localhost:8000

---

## 🌍 Deployment

This project is designed to run as a **single container (frontend + backend together)**.

You can deploy easily on:

* **Render**
* **Railway**
* **DigitalOcean**

No environment variables required — frontend automatically uses the same backend.

---

## 🔌 API Overview

All endpoints are designed to be simple and usable for real-world applications.

| Endpoint              | What it does                                             |
| --------------------- | -------------------------------------------------------- |
| `/companies`          | Returns all tracked companies with latest price & sector |
| `/data/{symbol}`      | Historical stock data with calculated metrics            |
| `/summary/{symbol}`   | Key stats like averages, volatility, momentum            |
| `/compare`            | Compare two stocks side-by-side                          |
| `/gainers`            | Shows top performing and worst performing stocks         |
| `/sentiment/{symbol}` | Returns AI-based sentiment score                         |
| `/summary/{query}` | Returns All Companies Symbol that matches with query                          |


---

## 🧠 How the Intelligence Works

* **Volatility** → Measures how unstable a stock is
* **Momentum** → Shows direction of movement (up/down trend)
* **Trend Signal** → Based on moving averages

### Final Sentiment Score (0–100):

* 0–30 → Bearish 📉
* 30–70 → Neutral ⚖️
* 70–100 → Bullish 📈

---

## 🔄 Data Flow

```
Yahoo Finance → Pandas Processing → SQLite → FastAPI → Frontend Dashboard
```

* Data is fetched and processed on startup
* Stored locally for fast performance
* Automatically used by APIs

---

## 🎯 Why this project stands out

* Clean full-stack architecture
* Real-world financial logic (not dummy data)
* API-first design (production mindset)
* Docker-ready deployment
* Focus on insights, not just data

---

## 📌 Future Improvements

* Real-time WebSocket updates
* More stocks (full NSE coverage)
* Portfolio tracking
* ML-based price prediction
* User authentication

---

## 👨‍💻 Author

Built as part of an engineering assessment to demonstrate:

* Backend API design
* Data processing skills
* Frontend integration
* Deployment readiness

---

⭐ If you found this interesting, feel free to explore or extend it!
