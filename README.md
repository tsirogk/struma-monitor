# Struma Flow Monitor

Αυτόματη ημερήσια καταγραφή παροχής Q (m3/s) του ποταμού Στρυμόνα.
Σταθμός 51880 — с. Марино поле (σημείο εισόδου στην Ελλάδα).
Πηγή: https://hydro.bg

## Αρχεία
- scrape_struma.py — scraper + dashboard generator
- data/struma_flow.csv — ιστορικά δεδομένα
- index.html — dashboard (GitHub Pages)
- .github/workflows/scrape.yml — cron 12:05 EET καθημερινά

## Τοπική εκτέλεση
    pip install requests beautifulsoup4
    python scrape_struma.py

## CSV δομή
    date, time_utc, Q_m3s, station, river, location
