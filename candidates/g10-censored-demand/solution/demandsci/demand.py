"""Demand history: one row per trading store x SKU x day with unconstrained expected demand.

Sales are demand censored by shelf stock. Shoppers arrive through the trading day following the day-type traffic shape;
when the shelf is empty they leave. For each day we observe the in-stock intervals (opening stock and availability
events) and the units sold while in stock.

Model (per store-SKU-day d):
  arrivals ~ Poisson process with intensity lambda_d * g_daytype(hour)
  lambda_d = r_d * eps_d,   eps_d ~ Gamma(alpha_category, mean 1)   (demand shocks that also drive sell-outs)
  log r_d  = store x period + SKU + day of week + category x week + category x promotion

A sell-out is a stopping time of the arrival process, so the likelihood of the in-stock sales is Poisson with exposure
E_in = traffic share of trading hours the item was on shelf; integrating eps gives a negative binomial with offset
log E_in. The expected demand for the day given what was observed is
  units_sold + E[lambda_d | sales, E_in] * (E_full - E_in),  E[lambda_d | .] = (alpha + N) / (alpha / r_d + E_in).
Days on shelf for all trading hours have E_in = E_full, so expected demand equals sales.
"""
from __future__ import annotations

import sqlite3

import numpy as np
import pandas as pd
from scipy import optimize, sparse
from scipy.special import digamma, gammaln

from demandsci import warehouse

KEY = ["store_id", "sku_id", "date"]
DAYTYPES = ("weekday", "saturday", "sunday")


def _hour(t: str) -> float:
    return int(t[11:13]) + int(t[14:16]) / 60 + int(t[17:19]) / 3600


def in_stock_hours(days: pd.DataFrame, events: pd.DataFrame) -> tuple[np.ndarray, np.ndarray]:
    """(in-stock fraction, trading indicator) per row and clock hour, shape (n, 24)."""
    n = len(days)
    open_h = days["open_time"].str.slice(0, 2).astype(int).to_numpy()
    close_h = days["close_time"].str.slice(0, 2).astype(int).to_numpy()
    hours = np.arange(24)
    trading = ((hours[None, :] >= open_h[:, None]) & (hours[None, :] < close_h[:, None])).astype(float)
    instock = trading * (days["on_hand_open"].to_numpy() > 0)[:, None]
    pos = pd.Series(np.arange(n), index=pd.MultiIndex.from_frame(days[KEY]))
    ev = events.assign(date=events["event_time"].str.slice(0, 10), t=events["event_time"].map(_hour))
    ev = ev.sort_values(["store_id", "sku_id", "event_time"])
    for key, g in ev.groupby(KEY, sort=False):
        i = pos.get(key)
        if i is None:
            continue
        o, c = open_h[i], close_h[i]
        state, start, intervals = bool(days["on_hand_open"].iat[i] > 0), float(o), []
        for t, e in zip(g["t"], g["event_type"]):
            if t < o or t >= c:
                continue
            if e == "out_of_stock" and state:
                intervals.append((start, t))
                state = False
            elif e == "back_in_stock" and not state:
                start, state = t, True
        if state:
            intervals.append((start, float(c)))
        row = np.zeros(24)
        for a, b in intervals:
            for h in range(int(a), min(int(np.ceil(b)), 24)):
                row[h] += max(0.0, min(b, h + 1) - max(a, h))
        instock[i] = row
    return instock, trading


def traffic_profiles(days: pd.DataFrame, hourly: np.ndarray, full: np.ndarray, trading: np.ndarray) -> np.ndarray:
    """Hour-of-day traffic shape per day type from days on shelf all day with that day type's standard hours."""
    prof = np.zeros((len(DAYTYPES), 24))
    for j, dt in enumerate(DAYTYPES):
        m = (days["daytype"] == dt).to_numpy()
        std = days.loc[m, ["open_time", "close_time"]].value_counts().idxmax()
        sel = m & full & (days["open_time"] == std[0]).to_numpy() & (days["close_time"] == std[1]).to_numpy()
        counts = hourly[sel].sum(0) * trading[sel].max(0)
        prof[j] = counts / counts.sum()
    return prof


