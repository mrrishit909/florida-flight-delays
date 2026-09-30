"""Step 2: turn the raw BTS files into a star schema that Power BI imports directly.

    ./venv/bin/python etl.py

Keeps only flights that DEPART a Florida airport (Aug 2025 - Jul 2026) and writes to model/:

    FactFlights.csv        one row per scheduled flight
    DimDate.csv            one row per day
    DimCarrier.csv         airline code -> name
    DimAirport.csv         every origin and destination airport
    DimCancelReason.csv    BTS cancellation codes A-D
"""
import zipfile
from pathlib import Path

import pandas as pd

HERE = Path(__file__).parent
RAW, OUT = HERE / "data" / "raw", HERE / "model"

CAUSES = ["CarrierDelay", "WeatherDelay", "NASDelay", "SecurityDelay", "LateAircraftDelay"]
COLS = ["FlightDate", "Reporting_Airline", "Origin", "OriginCityName", "OriginState", "OriginStateName",
        "Dest", "DestCityName", "DestState", "DestStateName", "CRSDepTime", "DepDelay", "ArrDelay", "ArrDel15",
        "Cancelled", "CancellationCode", "Diverted", "Distance"] + CAUSES

# BTS reporting-carrier codes (the 13 that fly in this period, plus a few that sometimes report)
CARRIERS = {
    "AA": "American Airlines", "AS": "Alaska Airlines", "B6": "JetBlue", "DL": "Delta Air Lines",
    "F9": "Frontier Airlines", "G4": "Allegiant Air", "HA": "Hawaiian Airlines", "MQ": "Envoy Air",
    "NK": "Spirit Airlines", "OH": "PSA Airlines", "OO": "SkyWest Airlines", "UA": "United Airlines",
    "WN": "Southwest Airlines", "YX": "Republic Airways", "9E": "Endeavor Air",
}
CANCEL_REASONS = {"A": "Carrier", "B": "Weather", "C": "National Air System", "D": "Security"}


def read_month(path):
    with zipfile.ZipFile(path) as z:
        name = next(n for n in z.namelist() if n.endswith(".csv"))
        df = pd.read_csv(z.open(name), usecols=COLS, dtype={"CancellationCode": "string"})
    return df[df["OriginState"] == "FL"]


def build():
    files = sorted(RAW.glob("ontime_*.zip"))
    assert len(files) == 12, f"expected 12 monthly zips in {RAW}, found {len(files)} (run download.py)"
    raw = pd.concat([read_month(f) for f in files], ignore_index=True)

    unknown = set(raw["Reporting_Airline"]) - set(CARRIERS)
    assert not unknown, f"add these carrier codes to CARRIERS: {unknown}"

    date = pd.to_datetime(raw["FlightDate"])
    fact = pd.DataFrame({
        "DateKey": date.dt.strftime("%Y%m%d").astype(int),
        "CarrierCode": raw["Reporting_Airline"],
        "OriginCode": raw["Origin"],
        "DestCode": raw["Dest"],
        "DepHour": (raw["CRSDepTime"] // 100 % 24).astype(int),  # scheduled departure hour; 2400 -> 0
        "DepDelay": raw["DepDelay"].round().astype("Int64"),       # minutes, negative = early
        "ArrDelay": raw["ArrDelay"].round().astype("Int64"),       # blank when cancelled or diverted
        "ArrDel15": raw["ArrDel15"].astype("Int64"),               # 1 = arrived 15+ min late
        "Cancelled": raw["Cancelled"].astype(int),
        "CancelCode": raw["CancellationCode"],
        "Diverted": raw["Diverted"].astype(int),
        "Distance": raw["Distance"].astype(int),
        **{c: raw[c].round().astype("Int64") for c in CAUSES},     # filled only for late arrivals
    })

    days = pd.date_range(date.min(), date.max(), freq="D")
    dim_date = pd.DataFrame({
        "DateKey": days.strftime("%Y%m%d").astype(int),
        "Date": days.strftime("%Y-%m-%d"),
        "Year": days.year,
        "MonthKey": days.year * 100 + days.month,  # sort MonthLabel by this in Power BI
        "MonthLabel": days.strftime("%b %Y"),
        "MonthStart": days.to_period("M").start_time.strftime("%Y-%m-%d"),
        "DayOfWeekNum": days.dayofweek + 1,        # 1 = Monday
        "DayName": days.strftime("%A"),
        "IsWeekend": (days.dayofweek >= 5).astype(int),
    })

    origin = raw[["Origin", "OriginCityName", "OriginState", "OriginStateName"]].set_axis(
        ["AirportCode", "City", "State", "StateName"], axis=1)
    dest = raw[["Dest", "DestCityName", "DestState", "DestStateName"]].set_axis(
        ["AirportCode", "City", "State", "StateName"], axis=1)
    dim_airport = pd.concat([origin, dest]).drop_duplicates("AirportCode").sort_values("AirportCode")
    dim_airport["IsFlorida"] = (dim_airport["State"] == "FL").astype(int)

    dim_carrier = pd.DataFrame(sorted(CARRIERS.items()), columns=["CarrierCode", "CarrierName"])
    dim_carrier = dim_carrier[dim_carrier["CarrierCode"].isin(fact["CarrierCode"])]
    dim_cancel = pd.DataFrame(sorted(CANCEL_REASONS.items()), columns=["CancelCode", "CancelReason"])

    OUT.mkdir(exist_ok=True)
    for name, df in [("FactFlights", fact), ("DimDate", dim_date), ("DimCarrier", dim_carrier),
                     ("DimAirport", dim_airport), ("DimCancelReason", dim_cancel)]:
        df.to_csv(OUT / f"{name}.csv", index=False)
        print(f"{name:16} {len(df):>8,} rows  {(OUT / f'{name}.csv').stat().st_size / 1e6:6.1f} MB")


if __name__ == "__main__":
    build()
