"""Market-week panel: the reporting grain in docs/metric_definitions.md."""
import pandas as pd

from northline_eval import warehouse


def market_week(con):
    o = warehouse.orders(con)
    ch = warehouse.courier_hours(con)
    g = o.groupby(["market_id", "week_start"], as_index=False).agg(
        orders=("order_id", "size"), late_orders=("is_late", "sum"))
    g["late_rate_pct"] = g["late_orders"] / g["orders"] * 100.0
    boost = (o.assign(b=(o["arm"] == "boost").astype(int))
               .groupby(["market_id", "week_start"], as_index=False)["b"].mean()
               .rename(columns={"b": "boost_share"}))
    hrs = ch.groupby(["market_id", "week_start"], as_index=False)["courier_hours"].sum()
    g = g.merge(boost, on=["market_id", "week_start"], how="left") \
         .merge(hrs, on=["market_id", "week_start"], how="left")
    g["boost_share"] = g["boost_share"].fillna(0.0)
    g["courier_hours"] = g["courier_hours"].fillna(0.0)
    return g.sort_values(["market_id", "week_start"]).reset_index(drop=True)


def phase2_markets(con):
    c = warehouse.config(con)
    p2 = c[c["phase"] == "phase2_order_randomised"]
    return (sorted(p2[p2["status"] == "running"]["market_id"].unique().tolist()),
            sorted(p2[p2["status"] == "holdout"]["market_id"].unique().tolist()),
            sorted(p2["week_start"].unique().tolist()))