def _design(days: pd.DataFrame) -> tuple[sparse.csr_matrix, list[str]]:
    d = pd.to_datetime(days["date"])
    week = ((d - d.min()).dt.days // 7).astype(str)
    factors = {
        "store_period": days["store_id"] + "|" + days["period"],
        "sku": days["sku_id"],
        "dow": d.dt.dayofweek.astype(str),
        "cat_week": days["category"] + "|" + week,
        "cat_promo": np.where(days["promo"], days["category"], "none"),
    }
    cols = [sparse.csr_matrix(np.ones((len(days), 1)))]
    names = ["intercept"]
    for name, f in factors.items():
        codes, levels = pd.factorize(pd.Series(f), sort=True)
        if name == "cat_promo":
            keep = [i for i, lv in enumerate(levels) if lv != "none"]
        else:
            keep = list(range(1, len(levels)))
        remap = -np.ones(len(levels), int)
        remap[keep] = np.arange(len(keep))
        r = remap[codes]
        ok = r >= 0
        cols.append(sparse.csr_matrix((np.ones(ok.sum()), (np.flatnonzero(ok), r[ok])), shape=(len(days), len(keep))))
        names += [f"{name}={levels[i]}" for i in keep]
    return sparse.hstack(cols, format="csr"), names


def fit_negative_binomial(X: sparse.csr_matrix, y: np.ndarray, offset: np.ndarray, group: np.ndarray, n_groups: int):
    """Joint maximum likelihood of NB2 regression coefficients and a log dispersion per group."""
    p = X.shape[1]
    XT = X.T.tocsr()

    def nll(theta):
        beta, loga = theta[:p], theta[p:]
        eta = X @ beta + offset
        mu = np.exp(eta)
        a = np.exp(loga)[group]
        ll = gammaln(y + a) - gammaln(a) + a * (np.log(a) - np.log(a + mu)) + y * (eta - np.log(a + mu))
        g_eta = a * (y - mu) / (a + mu)
        g_loga = a * (digamma(y + a) - digamma(a) + np.log(a) - np.log(a + mu) + 1 - (y + a) / (a + mu))
        grad = np.concatenate([XT @ g_eta, np.bincount(group, weights=g_loga, minlength=n_groups)])
        return -ll.sum(), -grad

    theta0 = np.zeros(p + n_groups)
    theta0[0] = np.log(y.sum() / np.exp(offset).sum())
    theta0[p:] = np.log(3.0)
    res = optimize.minimize(nll, theta0, jac=True, method="L-BFGS-B",
                            options={"maxiter": 3000, "maxfun": 6000, "ftol": 1e-13, "gtol": 1e-6})
    return res.x[:p], np.exp(res.x[p:])


def build_history(con: sqlite3.Connection, days: pd.DataFrame) -> pd.DataFrame:
    inv = pd.read_sql_query("SELECT store_id, sku_id, date, on_hand_open FROM inventory_daily", con)
    days = days.merge(inv, on=KEY, how="left").sort_values(KEY).reset_index(drop=True)
    days["daytype"] = pd.to_datetime(days["date"]).dt.dayofweek.map(lambda w: "sunday" if w == 6 else "saturday" if w == 5 else "weekday")

    hs = warehouse.hourly_sales(con)
    pos = pd.Series(np.arange(len(days)), index=pd.MultiIndex.from_frame(days[KEY]))
    idx = pos.reindex(pd.MultiIndex.from_frame(hs[KEY])).to_numpy()
    ok = ~np.isnan(idx)
    hourly = np.zeros((len(days), 24))
    np.add.at(hourly, (idx[ok].astype(int), hs["hour"].to_numpy()[ok]), hs["units"].to_numpy()[ok])
    sold = hourly.sum(1)

    instock, trading = in_stock_hours(days, warehouse.availability_events(con))
    full = np.isclose(instock.sum(1), trading.sum(1), atol=1e-9)
    prof = traffic_profiles(days, hourly, full, trading)[days["daytype"].map({d: i for i, d in enumerate(DAYTYPES)}).to_numpy()]
    e_in = (prof * instock).sum(1)
    e_full = (prof * trading).sum(1)

    X, _ = _design(days)
    cat_codes, _cats = pd.factorize(days["category"], sort=True)
    fit_rows = e_in > 1e-9
    beta, alpha = fit_negative_binomial(X[fit_rows], sold[fit_rows], np.log(e_in[fit_rows]), cat_codes[fit_rows], len(_cats))
    rate = np.exp(X @ beta)
    a = alpha[cat_codes]
    post_mean = (a + sold) / (a / rate + e_in)
    expected = np.where(full, sold, sold + post_mean * np.maximum(e_full - e_in, 0.0))

    days["units_sold"] = sold.astype(int)
    days["expected_demand"] = expected
    days["lost_units"] = days["expected_demand"] - days["units_sold"]
    days["stockout_day"] = ~full
    return days
