# Data model

Star schema, one fact table and four dimensions, all in `model/` as CSV.
Scope: every scheduled flight that **departs a Florida airport**, Aug 2025 – Jul 2026 (BTS reporting carriers).

```
                DimDate (DateKey)
                     │ 1
                     │
DimCarrier ──1───* FactFlights *───1── DimAirport   (OriginCode, active)
(CarrierCode)        │  *  └────────*── DimAirport   (DestCode, INACTIVE - used via USERELATIONSHIP)
                     │
                     1
              DimCancelReason (CancelCode)
```

All relationships: many-to-one, single direction (dimension filters fact).

## Tables

| Table | Grain | Key | Notes |
|---|---|---|---|
| FactFlights | one scheduled flight | – | 635,459 rows |
| DimDate | one day | DateKey (yyyymmdd) | mark as date table on `Date`; sort `MonthLabel` by `MonthKey` |
| DimCarrier | one airline | CarrierCode | 13 carriers |
| DimAirport | one airport | AirportCode | origins (Florida) + all destinations; `IsFlorida` flag |
| DimCancelReason | one BTS code | CancelCode | A Carrier, B Weather, C National Air System, D Security |

### FactFlights columns

| Column | Meaning |
|---|---|
| DateKey, CarrierCode, OriginCode, DestCode, CancelCode | foreign keys |
| DepHour | scheduled departure hour, 0–23 |
| DepDelay | departure delay, minutes (negative = early) |
| ArrDelay | arrival delay, minutes (negative = early); **blank for cancelled and diverted flights** |
| ArrDel15 | 1 = arrived 15+ minutes late, 0 = on time; **blank for cancelled and diverted flights** |
| Cancelled, Diverted | 0/1 |
| Distance | miles |
| CarrierDelay, WeatherDelay, NASDelay, SecurityDelay, LateAircraftDelay | minutes of a late arrival's delay by cause; **filled only when ArrDel15 = 1** and they add up to ArrDelay |

## Measure definitions

Each measure is defined once here. `measures.dax` implements it in DAX, and `check.py` (`kpis()`) implements the same
definition in pandas to produce `expected_values.md`.

| Measure | Numerator | Denominator | Treatment of cancelled / diverted |
|---|---|---|---|
| Scheduled Flights | rows | – | included |
| Completed Flights | Scheduled − Cancelled − Diverted | – | excluded by definition |
| Late Arrivals | rows with ArrDel15 = 1 | – | can't be late (blank) |
| **On-Time %** | Completed − Late | **Completed** | excluded (DOT convention) |
| **Cancellation Rate** | Cancelled | **Scheduled** | cancelled are the numerator |
| Avg Arrival Delay (min) | sum ArrDelay | completed flights (non-blank ArrDelay) | excluded; early arrivals count as negative |
| Avg Delay When Late (min) | sum ArrDelay where ArrDel15 = 1 | late arrivals | excluded |
| Cause minutes (5 measures) | sum of that cause column | – | only late arrivals have causes |
| Weather Share of Delay Min | Weather minutes | Total delay minutes (5 causes) | – |
| Weather Cancellations | Cancelled with CancelCode = B | – | – |
| On-Time % (All Florida) | On-Time % with DimAirport filters removed | | benchmark for the selected airport |
| On-Time vs Florida (pts) | (On-Time % − On-Time % (All Florida)) × 100 | | |
| Carrier On-Time Rank | RANKX over the selected carriers by On-Time % | | 1 = best |
| Flights To Destination | Scheduled Flights through the inactive DestCode relationship | | for "where do Florida flights go" |

**Why the denominators differ:** a cancelled flight never arrives, so counting it as "late" or "on time" would be
wrong. On-Time % therefore only looks at flights that arrived, and cancellations get their own rate over everything
that was scheduled. Diverted flights (landed somewhere else) are excluded from both punctuality measures, matching the
US DOT Air Travel Consumer Report.
