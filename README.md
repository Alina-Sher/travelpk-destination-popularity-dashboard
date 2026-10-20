# Destination Popularity Dashboard — Travel.pk

A Streamlit dashboard that ranks popular travel destinations across Pakistan, with filters for **Season** and **Traveler Type**.

> **Synthetic data notice.** The bundled dataset is an *illustrative, synthetic demonstration dataset*. It is **not** actual Travel.pk booking, customer, revenue or market data, and it was not scraped or collected from real customers. All values are assumptions.

## Task objective
Create a dashboard of top destinations with filters for season and traveler type, and state the data assumptions.

## Features
- Header, subtitle and data-transparency notice.
- Sidebar filters: **Season** (All Seasons, Spring, Summer, Autumn, Winter) and **Traveler type** (All Travelers, Solo, Couple, Family, Group), plus a **Reset Filters** button.
- KPI cards, all computed from the filtered data: destinations in results, top-ranked destination, total estimated trips, average popularity score.
- Interactive Plotly horizontal bar chart of the top 10 destinations (highest first; fewer if fewer match).
- Destination details table (destination, region, season, traveler type, popularity score, estimated trips) sorted by popularity.
- Two to three key insights computed from the filtered rows.
- "Data Sources & Assumptions" expandable panel.
- Friendly empty-state message if a filter combination has no results.

**Filter behavior:** both filters are combined with AND. "All" options apply no restriction. Chart, KPIs, insights and table all update together.

## Technology
Python 3.10+, Streamlit, Pandas, Plotly. No databases, APIs, keys or paid services; it works offline once dependencies are installed.

## Dataset
File: `data/destination_popularity.csv` (192 rows = 12 destinations × 4 seasons × 4 traveler types).

| Column | Meaning |
|---|---|
| destination | Destination name (Hunza, Skardu, Islamabad, Murree, Swat, Naran & Kaghan, Lahore, Karachi, Fairy Meadows, Gwadar, Chitral, Multan) |
| province_or_region | Province or region |
| season | Spring, Summer, Autumn, Winter |
| traveler_type | Solo, Couple, Family, Group |
| popularity_score | 0–100 index (see below) |
| estimated_trips | Assumed illustrative trip count for the segment |
| data_type | `synthetic_illustrative` on every row |

**How it was made:** each destination got a base trip level and hand-chosen season and traveler-type multipliers reflecting general assumptions (e.g., northern valleys peak in Summer, Murree and Gwadar are stronger in Winter, cities lean Family), plus small seeded random variation (±7%). These are the author's assumptions, not measurements.

## Popularity scoring
- Row level: `popularity_score = round(100 × estimated_trips ÷ max(estimated_trips in dataset), 1)`.
- Dashboard ranking: a destination's score for the selected filters is the **mean** `popularity_score` of its matching rows. Ties break on total estimated trips, then name.
- Every destination has all 16 segments, so this ordering equals ordering by total estimated trips.
- This is an unofficial, illustrative index, not a Travel.pk metric.

## Run locally
```bash
cd destination-popularity-dashboard
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
```
Opens at http://localhost:8501.

## Publish on GitHub
1. Create a new **public** repository on github.com (no README/.gitignore, since the project has them).
2. In the project folder:
```bash
git init
git add .
git commit -m "Add Destination Popularity Dashboard"
git branch -M main
git remote add origin https://github.com/<your-username>/destination-popularity-dashboard.git
git push -u origin main
```

## Deploy on Streamlit Community Cloud
1. Sign in at https://share.streamlit.io with GitHub and authorize access to the repository.
2. Click **Create app** → select the repository, branch `main`, main file `app.py`.
3. Under **Advanced settings**, choose Python 3.10 or newer.
4. Click **Deploy**. Add the resulting URL here only after it is actually live.

## Limitations and future work
- Synthetic values are assumptions, not market statistics; do not use them for business decisions.
- No price, capacity, events, multi-year trends or booking-channel information.
- Future version: replace the CSV with verified, privacy-compliant Travel.pk booking or search data (same columns), recompute `popularity_score` with the documented formula, and update the assumptions panel.
