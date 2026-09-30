# Building the report in Power BI Desktop

Three routes. A and B use Power BI Desktop (Windows only) and steps 2–6 below; C is the browser.

- **Route A, with Claude Code on the Windows laptop (recommended).** You import the data and draw the visuals.
  Claude builds the model (relationships, date table, all measures) and checks every number. About 20 minutes of your time.
- **Route B, by hand.** You do every step. About 30 minutes.

## Route C, in the browser (what was actually done, on a free USF account)
No Windows needed. The model part worked at app.powerbi.com; data refresh is blocked on a free license, so nothing may
depend on it.
1. Create → Get Data → drag `FactFlights.csv` into Upload file (it lands in your OneDrive). In the editor: Get data →
   Upload → `DimAirport.csv`. Rename the queries, then **Create a report ▾ → Create semantic model only**.
2. In the model editor (Editing mode): **New table** three times: `DimCarrier` and `DimCancelReason` as `DATATABLE`,
   `DimDate` as `ADDCOLUMNS(CALENDAR(...))` (same columns as `DimDate.csv`).
3. **TMDL view**: paste a `createOrReplace` script with the five relationships (`fact_dest` has `isActive: false`), Apply;
   then one with `ref table FactFlights` + the 22 measures and their `formatString`s, Apply.
4. Gotcha: relationships added by script "need to be recalculated" and Refresh needs a paid license. Re-committing the
   DimDate formula (select it, paste the same formula into the formula bar, Enter) recalculated the model.
5. **DAX query view**: paste `verify.dax`, Run; for each of the 5 results use Copy → Copy table, save as
   `powerbi_web/r1.tsv` … `r5.tsv`, then `./venv/bin/python check_powerbi.py` (all 184 values matched).
6. MonthLabel → Advanced → Sort by column → MonthKey. Then **New report** and build step 6's page.

## Route A setup (once per laptop)

1. Install **Power BI Desktop** (free, Microsoft Store), **Node.js LTS** (nodejs.org) and **Git for Windows**
   (git-scm.com).
2. Install **Claude Code**: follow https://code.claude.com/docs/en/setup (a one-line PowerShell command), then run
   `claude` once to sign in.
3. Read the license for Microsoft's Power BI Modeling MCP server (https://github.com/microsoft/powerbi-modeling-mcp).
   If you agree, run `setx PBI_MODELING_MCP_ACCEPT_EULA true` in PowerShell and open a new PowerShell window.
4. Get the project:
   ```
   git clone https://github.com/mrrishit909/florida-flight-delays
   cd florida-flight-delays
   claude
   ```
   Approve the `powerbi-modeling` server when Claude Code asks. It comes from `.mcp.json` in this repo.

Then do **step 2** yourself, save as `FloridaFlightDelays.pbix` in the repo folder, and leave the file open.
Tell Claude: *"Connect to FloridaFlightDelays in Power BI Desktop and do steps 3–5 of BUILD_IN_POWERBI.md."*
When it reports that every number matches, do **step 6** yourself; Claude can't create visuals. Then ask it to commit and push.

## 1. Get the data (Route B)
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
Open **DAX query view**, paste `verify.dax`, and run it. Every result must match `expected_values.md` (e.g. On-Time %
0.7549, TPA 78.3%, Envoy Air rank 1). If anything differs, the usual causes are a blank that turned into 0 in step 2, or
the DestCode relationship left active.

## 6. Report page (mirror of the web preview)
- Slicer: DimAirport[AirportCode] (filter the slicer to IsFlorida = 1), plus DimDate[MonthLabel].
- Cards: Scheduled Flights, On-Time %, Cancellation Rate, Avg Arrival Delay (min); On-Time vs Florida (pts) as a subtitle.
- Line chart: MonthLabel × On-Time % and On-Time % (All Florida).
- Column chart: FactFlights[DepHour] × On-Time %.
- Bar chart: DimCarrier[CarrierName] × On-Time %, sorted descending (tooltip: Scheduled Flights, Carrier On-Time Rank).
- Bar chart: the five cause measures (Carrier / Weather / NAS / Security / Late Aircraft Delay Min).
- Table: DimAirport[AirportCode], City, Scheduled Flights, On-Time %, Cancellation Rate.

## Done means
- [ ] Every `verify.dax` result matches `expected_values.md`.
- [ ] `FloridaFlightDelays.pbix` and `screenshots/report.png` (Win+Shift+S, save the image) are committed and pushed;
      each file is under 49 MB.
- [ ] The website notes that say ".pbix pending" get updated (on the Mac: ask Claude to refresh the case study).
