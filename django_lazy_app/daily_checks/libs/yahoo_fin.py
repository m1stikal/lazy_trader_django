# daily_checks/libs/yahoo_fin.py

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Dict, Iterable, List, Mapping, Optional, Tuple

import pandas as pd
import yfinance as yf

# Import your Django models directly (no apps.get_model, no exchange logic)
from daily_checks.models import Stock,OpenPosition,Platform

import os, certifi
caf = certifi.where()
os.environ["SSL_CERT_FILE"] = caf
os.environ["REQUESTS_CA_BUNDLE"] = caf
os.environ["CURL_CA_BUNDLE"] = caf

# --------------------------------------------------------------------
# JSE suffix: ALWAYS append ".JO" to root codes when missing for Yahoo.
# --------------------------------------------------------------------

JSE_SUFFIX = ".JO"


def _to_yahoo(ticker_root: str) -> str:
    t = (ticker_root or "").upper().strip()
    return t if "." in t else f"{t}{JSE_SUFFIX}"


# -----------------------------
# Finance helpers
# -----------------------------

def _download(symbol: str, period: str = "6mo", interval: str = "1d") -> pd.DataFrame:
    # Do NOT pass requests.Session; let yfinance manage its own session
    df = yf.download(symbol, period=period, interval=interval, auto_adjust=True, progress=False)
    if isinstance(df, pd.DataFrame) and not df.empty:
        df = df.rename(columns={c: c.capitalize() for c in df.columns})
    return df


def _sma(series: pd.Series, window: int) -> pd.Series:
    return series.rolling(window=window, min_periods=window).mean()


def _rsi(close: pd.Series, period: int = 14) -> pd.Series:
    delta = close.diff()
    up = delta.clip(lower=0.0)
    down = -1 * delta.clip(upper=0.0)
    ma_up = up.ewm(com=period - 1, adjust=False).mean()
    ma_down = down.ewm(com=period - 1, adjust=False).mean()
    rs = ma_up / ma_down.replace(0, 1e-9)
    return 100.0 - (100.0 / (1.0 + rs))


# -----------------------------
# Public API
# -----------------------------

@dataclass
class Position:
    symbol: str
    qty: float
    avg_price: float


def _pick_field(model, candidates: Iterable[str]) -> Optional[str]:
    names = {f.name for f in model._meta.get_fields()}
    for n in candidates:
        if n in names:
            return n
    return None


def get_open_positions(positions: Optional[Iterable[Mapping[str, float]]] = None) -> Dict[str, Dict[str, float]]:
    """
    If positions is provided (iterable of {symbol, qty, avg_price}), compute P&L.
    If positions is None, pull from DB using OpenPosition + Stock (direct imports).
    """
    pos_list: List[Position] = []

    if positions is None and OpenPosition is not None:
        stock_fk = _pick_field(OpenPosition, ("stock", "instrument", "security", "asset")) or "stock"
        qty_field = _pick_field(OpenPosition, ("qty", "quantity", "shares", "units")) or "qty"
        price_field = _pick_field(OpenPosition, ("avg_price", "average_price", "avg_cost", "average_cost", "cost_basis", "price")) or "avg_price"
        sym_field = _pick_field(Stock, ("code", "name")) or "code"

        rows = OpenPosition.objects.values(qty_field, price_field, f"{stock_fk}__{sym_field}")
        for r in rows:
            code = r.get(f"{stock_fk}__{sym_field}")
            if not code:
                continue
            try:
                pos_list.append(
                    Position(
                        symbol=_to_yahoo(code),
                        qty=float(r.get(qty_field) or 0),
                        avg_price=float(r.get(price_field) or 0),
                    )
                )
            except Exception:
                continue
    else:
        for rec in positions or []:
            try:
                pos_list.append(
                    Position(
                        symbol=_to_yahoo(rec["symbol"]),
                        qty=float(rec["qty"]),
                        avg_price=float(rec["avg_price"]),
                    )
                )
            except Exception:
                continue

    out: Dict[str, Dict[str, float]] = {}
    if not pos_list:
        return out

    # Batch price lookups
    symbols = [p.symbol for p in pos_list]
    quotes = yf.download(" ".join(symbols), period="5d", interval="1d", auto_adjust=True, progress=False)

    last_prices: Dict[str, float] = {}
    if isinstance(quotes, pd.DataFrame) and not quotes.empty:
        if isinstance(quotes.columns, pd.MultiIndex):
            for sym in symbols:
                try:
                    px = float(quotes["Close"][sym].dropna().iloc[-1])
                    last_prices[sym] = px
                except Exception:
                    continue
        else:
            px = float(quotes["Close"].dropna().iloc[-1])
            last_prices[symbols[0]] = px

    for p in pos_list:
        last = last_prices.get(p.symbol)
        if last is None or math.isnan(last):
            continue
        pnl = (last - p.avg_price) * p.qty
        change_pct = ((last / p.avg_price) - 1.0) * 100.0 if p.avg_price else 0.0
        out[p.symbol] = {
            "qty": p.qty,
            "avg_price": round(p.avg_price, 6),
            "last": round(last, 6),
            "pnl": round(pnl, 2),
            "pnl_pct": round(change_pct, 3),
        }

    return out


