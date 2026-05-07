#!/usr/bin/env python3
"""
Struma River Flow Scraper
Σταθμός: 51880 - Струма / с. Марино поле (είσοδος στην Ελλάδα)
Πηγή: https://hydro.bg/bg/t1.php?ime=&gr=data/&gn=tablRekiB2017
"""

import requests
from bs4 import BeautifulSoup
import csv
import os
from datetime import datetime, timezone
import sys

URL        = "https://hydro.bg/bg/t1.php?ime=&gr=data/&gn=tablRekiB2017"
STATION_ID = "51880"
CSV_FILE   = "data/struma_flow.csv"
HEADERS_CSV = ["date", "time_utc", "Q_m3s", "station", "river", "location"]

HEADERS_HTTP = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:125.0) "
        "Gecko/20100101 Firefox/125.0"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "bg-BG,bg;q=0.9,en-US;q=0.8,en;q=0.7",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "none",
    "Sec-Fetch-User": "?1",
    "DNT": "1",
}


def scrape_flow():
    try:
        session = requests.Session()
        # Πρώτη επίσκεψη στην αρχική σελίδα για cookies
        session.get("https://hydro.bg/", headers=HEADERS_HTTP, timeout=15)
        # Προσθήκη referer για να μοιάζει με πλοήγηση από Firefox
        headers_with_referer = {**HEADERS_HTTP, "Referer": "https://hydro.bg/"}
        resp = session.get(URL, headers=headers_with_referer, timeout=30)
        resp.raise_for_status()
        resp.encoding = "utf-8"
    except requests.RequestException as e:
        print(f"[ERROR] HTTP request failed: {e}", file=sys.stderr)
        return None

    soup = BeautifulSoup(resp.text, "html.parser")

    target_row = None
    for row in soup.find_all("tr"):
        cells = row.find_all("td")
        if cells and cells[0].get_text(strip=True) == STATION_ID:
            target_row = cells
            break

    if target_row is None:
        print(f"[ERROR] Station {STATION_ID} not found.", file=sys.stderr)
        return None

    texts      = [c.get_text(strip=True) for c in target_row]
    print(f"[DEBUG] Row cells: {texts}")

    river_name = texts[1] if len(texts) > 1 else "Струма"
    location   = texts[2] if len(texts) > 2 else "с. Марино поле"

    # 8η στήλη (index 7) = Q [m3/s]
    q_value = None
    try:
        cell_text = texts[7]
        q_value = float(cell_text.replace(",", ".").replace(" ", ""))
    except (IndexError, ValueError):
        # Fallback: πρώτη αριθμητική τιμή μετά τη στήλη 3
        for cell_text in texts[3:]:
            try:
                q_value = float(cell_text.replace(",", ".").replace(" ", ""))
                break
            except ValueError:
                continue

    if q_value is None:
        print("[ERROR] Could not parse Q value.", file=sys.stderr)
        return None

    now_utc = datetime.now(timezone.utc)
    return {
        "date":     now_utc.strftime("%Y-%m-%d"),
        "time_utc": now_utc.strftime("%H:%M"),
        "Q_m3s":    q_value,
        "station":  STATION_ID,
        "river":    river_name,
        "location": location,
    }


def save_to_csv(record):
    os.makedirs("data", exist_ok=True)
    file_exists = os.path.isfile(CSV_FILE)
    with open(CSV_FILE, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=HEADERS_CSV)
        if not file_exists:
            writer.writeheader()
        writer.writerow(record)
    print(f"[OK] {record['date']} {record['time_utc']} UTC — Q = {record['Q_m3s']} m3/s")


def generate_dashboard():
    if not os.path.isfile(CSV_FILE):
        return
    dates, flows = [], []
    with open(CSV_FILE, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            dates.append(row["date"])
            flows.append(float(row["Q_m3s"]))
    if not dates:
        return

    latest_q    = flows[-1]
    latest_date = dates[-1]
    max_q       = max(flows)
    min_q       = min(flows)
    avg_q       = sum(flows) / len(flows)

    html = f"""<!DOCTYPE html>
<html lang="el">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Στρυμόνας — Παροχή</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
<style>
  body  {{ font-family:Arial,sans-serif; background:#f5f7fa; margin:0; padding:20px; color:#333; }}
  h1    {{ color:#1a6496; }}
  .stats{{ display:flex; gap:16px; flex-wrap:wrap; margin-bottom:24px; }}
  .card {{ background:#fff; border-radius:8px; padding:16px 24px; box-shadow:0 2px 6px rgba(0,0,0,.1); }}
  .val  {{ font-size:1.8em; font-weight:bold; color:#1a6496; }}
  .lbl  {{ font-size:.8em; color:#888; margin-top:4px; }}
  .box  {{ background:#fff; border-radius:8px; padding:20px; box-shadow:0 2px 6px rgba(0,0,0,.1); }}
  footer{{ margin-top:16px; font-size:.75em; color:#aaa; text-align:center; }}
</style>
</head>
<body>
<h1>Ποταμός Στρυμόνας — Παροχή Q</h1>
<p>Σταθμός 51880 · с. Марино поле · Πηγή: hydro.bg</p>
<div class="stats">
  <div class="card"><div class="val">{latest_q:.3f}</div><div class="lbl">Τελευταία (m³/s)<br>{latest_date}</div></div>
  <div class="card"><div class="val">{max_q:.3f}</div><div class="lbl">Μέγιστη (m³/s)</div></div>
  <div class="card"><div class="val">{min_q:.3f}</div><div class="lbl">Ελάχιστη (m³/s)</div></div>
  <div class="card"><div class="val">{avg_q:.3f}</div><div class="lbl">Μέση (m³/s)</div></div>
  <div class="card"><div class="val">{len(dates)}</div><div class="lbl">Ημέρες</div></div>
</div>
<div class="box">
  <canvas id="chart" height="90"></canvas>
</div>
<footer>Αυτόματη ενημέρωση κάθε ημέρα μέσω Windows Task Scheduler + GitHub</footer>
<script>
new Chart(document.getElementById("chart"), {{
  type: "line",
  data: {{
    labels: {dates},
    datasets: [{{
      label: "Q (m³/s)",
      data: {flows},
      borderColor: "#1a6496",
      backgroundColor: "rgba(26,100,150,0.1)",
      borderWidth: 2,
      tension: 0.3,
      fill: true,
      pointRadius: {len(dates)} > 60 ? 0 : 3
    }}]
  }},
  options: {{
    responsive: true,
    plugins: {{
      title: {{ display: true, text: "Ημερήσια παροχή Στρυμόνα — Marino Pole (m³/s)" }}
    }},
    scales: {{
      x: {{ ticks: {{ maxTicksLimit: 12 }} }},
      y: {{ title: {{ display: true, text: "Q (m³/s)" }} }}
    }}
  }}
}});
</script>
</body>
</html>"""

    with open("index.html", "w", encoding="utf-8") as f:
        f.write(html)
    print("[OK] Dashboard: index.html")


if __name__ == "__main__":
    record = scrape_flow()
    if record:
        save_to_csv(record)
        generate_dashboard()
    else:
        sys.exit(1)
