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
from datetime import datetime, timezone, timedelta
import sys

# ── Ρυθμίσεις ─────────────────────────────────────────────────────────────────
URL = "https://hydro.bg/bg/t1.php?ime=&gr=data/&gn=tablRekiB2017"
STATION_ID = "51880"
CSV_FILE = "data/struma_flow.csv"
HEADERS_CSV = ["date", "time_utc", "Q_m3s", "station", "river", "location"]

HEADERS_HTTP = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "bg,en;q=0.9",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}

# ── Κύρια συνάρτηση scraping ───────────────────────────────────────────────────
def scrape_flow() -> dict | None:
    """Κατεβάζει τη σελίδα και εξάγει την παροχή Q για τον σταθμό 51880."""
    try:
        session = requests.Session()
        # Πρώτα φορτώνουμε την αρχική σελίδα για να πάρουμε cookies
        session.get("https://hydro.bg/", headers=HEADERS_HTTP, timeout=15)
        resp = session.get(URL, headers=HEADERS_HTTP, timeout=30)
        resp.raise_for_status()
        resp.encoding = "utf-8"
    except requests.RequestException as e:
        print(f"[ERROR] HTTP request failed: {e}", file=sys.stderr)
        return None

    soup = BeautifulSoup(resp.text, "html.parser")

    # Αναζήτηση γραμμής με station_id 51880
    target_row = None
    for row in soup.find_all("tr"):
        cells = row.find_all("td")
        if cells and cells[0].get_text(strip=True) == STATION_ID:
            target_row = cells
            break

    if target_row is None:
        print(f"[ERROR] Station {STATION_ID} not found in table.", file=sys.stderr)
        return None

    # Εξαγωγή τιμών (προσαρμόστε τον index αν αλλάξει η δομή)
    try:
        # Τυπική δομή: [ID, River, Location, ..., Q, ...]
        # Βρίσκουμε τη στήλη Q δυναμικά ή χρησιμοποιούμε γνωστή θέση
        texts = [c.get_text(strip=True) for c in target_row]
        print(f"[DEBUG] Row cells: {texts}")

        # Q [m3/s] — αναζήτηση αριθμητικής τιμής μετά τη θέση 3
        q_value = None
        river_name = texts[1] if len(texts) > 1 else "Струма"
        location   = texts[2] if len(texts) > 2 else "с. Марино поле"

        for cell_text in texts[3:]:
            cleaned = cell_text.replace(",", ".").replace(" ", "")
            try:
                q_value = float(cleaned)
                break  # Πρώτη αριθμητική τιμή = Q
            except ValueError:
                continue

        if q_value is None:
            print("[ERROR] Could not parse Q value.", file=sys.stderr)
            return None

    except (IndexError, ValueError) as e:
        print(f"[ERROR] Parsing error: {e}", file=sys.stderr)
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


# ── Αποθήκευση CSV ─────────────────────────────────────────────────────────────
def save_to_csv(record: dict) -> None:
    os.makedirs(os.path.dirname(CSV_FILE), exist_ok=True)
    file_exists = os.path.isfile(CSV_FILE)

    with open(CSV_FILE, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=HEADERS_CSV)
        if not file_exists:
            writer.writeheader()
        writer.writerow(record)

    print(f"[OK] Saved: {record['date']} {record['time_utc']} UTC — Q = {record['Q_m3s']} m³/s")


# ── Δημιουργία dashboard ───────────────────────────────────────────────────────
def generate_dashboard() -> None:
    """Διαβάζει το CSV και παράγει index.html με Chart.js."""
    if not os.path.isfile(CSV_FILE):
        print("[WARN] No CSV data yet for dashboard.")
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

    labels_js = str(dates)
    data_js   = str(flows)

    html = f"""<!DOCTYPE html>
<html lang="el">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Στρυμόνας — Παροχή (Marino Pole)</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
<style>
  body {{ font-family: Arial, sans-serif; background:#f5f7fa; margin:0; padding:20px; color:#333; }}
  h1   {{ color:#1a6496; margin-bottom:4px; }}
  .sub {{ color:#666; font-size:0.9em; margin-bottom:20px; }}
  .stats {{ display:flex; gap:16px; flex-wrap:wrap; margin-bottom:24px; }}
  .card  {{ background:#fff; border-radius:8px; padding:16px 24px; box-shadow:0 2px 6px rgba(0,0,0,0.1); min-width:140px; }}
  .card .val  {{ font-size:1.8em; font-weight:bold; color:#1a6496; }}
  .card .lbl  {{ font-size:0.8em; color:#888; margin-top:4px; }}
  .chart-box  {{ background:#fff; border-radius:8px; padding:20px; box-shadow:0 2px 6px rgba(0,0,0,0.1); }}
  footer      {{ margin-top:16px; font-size:0.75em; color:#aaa; text-align:center; }}
</style>
</head>
<body>
<h1>🌊 Ποταμός Στρυμόνας — Παροχή Q</h1>
<p class="sub">Σταθμός 51880 · с. Марино поле (είσοδος στην Ελλάδα) · Πηγή: hydro.bg</p>

<div class="stats">
  <div class="card"><div class="val">{latest_q:.3f}</div><div class="lbl">Τελευταία τιμή (m³/s)<br>{latest_date}</div></div>
  <div class="card"><div class="val">{max_q:.3f}</div><div class="lbl">Μέγιστη Q (m³/s)</div></div>
  <div class="card"><div class="val">{min_q:.3f}</div><div class="lbl">Ελάχιστη Q (m³/s)</div></div>
  <div class="card"><div class="val">{avg_q:.3f}</div><div class="lbl">Μέση Q (m³/s)</div></div>
  <div class="card"><div class="val">{len(dates)}</div><div class="lbl">Ημέρες καταγραφής</div></div>
</div>

<div class="chart-box">
  <canvas id="flowChart" height="90"></canvas>
</div>

<footer>Αυτόματη ενημέρωση κάθε ημέρα μέσω GitHub Actions · Τελευταία ενημέρωση: {latest_date}</footer>

<script>
const labels = {labels_js};
const data   = {data_js};
const ctx    = document.getElementById('flowChart').getContext('2d');
new Chart(ctx, {{
  type: 'line',
  data: {{
    labels: labels,
    datasets: [{{
      label: 'Q (m³/s)',
      data: data,
      borderColor: '#1a6496',
      backgroundColor: 'rgba(26,100,150,0.1)',
      borderWidth: 2,
      pointRadius: data.length > 60 ? 0 : 3,
      tension: 0.3,
      fill: true,
    }}]
  }},
  options: {{
    responsive: true,
    plugins: {{
      legend: {{ display: false }},
      title: {{
        display: true,
        text: 'Ημερήσια παροχή Στρυμόνα στο Marino Pole (m³/s)',
        font: {{ size: 14 }}
      }},
      tooltip: {{
        callbacks: {{
          label: ctx => `Q = ${{ctx.parsed.y.toFixed(3)}} m³/s`
        }}
      }}
    }},
    scales: {{
      x: {{ ticks: {{ maxTicksLimit: 12 }} }},
      y: {{
        beginAtZero: false,
        title: {{ display: true, text: 'Q (m³/s)' }}
      }}
    }}
  }}
}});
</script>
</body>
</html>"""

    with open("index.html", "w", encoding="utf-8") as f:
        f.write(html)
    print("[OK] Dashboard generated: index.html")


# ── Entry point ────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    record = scrape_flow()
    if record:
        save_to_csv(record)
        generate_dashboard()
    else:
        print("[FAIL] No data saved.")
        sys.exit(1)
