"""Step 1: download 12 months of US flight on-time data from the Bureau of Transportation Statistics (BTS).

    ./venv/bin/python download.py

One zip per month (~30 MB each, ~245 MB unzipped) into data/raw/. Already-downloaded months are skipped.
The BTS server is slow per connection, so all months download in parallel.
"""
import ssl
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

MONTHS = [(2025, m) for m in range(8, 13)] + [(2026, m) for m in range(1, 8)]  # Aug 2025 - Jul 2026
URL = "https://transtats.bts.gov/PREZIP/On_Time_Reporting_Carrier_On_Time_Performance_1987_present_{y}_{m}.zip"
RAW = Path(__file__).parent / "data" / "raw"
# python.org Python on macOS ships without CA certs; the system bundle works
CTX = ssl.create_default_context(cafile="/etc/ssl/cert.pem" if Path("/etc/ssl/cert.pem").exists() else None)


def fetch(ym):
    y, m = ym
    out = RAW / f"ontime_{y}_{m}.zip"
    if out.exists():
        return f"have {out.name}"
    part = out.with_suffix(".part")
    with urllib.request.urlopen(URL.format(y=y, m=m), timeout=3600, context=CTX) as r, open(part, "wb") as f:
        while chunk := r.read(1 << 20):
            f.write(chunk)
    part.rename(out)  # only a finished download gets the .zip name
    return f"got  {out.name}"


if __name__ == "__main__":
    RAW.mkdir(parents=True, exist_ok=True)
    with ThreadPoolExecutor(len(MONTHS)) as pool:
        for line in pool.map(fetch, MONTHS):
            print(line)
