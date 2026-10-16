"""Excess and aging inventory.

Excess answers "what will not sell through in time?": stock against forward demand, in four
tiers. Aging answers a different question, "what has been sitting too long?": stock that no
receipt inside the aging window can account for. The two are easy to mix up, so they are
separate functions with separate outputs.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from .config import INVENTORY, InventoryConfig

TIERS = ("normal", "surplus", "excess", "over_excess")


def demand_by_month(demand: pd.DataFrame, as_of: pd.Timestamp, cfg: InventoryConfig = INVENTORY,
                    fold_past_due: bool = True) -> pd.DataFrame:
    """Units of demand per item for each month from `as_of`, one column per month offset.

    A line dated before `as_of` is either still owed or noise. Confirmed orders are still owed:
    folded into the current month. Everything else past due (old requirements, stale plans) is
    dropped. With `fold_past_due=False` every past-due line is dropped: the date-filter bug.
    """
    if demand.empty:
        return pd.DataFrame(0, index=pd.Index([], name="item"), columns=range(cfg.horizon_months))
    d = demand.copy()
    d["offset"] = ((d["date"].dt.year - as_of.year) * 12 + d["date"].dt.month - as_of.month).astype(int)
    owed = d["kind"].isin(cfg.fold_past_due) if fold_past_due else pd.Series(False, index=d.index)
    d = d[(d["offset"] >= 0) | owed]
    d["offset"] = d["offset"].clip(lower=0)
    d = d[d["offset"] < cfg.horizon_months]
    table = d.pivot_table(index="item", columns="offset", values="units", aggfunc="sum", fill_value=0)
    return table.reindex(columns=range(cfg.horizon_months), fill_value=0)


def excess(stock: pd.DataFrame, demand: pd.DataFrame, as_of: pd.Timestamp,
           cfg: InventoryConfig = INVENTORY, fold_past_due: bool = True) -> pd.DataFrame:
    """Four tiers per item, in units and dollars. The tiers always add up to on-hand stock.

        over_excess = stock beyond everything the next 12 months will use
        normal      = what the next 3 months will use
        surplus     = what months 4-6 will use
        excess      = the rest
    """
    by_month = demand_by_month(demand, as_of, cfg, fold_past_due).reindex(stock["item"], fill_value=0)
    near = by_month.iloc[:, :cfg.normal_months].sum(axis=1).to_numpy()
    mid = by_month.iloc[:, cfg.normal_months:cfg.surplus_months].sum(axis=1).to_numpy()
    year = by_month.sum(axis=1).to_numpy()
    on_hand = stock["on_hand"].to_numpy(dtype=float)

    over = np.maximum(0.0, on_hand - year)
    normal = np.minimum(on_hand - over, near)
    surplus = np.minimum(on_hand - over - normal, mid)
    exc = on_hand - over - normal - surplus

    out = stock[["item", "lifecycle", "on_hand", "unit_cost"]].copy()
    for name, units in zip(TIERS, (normal, surplus, exc, over)):
        out[name] = units
    out["total_excess"] = out["excess"] + out["over_excess"]
    out["excess_value"] = out["total_excess"] * out["unit_cost"]
    out["stock_value"] = out["on_hand"] * out["unit_cost"]
    return out


def summary(tiers: pd.DataFrame) -> pd.Series:
    """Dollars by tier, and the excess share of stock. Report dollars first: the share rises
    whenever healthy stock ships, even while excess dollars fall."""
    dollars = {t: float((tiers[t] * tiers["unit_cost"]).sum()) for t in TIERS}
    dollars["total_excess"] = dollars["excess"] + dollars["over_excess"]
    dollars["stock"] = float(tiers["stock_value"].sum())
    dollars["excess_share"] = dollars["total_excess"] / dollars["stock"]
    return pd.Series(dollars)


def aged(tiers: pd.DataFrame, receipts: pd.DataFrame, as_of: pd.Timestamp,
         cfg: InventoryConfig = INVENTORY) -> pd.DataFrame:
    """Stock older than the aging window.

    aged_units = excess units that the receipts inside the window cannot account for. An item
    is on the write-off list only if it also has not been received inside the window at all:
    stock that was bought again last year is an over-buy, not dead stock.
    """
    cutoff = as_of - pd.DateOffset(years=cfg.aging_years)
    recent = receipts[receipts["date"] >= cutoff].groupby("item")["units"].sum()
    last = receipts.groupby("item")["date"].max()
    out = tiers[["item", "lifecycle", "total_excess", "unit_cost"]].copy()
    out["received_in_window"] = out["item"].map(recent).fillna(0.0)
    out["last_receipt"] = out["item"].map(last)
    out["aged_units"] = np.maximum(0.0, out["total_excess"] - out["received_in_window"])
    out["aged_value"] = out["aged_units"] * out["unit_cost"]
    out["write_off_list"] = (out["aged_units"] > 0) & (out["last_receipt"].isna() | (out["last_receipt"] < cutoff))
    return out[out["aged_units"] > 0].sort_values("aged_value", ascending=False).reset_index(drop=True)
