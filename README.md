# Worcester Community Development Dashboard

Interactive Streamlit dashboard combining OpenStreetMap community resource
locations with U.S. Census ACS unemployment data to help stakeholders
prioritize areas for community development investment in Worcester, MA.

## Project files

| File | Purpose |
|---|---|
| `prepare_data.py` | Run ONCE locally to download/clean data and write the `data/` files |
| `app.py` | The Streamlit dashboard (reads only the files in `data/`) |
| `requirements.txt` | Libraries Streamlit Cloud installs at deployment |
| `data/` | Generated data files (commit these to the repo before deploying) |

## Step 1 — Build the data files (local machine)

```bash
pip install osmnx pygris requests geopandas pandas shapely
python prepare_data.py
```

This writes `data/worcester_boundary.geojson`, `data/resources.geojson`,
and `data/zips.geojson`, and prints a preview of the per-ZIP metrics.

## Step 2 — Test locally

```bash
pip install -r requirements.txt
streamlit run app.py
```

Open http://localhost:8501 and check every filter, hover tooltip, chart,
and download button.

## Step 3 — Deploy to Streamlit Community Cloud (free)

1. Create a public GitHub repository and push: `app.py`,
   `requirements.txt`, `README.md`, and the whole `data/` folder.
   (You can leave `prepare_data.py` in the repo too — it is documentation
   of your data pipeline, and Streamlit ignores it.)
2. Go to https://share.streamlit.io and sign in with GitHub.
3. Click **Create app** → pick your repo → set **Main file path** to
   `app.py` → **Deploy**.
4. After 2–3 minutes you get a public URL like
   `https://<your-app>.streamlit.app` — that is the link for your report.

## Data sources

- Community resources: OpenStreetMap contributors (via OSMnx)
- Unemployment & population: U.S. Census Bureau, ACS 5-Year Estimates (DP03/DP05)
- Boundaries: Census TIGER/Line ZCTA shapefiles (via pygris)
