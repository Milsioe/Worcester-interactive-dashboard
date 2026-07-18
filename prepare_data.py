"""
prepare_data.py
Task 1: Planning and Data Preparation
Community Development Dashboard - Worcester, Massachusetts

Run this script ONCE on your own machine (it needs internet access to
OpenStreetMap and the U.S. Census Bureau). It downloads, cleans, and joins
all datasets, then saves three files into the data/ folder:

    data/worcester_boundary.geojson   - city boundary polygon
    data/resources.geojson            - community resource points
    data/zips.geojson                 - ZIP code polygons + all metrics

The Streamlit app (app.py) only reads these files, so the deployed
dashboard never has to call external APIs and loads quickly.

Requirements for THIS script only (not needed for deployment):
    pip install osmnx pygris requests geopandas pandas shapely
"""

import warnings

import geopandas as gpd
import osmnx as ox
import pandas as pd
import requests
from pygris import zctas

warnings.filterwarnings("ignore")

PLACE = "Worcester, Massachusetts, USA"
CRS = "EPSG:4326"

# ---------------------------------------------------------------------------
# Step 1: City boundary
# ---------------------------------------------------------------------------
print("Downloading Worcester city boundary from OpenStreetMap...")
city = ox.geocode_to_gdf(PLACE).to_crs(CRS)
city[["geometry"]].to_file("data/worcester_boundary.geojson", driver="GeoJSON")

# ---------------------------------------------------------------------------
# Step 2: Community resources from OpenStreetMap (OSMnx)
# ---------------------------------------------------------------------------
print("Downloading community resources from OpenStreetMap...")

layers = {
    "School": {"amenity": "school"},
    "Hospital": {"amenity": "hospital"},
    "Church": {"building": "church"},
}

frames = []
for category, tags in layers.items():
    gdf = ox.features_from_place(PLACE, tags=tags)
    gdf = gdf.reset_index()
    gdf["category"] = category
    frames.append(gdf)

# YMCA / recreation: pull leisure features, keep fitness and sports centres,
# and flag anything whose name mentions YMCA
leisure = ox.features_from_place(PLACE, tags={"leisure": True}).reset_index()
leisure["name"] = leisure.get("name", pd.Series(dtype=object))
is_ymca = leisure["name"].fillna("").str.contains("YMCA|YWCA", case=False)
is_fitness = leisure.get("leisure", pd.Series(dtype=object)).isin(
    ["fitness_centre", "sports_centre"]
)
rec = leisure[is_ymca | is_fitness].copy()
rec["category"] = "YMCA / Recreation"
frames.append(rec)

resources = pd.concat(frames, ignore_index=True)

# --- Cleaning (Task 1: handle missing values, ensure consistency) ---
resources = gpd.GeoDataFrame(resources, geometry="geometry", crs=CRS)
resources = resources[resources.geometry.notna()]           # drop missing geometry
resources["geometry"] = resources.geometry.representative_point()  # polygons -> points
resources["name"] = resources["name"].fillna("Unnamed " + resources["category"])
resources = resources.drop_duplicates(subset=["name", "category"])  # remove duplicates
resources = resources[["name", "category", "geometry"]].to_crs(CRS)

print(resources["category"].value_counts())
resources.to_file("data/resources.geojson", driver="GeoJSON")

# ---------------------------------------------------------------------------
# Step 3: ZIP code (ZCTA) boundaries from Census TIGER
# ---------------------------------------------------------------------------
print("Downloading ZCTA boundaries (Census TIGER via pygris)...")
zcta = zctas(starts_with="016", year=2020, cb=True).to_crs(CRS)
zcta = zcta.rename(columns={"ZCTA5CE20": "zip"})[["zip", "geometry"]]

# Keep only ZCTAs that meaningfully overlap the city (>5% of their area)
proj = "EPSG:26986"  # Massachusetts state plane, meters
inter = gpd.overlay(zcta.to_crs(proj), city.to_crs(proj)[["geometry"]], how="intersection")
inter["overlap"] = inter.geometry.area
zcta_m = zcta.to_crs(proj)
zcta_m["area"] = zcta_m.geometry.area
share = inter.groupby("zip")["overlap"].sum() / zcta_m.set_index("zip")["area"]
keep = share[share > 0.05].index
zips = zcta[zcta["zip"].isin(keep)].copy()
print("Worcester ZIP codes kept:", sorted(zips["zip"]))

# ---------------------------------------------------------------------------
# Step 4: Unemployment + population from the Census ACS 5-Year API
#         (DP03_0009PE = unemployment rate, DP05_0001E = total population)
# ---------------------------------------------------------------------------
print("Downloading ACS unemployment and population data...")


def fetch_acs(year):
    url = (
        f"https://api.census.gov/data/{year}/acs/acs5/profile"
        "?get=DP03_0009PE,DP05_0001E&for=zip%20code%20tabulation%20area:*"
    )
    r = requests.get(url, timeout=60)
    r.raise_for_status()
    rows = r.json()
    df = pd.DataFrame(rows[1:], columns=rows[0])
    df = df.rename(
        columns={
            "DP03_0009PE": "unemployment_rate",
            "DP05_0001E": "population",
            "zip code tabulation area": "zip",
        }
    )
    return df


acs = None
for year in [2023, 2022, 2021]:  # year-fallback logic
    try:
        acs = fetch_acs(year)
        print(f"Using ACS 5-Year {year} data")
        break
    except Exception as e:
        print(f"ACS {year} unavailable ({e}); trying earlier year...")

acs["unemployment_rate"] = pd.to_numeric(acs["unemployment_rate"], errors="coerce")
acs["population"] = pd.to_numeric(acs["population"], errors="coerce")
acs = acs[acs["unemployment_rate"].between(0, 100)]  # drop ACS sentinel values

zips = zips.merge(acs[["zip", "unemployment_rate", "population"]], on="zip", how="left")
zips["unemployment_rate"] = zips["unemployment_rate"].fillna(
    zips["unemployment_rate"].median()
)

# ---------------------------------------------------------------------------
# Step 5: Calculated fields (Task 1: aggregates for the analysis)
# ---------------------------------------------------------------------------
print("Computing per-ZIP aggregates and priority score...")
joined = gpd.sjoin(resources, zips[["zip", "geometry"]], predicate="within")
counts = (
    joined.groupby(["zip", "category"]).size().unstack(fill_value=0).reset_index()
)
zips = zips.merge(counts, on="zip", how="left")
for col in ["School", "Hospital", "Church", "YMCA / Recreation"]:
    if col not in zips.columns:
        zips[col] = 0
    zips[col] = zips[col].fillna(0).astype(int)

zips["total_resources"] = zips[
    ["School", "Hospital", "Church", "YMCA / Recreation"]
].sum(axis=1)
zips["resources_per_10k"] = (
    zips["total_resources"] / zips["population"].replace(0, pd.NA) * 10000
).fillna(0).round(2)


def minmax(s):
    rng = s.max() - s.min()
    return (s - s.min()) / rng if rng else s * 0


# Priority score (0-100): high unemployment AND low resource access -> high score
zips["priority_score"] = (
    100 * (0.5 * minmax(zips["unemployment_rate"]) + 0.5 * (1 - minmax(zips["resources_per_10k"])))
).round(1)

zips.to_file("data/zips.geojson", driver="GeoJSON")
print("\nDone. Files written to data/. Preview:")
print(
    zips[
        ["zip", "unemployment_rate", "total_resources", "resources_per_10k", "priority_score"]
    ].sort_values("priority_score", ascending=False).to_string(index=False)
)