def get_buys(
    *,
    max_count: int = 5,
    period: str = "6mo",
    interval: str = "1d",
    sma_fast: int = 50,
    sma_slow: int = 200,
    rsi_buy_below: Optional[float] = 60.0,
    **_ignore,  # absorb any legacy kwargs like 'exchanges' without effect
) -> Dict[str, Dict[str, float]]:
    """
    Screen ALL DB tickers from Stock and return one bucket:
      {"buy": {...}, "non_buy": {...}}
    All tickers are converted to Yahoo format by appending ".JO" when missing.
    """
    sym_field = _pick_field(Stock, ("code", "name")) or "code"
    codes = list(Stock.objects.values_list(sym_field, flat=True).distinct())
    symbols = [_to_yahoo(c) for c in codes if c]

    def analyse_symbol(sym: str) -> Tuple[bool, Dict[str, float]]:
        df = _download(sym, period=period, interval=interval)
        if df.empty:
            return False, {"reason": "no_data"}
        close = df["Close"].dropna()
        sfast = _sma(close, sma_fast)
        sslow = _sma(close, sma_slow)
        rsi = _rsi(close, 14)

        last = float(close.iloc[-1])
        f = float(sfast.iloc[-1]) if not math.isnan(sfast.iloc[-1]) else None
        s = float(sslow.iloc[-1]) if not math.isnan(sslow.iloc[-1]) else None
        r = float(rsi.iloc[-1]) if not math.isnan(rsi.iloc[-1]) else None

        trend_ok = f is not None and s is not None and last > f and f > s
        rsi_ok = True if rsi_buy_below is None else (r is not None and r < rsi_buy_below)

        payload = {
            "last": round(last, 6),
            "sma_fast": round(f, 6) if f is not None else None,
            "sma_slow": round(s, 6) if s is not None else None,
            "rsi": round(r, 3) if r is not None else None,
        }
        return (trend_ok and rsi_ok), payload

    def score(d: Dict[str, float]) -> float:
        sc = 0.0
        last = d.get("last"); f = d.get("sma_fast"); s = d.get("sma_slow"); r = d.get("rsi")
        if last and f and f > 0:
            sc += (last / f)
        if f and s and s > 0:
            sc += (f / s)
        if r is not None:
            sc += (100.0 - r) / 100.0
        return sc

    buy_bucket: Dict[str, Dict[str, float]] = {}
    non_bucket: Dict[str, Dict[str, float]] = {}

    for sym in symbols:
        try:
            ok, data = analyse_symbol(sym)
            if ok:
                buy_bucket[sym] = data | {"_score": score(data)}
            else:
                non_bucket[sym] = data
        except Exception as e:
            non_bucket[sym] = {"reason": f"error:{type(e).__name__}"}

    if max_count and buy_bucket:
        ranked = sorted(buy_bucket.items(), key=lambda kv: kv[1].get("_score", 0.0), reverse=True)[:max_count]
        buy_bucket = {k: {kk: vv for kk, vv in v.items() if kk != "_score"} for k, v in ranked}
    else:
        for v in buy_bucket.values():
            v.pop("_score", None)

    return {"buy": buy_bucket, "non_buy": non_bucket}