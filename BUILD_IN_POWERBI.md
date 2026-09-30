# Building the report in Power BI Desktop

Power BI Desktop runs on Windows only (a USF lab PC or a Windows VM works). About 30 minutes.

## 1. Get the data
Download this repo (Code → Download ZIP) and unzip it. Everything needed is in `model/`.

## 2. Import the five tables
Home → Get data → Text/CSV, once per file in `model/`: `FactFlights`, `DimDate`, `DimCarrier`, `DimAirport`,
`DimCancelReason`. Choose **Transform Data** for each and check the types:

| Column | Type |
|---|---|
| DimDate[Date], DimDate[MonthStart] | Date |
| all `*Key` columns, DepHour, DepDelay, ArrDelay, ArrDel15, Cancelled, Diverted, Distance, the 5 `*Delay` cause columns | Whole number |
| codes and names | Text |

Blank cells in ArrDelay / ArrDel15 / the cause columns must stay **blank (null)**, not 0. The measures depend on it.
Close & Apply.

## 3. Relationships (Model view)
Delete anything Power BI auto-detected, then create:

| From (many) | To (one) | Active |
|---|---|---|
| FactFlights[DateKey] | DimDate[DateKey] | yes |
| FactFlights[CarrierCode] | DimCarrier[CarrierCode] | yes |
| FactFlights[OriginCode] | DimAirport[AirportCode] | yes |
| FactFlights[DestCode] | DimAirport[AirportCode] | **no** (used by `Flights To Destination`) |
| FactFlights[CancelCode] | DimCancelReason[CancelCode] | yes |

All single cross-filter direction. Then:
- DimDate → Mark as date table → `Date`.
- DimDate[MonthLabel] → Sort by column → `MonthKey`.
- Hide every key column on FactFlights from report view.

## 4. Measures
Create a new measure on FactFlights for each block in `measures.dax` (copy/paste). Set formats:
On-Time %, Cancellation Rate, On-Time % (All Florida) and Weather Share of Delay Min = Percentage, 1 decimal.

## 5. Check the numbers before designing anything
Put each measure on a card and compare with `expected_values.md`. Then add a DimAirport[AirportCode] slicer and
compare a few airports (e.g. TPA 78.3% on time). If anything differs, the usual cause is a blank that turned into 0
in step 2.

## 6. Report page (mirror of the web preview)
- Slicer: DimAirport[AirportCode] (filter the slicer to IsFlorida = 1), plus DimDate[MonthLabel].
- Cards: Scheduled Flights, On-Time %, Cancellation Rate, Avg Arrival Delay (min); On-Time vs Florida (pts) as a subtitle.
- Line chart: MonthLabel × On-Time % and On-Time % (All Florida).
- Column chart: FactFlights[DepHour] × On-Time %.
- Bar chart: DimCarrier[CarrierName] × On-Time %, sorted descending (tooltip: Scheduled Flights, Carrier On-Time Rank).
- Bar chart: the five cause measures (Carrier / Weather / NAS / Security / Late Aircraft Delay Min).
- Table: DimAirport[AirportCode], City, Scheduled Flights, On-Time %, Cancellation Rate.

Save as `FloridaFlightDelays.pbix` in the repo root, take a screenshot of the page into `screenshots/`, and commit both.
