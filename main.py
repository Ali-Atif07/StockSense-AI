
from fastapi import FastAPI, HTTPException, Query
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
import numpy as np
import requests
from datetime import datetime, timedelta
import sqlite3, os, time
from contextlib import asynccontextmanager

COMPANIES = {
    "RELIANCE":   {"name": "Reliance Industries",   "sector": "Energy"},
    "TCS":        {"name": "Tata Consultancy Svcs",  "sector": "IT"},
    "INFY":       {"name": "Infosys",                "sector": "IT"},
    "WIPRO":      {"name": "Wipro",                  "sector": "IT"},
    "HDFCBANK":   {"name": "HDFC Bank",              "sector": "Banking"},
    "ICICIBANK":  {"name": "ICICI Bank",             "sector": "Banking"},
    "BAJFINANCE": {"name": "Bajaj Finance",          "sector": "NBFC"},
}

DB_PATH = "data/stocks.db"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/json",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://finance.yahoo.com",
}

# ─────────────────────────────────────────────────────────────────────────────
# YAHOO FINANCE DIRECT HTTP FETCH
# ─────────────────────────────────────────────────────────────────────────────

def fetch_yahoo(symbol: str, period: str = "1y") -> pd.DataFrame:
    url = f"https://query2.finance.yahoo.com/v8/finance/chart/{symbol}.NS"
    params = {"range": period, "interval": "1d",
              "includePrePost": False, "events": "div,splits"}
    try:
        resp = requests.get(url, headers=HEADERS, params=params, timeout=15)
        resp.raise_for_status()
        data = resp.json()
        result = data.get("chart", {}).get("result", [])
        if not result:
            return pd.DataFrame()

        r  = result[0]
        ts = r.get("timestamp", [])
        q  = r["indicators"]["quote"][0]

        df = pd.DataFrame({
            "date":   pd.to_datetime(ts, unit="s")
                        .tz_localize("UTC")
                        .tz_convert("Asia/Kolkata")
                        .strftime("%Y-%m-%d"),
            "open":   q["open"],
            "high":   q["high"],
            "low":    q["low"],
            "close":  q["close"],
            "volume": q["volume"],
        })

        df[["open","high","low","close"]] = df[["open","high","low","close"]].ffill()
        df["volume"] = pd.to_numeric(df["volume"], errors="coerce").fillna(0).astype(int)
        df = df.dropna(subset=["close"])
        df[["open","high","low","close"]] = df[["open","high","low","close"]].round(2)
        df = df.drop_duplicates(subset=["date"])

        return df

    except Exception as e:
        return pd.DataFrame()

def lookup_name(symbol: str) -> dict:
    """Search Yahoo Finance for company name and sector."""
    url = "https://query2.finance.yahoo.com/v1/finance/search"
    params = {"q": f"{symbol}.NS", "lang": "en-US", "region": "IN",
              "quotesCount": 3, "newsCount": 0}
    try:
        resp = requests.get(url, headers=HEADERS, params=params, timeout=8)
        for q in resp.json().get("quotes", []):
            if q.get("exchange") in ("NSI","BSI") or ".NS" in q.get("symbol",""):
                return {"name": q.get("longname") or q.get("shortname", symbol),
                        "sector": q.get("sector", "Unknown")}
    except Exception:
        pass
    return {"name": symbol, "sector": "Unknown"}

