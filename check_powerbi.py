"""Compare the Power BI results with check.py (pandas), value by value.

    ./venv/bin/python check_powerbi.py [folder]      (default: powerbi_web/)

The folder holds r1.tsv ... r5.tsv: the five verify.dax results, copied from DAX query view
(Results -> Copy -> Copy table, then pasted into a file). Full precision, so the tolerance is 1e-9.
"""
import csv, math, sys
from pathlib import Path
from check import kpis, load
S = Path(sys.argv[1] if len(sys.argv) > 1 else Path(__file__).parent / "powerbi_web")
fact, dims = load()
rows = lambda n: list(csv.DictReader(open(S / f"r{n}.tsv"), delimiter="\t"))
bad = []
def eq(label, got, want, tol=1e-9):
    got = float(got)
    if not math.isclose(got, want, rel_tol=tol, abs_tol=tol):
        bad.append(f"{label}: Power BI {got} vs pandas {want}")
k = kpis(fact); r = rows(1)[0]
for col, want in [("[Scheduled Flights]", k["scheduled"]), ("[Cancelled Flights]", k["cancelled"]), ("[Diverted Flights]", k["diverted"]),
                  ("[Completed Flights]", k["completed"]), ("[Late Arrivals]", k["late"]), ("[On-Time %]", k["on_time_pct"]),
                  ("[Cancellation Rate]", k["cancel_rate"]), ("[Avg Arrival Delay (min)]", k["avg_arr_delay"]),
                  ("[Avg Delay When Late (min)]", k["avg_delay_when_late"]), ("[Total Delay Min]", k["total_delay_min"]),
                  ("[Weather Share of Delay Min]", k["weather_share"]), ("[Weather Cancellations]", k["weather_cancellations"])]:
    eq(col, r[col], want)
r = rows(2)[0]
for col, c in [("[Late Aircraft Delay Min]", "LateAircraftDelay"), ("[Carrier Delay Min]", "CarrierDelay"), ("[NAS Delay Min]", "NASDelay"),
               ("[Weather Delay Min]", "WeatherDelay"), ("[Security Delay Min]", "SecurityDelay")]:
    eq(col, r[col], k["cause_min"][c])
fl = k["on_time_pct"]; n = 0
for r in rows(3):
    a = kpis(fact[fact.OriginCode == r["DimAirport[AirportCode]"]]); n += 1
    eq(r["DimAirport[AirportCode]"] + " flights", r["[Flights]"], a["scheduled"])
    eq(r["DimAirport[AirportCode]"] + " otp", r["[On-Time %]"], a["on_time_pct"])
    eq(r["DimAirport[AirportCode]"] + " cancel", r["[Cancellation Rate]"], a["cancel_rate"])
    eq(r["DimAirport[AirportCode]"] + " pts", r["[On-Time vs Florida (pts)]"], (a["on_time_pct"] - fl) * 100)
assert n == fact.OriginCode.nunique(), f"airports: {n}"
names = dims["DimCarrier"].set_index("CarrierName")["CarrierCode"]
ranked = sorted(((kpis(g)["on_time_pct"], c) for c, g in fact.groupby("CarrierCode")), reverse=True)
for r in rows(4):
    code = names[r["DimCarrier[CarrierName]"]]; a = kpis(fact[fact.CarrierCode == code])
    eq(code + " flights", r["[Flights]"], a["scheduled"]); eq(code + " otp", r["[On-Time %]"], a["on_time_pct"])
    eq(code + " rank", r["[Carrier On-Time Rank]"], [c for _, c in ranked].index(code) + 1)
for r in rows(5):
    a = kpis(fact[fact.DateKey // 100 == int(r["DimDate[MonthKey]"])])
    for col, want in [("[Flights]", a["scheduled"]), ("[On-Time %]", a["on_time_pct"]), ("[Cancellation Rate]", a["cancel_rate"]),
                      ("[Weather Cancellations]", a["weather_cancellations"])]:
        eq(r["DimDate[MonthKey]"] + " " + col, r[col], want)
checked = 12 + 5 + 4 * n + 3 * len(rows(4)) + 4 * len(rows(5))
print("\n".join(bad) if bad else f"ALL {checked} VALUES MATCH (Power BI web vs pandas, rel tol 1e-9)")
