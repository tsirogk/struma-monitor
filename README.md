# 🌊 Struma Flow Monitor

Αυτόματη ημερήσια καταγραφή της παροχής Q (m³/s) του ποταμού **Στρυμόνα**  
στον σταθμό **51880 — с. Марино поле** (σημείο εισόδου στην Ελλάδα).

**Πηγή δεδομένων:** [hydro.bg](https://hydro.bg/bg/t1.php?ime=&gr=data/&gn=tablRekiB2017)

---

## Αρχεία

| Αρχείο | Περιγραφή |
|--------|-----------|
| `scrape_struma.py` | Python scraper + dashboard generator |
| `data/struma_flow.csv` | Ιστορικά δεδομένα (αυτόματη συσσώρευση) |
| `index.html` | Dashboard με Chart.js (GitHub Pages) |
| `.github/workflows/scrape.yml` | GitHub Action — τρέχει κάθε μέρα 12:05 EET |

---

## Ρύθμιση (μία φορά)

### 1. Δημιουργία repository

```bash
git init struma-monitor
cd struma-monitor
# Αντιγράψτε όλα τα αρχεία εδώ
git add .
git commit -m "init: Struma flow monitor"
git remote add origin https://github.com/YOUR_USERNAME/struma-monitor.git
git push -u origin main
```

### 2. Ενεργοποίηση GitHub Pages

- Settings → Pages → Source: **Deploy from branch** → `main` → `/` (root)
- Dashboard διαθέσιμο στο: `https://YOUR_USERNAME.github.io/struma-monitor/`

### 3. Έλεγχος workflow

- Actions tab → **Struma Flow Daily Scraper** → **Run workflow** (χειροκίνητη δοκιμή)

---

## Τοπική εκτέλεση

```bash
pip install requests beautifulsoup4
python scrape_struma.py
```

---

## Δομή CSV

```
date,time_utc,Q_m3s,station,river,location
2026-05-04,10:05,77.282,51880,Струма,с. Марино поле
```

---

## Σημειώσεις

- Αν η hydro.bg αλλάξει τη δομή του HTML πίνακα, ενημερώστε τον index στήλης Q στο `scrape_struma.py`
- Για debug: ελέγξτε το `[DEBUG] Row cells:` output στα GitHub Actions logs
- Ώρες UTC: το cron τρέχει 10:05 UTC → 12:05 EET (χειμώνας) / 13:05 EEST (καλοκαίρι)

---

## Επέκταση ιδέες

- Αποστολή email/Telegram alert αν Q > threshold (πλημμύρα)
- Συσχέτιση με βροχόπτωση (ERA5 reanalysis)
- Export σε QGIS για χαρτογράφηση υδρολογικής λεκάνης