# ─────────────────────────────────────────────────────────────────────────────
# DATABASE
# ─────────────────────────────────────────────────────────────────────────────

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    os.makedirs("data", exist_ok=True)
    conn = get_db()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS stock_prices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            symbol TEXT NOT NULL, date TEXT NOT NULL,
            open REAL, high REAL, low REAL, close REAL, volume INTEGER,
            UNIQUE(symbol, date)
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS company_info (
            symbol TEXT PRIMARY KEY, name TEXT, sector TEXT
        )
    """)
    conn.commit()
    conn.close()

def store_df(symbol: str, df: pd.DataFrame) -> int:
    conn = get_db()
    n = 0
    for _, row in df.iterrows():
        try:
            conn.execute("""
                INSERT OR IGNORE INTO stock_prices
                (symbol, date, open, high, low, close, volume)
                VALUES (?,?,?,?,?,?,?)
            """, (symbol, row["date"], float(row["open"]), float(row["high"]),
                  float(row["low"]), float(row["close"]), int(row["volume"])))
            n += 1
        except Exception:
            pass
    conn.commit()
    conn.close()
    return n

def get_name(symbol: str) -> dict:
    """Get company name — from COMPANIES dict, then DB cache, then Yahoo."""
    if symbol in COMPANIES:
        return COMPANIES[symbol]
    conn = get_db()
    row  = conn.execute("SELECT name, sector FROM company_info WHERE symbol=?", (symbol,)).fetchone()
    conn.close()
    if row:
        return {"name": row["name"], "sector": row["sector"]}
    return {"name": symbol, "sector": "Unknown"}

# ─────────────────────────────────────────────────────────────────────────────
# ANALYTICS
# ─────────────────────────────────────────────────────────────────────────────

def enrich(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy().sort_values("date")
    df["daily_return"] = ((df["close"] - df["open"]) / df["open"] * 100).round(3)
    df["ma7"]          = df["close"].rolling(7).mean().round(2)
    df["ma30"]         = df["close"].rolling(30).mean().round(2)
    df["volatility"]   = (df["daily_return"].rolling(7).std() * np.sqrt(252)).round(3)
    df["momentum"]     = df["close"].pct_change(30).mul(100).round(3)
    return df

def predict(df: pd.DataFrame) -> list:
    if len(df) < 10:
        return []
    t    = np.arange(len(df))
    coef = np.polyfit(t, df["close"].values, 1)
    return [round(float(coef[0] * i + coef[1]), 2) for i in range(len(df), len(df) + 5)]

# ─────────────────────────────────────────────────────────────────────────────
# STARTUP
# ─────────────────────────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    for symbol in COMPANIES:
        df = fetch_yahoo(symbol, "1y")
        if not df.empty:
            store_df(symbol, df)
        time.sleep(0.4)
    yield

app = FastAPI(title="Stock Intelligence Dashboard",
              description="Real NSE data · Analytics · Compare · Sentiment · Search any symbol",
              version="2.0.0", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=["*"],
                   allow_methods=["*"], allow_headers=["*"])
app.mount("/static", StaticFiles(directory="static"), name="static")

# ═════════════════════════════════════════════════════════════════════════════
# ROUTES
# ═════════════════════════════════════════════════════════════════════════════

@app.get("/", response_class=HTMLResponse, include_in_schema=False)
async def root():
    return open("static/index.html", encoding="utf-8").read()

@app.get("/health")
async def health():
    return {"status": "ok", "timestamp": datetime.now().isoformat()}

@app.get("/companies", tags=["Data"])
async def get_companies():
    conn, result = get_db(), []
    for sym, info in COMPANIES.items():
        row = conn.execute("""
            SELECT close, open, date FROM stock_prices
            WHERE symbol=? ORDER BY date DESC LIMIT 1
        """, (sym,)).fetchone()
        if row:
            result.append({
                "symbol": sym, "name": info["name"], "sector": info["sector"],
                "latest_close": row["close"], "date": row["date"],
                "daily_change": round((row["close"]-row["open"])/row["open"]*100, 2),
                "is_real_data": True,
            })
    conn.close()
    return {"companies": result, "total": len(result)}

@app.get("/search", tags=["Data"])
async def search_symbol(q: str = Query(..., description="Any NSE symbol e.g. SBIN, ONGC, LT")):
    """Fetch and store any NSE symbol on demand — not limited to the default 8."""
    symbol = q.strip().upper()

    conn     = get_db()
    existing = conn.execute("SELECT COUNT(*) as c FROM stock_prices WHERE symbol=?",
                            (symbol,)).fetchone()["c"]
    conn.close()

    if existing == 0:
        df = fetch_yahoo(symbol, "1y")
        if df.empty:
            raise HTTPException(404,
                f"No data found for '{symbol}' on NSE. "
                "Check the symbol — use NSE ticker without .NS suffix (e.g. SBIN, ONGC, LT, NESTLEIND)")
        store_df(symbol, df)
        info = lookup_name(symbol)
        conn = get_db()
        conn.execute("INSERT OR REPLACE INTO company_info VALUES (?,?,?)",
                     (symbol, info["name"], info["sector"]))
        conn.commit()
        conn.close()

    conn = get_db()
    row  = conn.execute("SELECT close, open, date FROM stock_prices WHERE symbol=? ORDER BY date DESC LIMIT 1",
                        (symbol,)).fetchone()
    conn.close()
    if not row:
        raise HTTPException(404, f"Could not retrieve data for {symbol}")

    info = get_name(symbol)
    return {
        "symbol": symbol, "name": info["name"], "sector": info["sector"],
        "latest_close": row["close"], "date": row["date"],
        "daily_change": round((row["close"]-row["open"])/row["open"]*100, 2),
        "fetched_now": existing == 0,
        "is_real_data": True,
    }

@app.get("/data/{symbol}", tags=["Data"])
async def get_data(symbol: str, days: int = Query(30, ge=7, le=365)):
    symbol = symbol.upper()
    conn   = get_db()
    rows   = conn.execute("""
        SELECT date, open, high, low, close, volume FROM stock_prices
        WHERE symbol=? ORDER BY date DESC LIMIT ?
    """, (symbol, days + 30)).fetchall()
    full = conn.execute("""
        SELECT high, low FROM stock_prices WHERE symbol=? AND date>=?
    """, (symbol, (datetime.now()-timedelta(days=365)).strftime("%Y-%m-%d"))).fetchall()
    conn.close()

    if not rows:
        raise HTTPException(404, f"No data for {symbol}. Search it first via /search?q={symbol}")

    # df   = enrich(pd.DataFrame([dict(r) for r in rows])).tail(days)
    df_raw = pd.DataFrame([dict(r) for r in rows])

    if df_raw.empty:
        raise HTTPException(404, f"No sufficient data for {symbol}")

    df = enrich(df_raw)

    # ensure we don't exceed available data
    df = df.tail(min(days, len(df)))
    info = get_name(symbol)

    return {
        "symbol": symbol, "name": info["name"], "sector": info["sector"],
        "days": days, "is_real_data": True,
        "w52_high": round(max(r["high"] for r in full), 2) if full else None,
        "w52_low":  round(min(r["low"]  for r in full), 2) if full else None,
        "data":       df.where(pd.notna(df), None).to_dict("records"),
        "prediction": predict(df),
    }

@app.get("/summary/{symbol}", tags=["Analytics"])
async def get_summary(symbol: str):
    symbol = symbol.upper()
    since  = (datetime.now()-timedelta(days=365)).strftime("%Y-%m-%d")
    conn   = get_db()
    rows   = conn.execute("""
        SELECT date, open, high, low, close, volume FROM stock_prices
        WHERE symbol=? AND date>=? ORDER BY date
    """, (symbol, since)).fetchall()
    conn.close()
    if not rows:
        raise HTTPException(404, f"No data for {symbol}")

    df = enrich(pd.DataFrame([dict(r) for r in rows]))
    l  = df.iloc[-1]
    return {
        "symbol": symbol, "name": get_name(symbol)["name"],
        "latest_close": round(float(l["close"]), 2),
        "daily_change": round(float(l["daily_return"]), 3),
        "w52_high":     round(float(df["high"].max()), 2),
        "w52_low":      round(float(df["low"].min()), 2),
        "avg_close":    round(float(df["close"].mean()), 2),
        "avg_volume":   int(df["volume"].mean()),
        "volatility":   round(float(df["volatility"].dropna().iloc[-1]), 3) if not df["volatility"].dropna().empty else None,
        "momentum":     round(float(df["momentum"].dropna().iloc[-1]), 3)   if not df["momentum"].dropna().empty else None,
        "ma7":          round(float(l["ma7"]),  2) if pd.notna(l["ma7"])  else None,
        "ma30":         round(float(l["ma30"]), 2) if pd.notna(l["ma30"]) else None,
        "total_trading_days": len(df),
    }

@app.get("/compare", tags=["Analytics"])
async def compare(symbol1: str = Query(...), symbol2: str = Query(...),
                  days: int = Query(30, ge=7, le=365)):
    s1, s2 = symbol1.upper(), symbol2.upper()
    since  = (datetime.now()-timedelta(days=days+30)).strftime("%Y-%m-%d")
    conn   = get_db()

    def series(sym):
        rows = conn.execute("""
            SELECT date, close FROM stock_prices WHERE symbol=? AND date>=? ORDER BY date
        """, (sym, since)).fetchall()
        if not rows:
            raise HTTPException(404, f"No data for {sym}")
        return pd.DataFrame([dict(r) for r in rows]).set_index("date")["close"].rename(sym)

    s1s = series(s1); s2s = series(s2)
    conn.close()
    combined = pd.concat([s1s, s2s], axis=1).dropna().tail(days)
    norm     = (combined / combined.iloc[0] * 100).round(3)
    corr     = round(float(combined.corr().iloc[0,1]), 4)

    return {
        "symbol1": s1, "name1": get_name(s1)["name"],
        "symbol2": s2, "name2": get_name(s2)["name"],
        "days": days, "correlation": corr,
        "interpretation": (
            "Highly correlated"      if corr > 0.8 else
            "Moderately correlated"  if corr > 0.5 else
            "Weak correlation"       if corr > 0.2 else
            "Low/inverse correlation"
        ),
        "performance": {
            s: {"start": round(float(combined[s].iloc[0]),2),
                "end":   round(float(combined[s].iloc[-1]),2),
                "return_pct": round((float(combined[s].iloc[-1])/float(combined[s].iloc[0])-1)*100,2)}
            for s in [s1, s2]
        },
        "normalised_history": [
            {"date": d, s1: row[s1], s2: row[s2]} for d, row in norm.iterrows()
        ],
    }

@app.get("/gainers", tags=["Analytics"])
async def gainers(days: int = Query(7, ge=1, le=90)):
    conn = get_db()
    syms = list(COMPANIES.keys())
    extra = conn.execute("SELECT symbol FROM company_info").fetchall()
    syms += [r["symbol"] for r in extra if r["symbol"] not in syms]
    result = []
    for sym in syms:
        rows = conn.execute("""
            SELECT close FROM stock_prices WHERE symbol=? ORDER BY date DESC LIMIT ?
        """, (sym, days+1)).fetchall()
        if len(rows) >= 2:
            chg = round((rows[0]["close"]-rows[-1]["close"])/rows[-1]["close"]*100, 2)
            info = get_name(sym)
            result.append({"symbol": sym, "name": info["name"],
                           "sector": info.get("sector","Other"),
                           "change_pct": chg, "latest_close": rows[0]["close"]})
    conn.close()
    result.sort(key=lambda x: x["change_pct"], reverse=True)
    return {"period_days": days, "top_gainers": result[:3], "top_losers": result[-3:][::-1]}

@app.get("/sentiment/{symbol}", tags=["Analytics"])
async def sentiment(symbol: str):
    symbol = symbol.upper()
    conn   = get_db()
    rows   = conn.execute("""
        SELECT date, open, close, high, low, volume FROM stock_prices
        WHERE symbol=? ORDER BY date DESC LIMIT 60
    """, (symbol,)).fetchall()
    conn.close()
    if not rows:
        raise HTTPException(404, f"No data for {symbol}")

    df  = enrich(pd.DataFrame([dict(r) for r in rows]).sort_values("date"))
    mom = float(df["momentum"].dropna().iloc[-1])   if not df["momentum"].dropna().empty   else 0
    vol = float(df["volatility"].dropna().iloc[-1]) if not df["volatility"].dropna().empty else 25
    ma7 = float(df["ma7"].dropna().iloc[-1])        if not df["ma7"].dropna().empty        else float(df["close"].iloc[-1])

    ms = min(max((mom+20)/40*50, 0), 50)
    vs = min(max((50-vol)/50*30, 0), 30)
    ts = 20 if float(df["close"].iloc[-1]) > ma7 else 0
    sc = round(ms + vs + ts, 1)

    return {
        "symbol": symbol, "name": get_name(symbol)["name"],
        "sentiment_score": sc,
        "label": "Bullish" if sc >= 60 else "Neutral" if sc >= 40 else "Bearish",
        "components": {"momentum_score": round(ms,1), "stability_score": round(vs,1), "trend_score": ts},
        "note": "Composite: 30-day momentum + volatility stability + MA7 trend signal.",
    }

@app.get("/suggest", tags=["Data"])
async def suggest(q: str):
    url = "https://query2.finance.yahoo.com/v1/finance/search"
    params = {
        "q": q,
        "lang": "en-US",
        "region": "IN",
        "quotesCount": 10,
        "newsCount": 0
    }

    try:
        resp = requests.get(url, headers=HEADERS, params=params, timeout=5)
        data = resp.json()
        suggestions = []
        for item in data.get("quotes", []):
            sym = item.get("symbol", "")
            if sym.endswith(".NS"): 
                suggestions.append({
                    "symbol": sym.replace(".NS", ""),
                    "name": item.get("longname") or item.get("shortname", "")
                })

        return {"suggestions": suggestions[:5]}

    except Exception:
        return {"suggestions": []}