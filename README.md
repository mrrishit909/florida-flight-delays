# Florida Flight Delays (Power BI)

How reliable are flights out of Florida, and why are they late? A year of US DOT flight data (Aug 2025 – Jul 2026,
635,459 departures from 20 Florida airports) modeled as a Power BI star schema with DAX measures.

**Web preview of the dashboard:** https://mrrishit909.github.io/projects/florida-flight-delays/preview/
**Build log:** https://mrrishit909.github.io/projects/florida-flight-delays/

## What's here

| Step | Files | What it does |
|---|---|---|
| 1 | `download.py` | downloads 12 monthly on-time files from BTS (~360 MB of zips, not committed) |
| 2 | `etl.py` → `model/*.csv` | keeps Florida departures, builds 1 fact + 4 dimension tables |
| 3 | `model.md`, `measures.dax` | relationships and every measure's definition (numerator, denominator, exclusions) |
| 4 | `check.py` → `expected_values.md` | integrity asserts + the value every measure must show in Power BI |
| 5 | `preview.py`, `preview/` | web version of the report, computed with the same measure code |
| 6 | `BUILD_IN_POWERBI.md` | step-by-step build of the .pbix in Power BI Desktop |

## Run it

```
python3 -m venv venv && ./venv/bin/pip install -r requirements.txt
./venv/bin/python download.py     # ~5 min, parallel
./venv/bin/python etl.py          # ~15 s
./venv/bin/python check.py        # asserts + expected_values.md
./venv/bin/python preview.py      # preview/data.json
```

## Headline findings

- **75.5%** of completed flights arrived on time (within 15 minutes); **1.8%** were cancelled.
- **Time of day matters most:** 92% on time for 6 a.m. departures versus 63% for 8 p.m. ones.
- **Late-arriving aircraft** cause 42.5% of all delay minutes. Weather directly causes 5.9% of delay minutes, but it
  accounts for 59% of cancellations (most of them January through March).
- **Tampa (TPA)** beats the Florida average by 2.9 points; Fort Lauderdale (FLL) trails it by 4.7.

## Data

US Bureau of Transportation Statistics, *Reporting Carrier On-Time Performance (1987–present)*,
https://www.transtats.bts.gov/. Public domain. Covers carriers with at least 0.5% of US domestic passenger revenue.

## Not done yet

- The `.pbix` itself: Power BI Desktop is Windows-only and this was built on a Mac. Everything it needs (model, measures,
  expected values, build guide) is here; screenshots get added once it is built.
- No year-over-year comparison (one year of data).
