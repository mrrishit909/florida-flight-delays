"""Step 5: aggregate the model into preview/data.json for the web preview (preview/index.html).

    ./venv/bin/python preview.py

Uses kpis() from check.py, so every number in the preview is computed exactly like the DAX measures.
One slice per Florida airport plus "ALL", so the airport picker never needs the 30 MB fact table.
"""
import json
from pathlib import Path

from check import CAUSES, kpis, load

OUT = Path(__file__).parent / "preview" / "data.json"


def r(x, n=6):  # 6 decimals so the page rounds once, like check.py (no 73.75 -> 73.8 double rounding)
    return None if x is None else round(float(x), n)


def slice_(f, dims):
    k = kpis(f)
    names = dims["DimCarrier"].set_index("CarrierCode")["CarrierName"]
    months = dims["DimDate"].drop_duplicates("MonthKey").set_index("MonthKey")["MonthLabel"]
    completed = f[(f["Cancelled"] == 0) & (f["Diverted"] == 0)]
    return {
        "kpi": {"flights": k["scheduled"], "otp": r(k["on_time_pct"]), "cancel": r(k["cancel_rate"]),
                "delay": r(k["avg_arr_delay"], 1), "late_delay": r(k["avg_delay_when_late"], 1)},
        "months": [{"m": months[mk], "otp": r(kpis(g)["on_time_pct"]), "cancel": r(kpis(g)["cancel_rate"])}
                   for mk, g in f.groupby(f["DateKey"] // 100)],
        # same noise rule for carriers: under 100 flights in this slice, leave it out
        "carriers": sorted([{"c": names[c], "n": len(g), "otp": r(kpis(g)["on_time_pct"])}
                            for c, g in f.groupby("CarrierCode") if len(g) >= 100], key=lambda d: -d["otp"]),
        "causes": sorted([{"c": CAUSES[c], "min": v} for c, v in k["cause_min"].items()], key=lambda d: -d["min"]),
        # hours with fewer than 100 completed flights are noise (e.g. one 00:xx flight); drop them
        "hours": [{"h": int(h), "n": len(g), "otp": r(1 - (g["ArrDel15"] == 1).mean())}
                  for h, g in completed.groupby("DepHour") if len(g) >= 100],
    }


if __name__ == "__main__":
    fact, dims = load()
    ap = dims["DimAirport"].set_index("AirportCode")["City"]
    order = fact["OriginCode"].value_counts().index  # busiest first
    data = {
        "period": "Aug 2025 – Jul 2026",
        "airports": [{"code": a, "city": ap[a]} for a in order],
        "slices": {"ALL": slice_(fact, dims), **{a: slice_(fact[fact["OriginCode"] == a], dims) for a in order}},
    }
    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text(json.dumps(data, separators=(",", ":")))
    print(f"wrote {OUT} ({OUT.stat().st_size / 1e3:.0f} KB, {len(order)} airports)")
