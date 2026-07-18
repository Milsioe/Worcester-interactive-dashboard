import os

import streamlit as st
import streamlit.components.v1 as components
import pandas as pd

# Folder where this file lives — assets are loaded relative to it,
# so the app works no matter which folder Streamlit is launched from.
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

st.set_page_config(
    page_title="Worcester Interactive Dashboard",
    layout="wide"
)

# --------------------------------------------------
# Data (defined once, used everywhere)
# --------------------------------------------------
unemployment = pd.DataFrame({
    "ZIP Code": [
        "01602", "01603", "01604", "01605",
        "01606", "01607", "01608", "01609", "01610"
    ],
    "Unemployment Rate (%)": [
        5.2, 6.1, 5.8, 7.3,
        4.9, 5.5, 6.4, 5.7, 5.3
    ]
})

resources = pd.DataFrame({
    "Resource Type": ["Hospitals", "Schools", "Libraries", "Parks"],
    "Count": [8, 24, 10, 18]
})


# --------------------------------------------------
# Helper: show an image only if the file exists
# --------------------------------------------------
def show_image(filename):
    path = os.path.join(BASE_DIR, filename)
    if os.path.exists(path):
        st.image(path, use_container_width=True)
    else:
        st.error(f"{filename} was not found in {BASE_DIR}.")


# --------------------------------------------------
# Title
# --------------------------------------------------
st.title("🏙️ Worcester Interactive Dashboard for Community Resources")

st.subheader(
    "A Geospatial Analysis of Community Resources and Unemployment "
    "in Worcester, Massachusetts"
)

st.write("""
This interactive dashboard explores the relationship between community resources
and unemployment across Worcester, Massachusetts. It provides geographic
visualizations and analytical insights to support community planning,
resource allocation, and data-driven decision-making.
""")

st.divider()

# --------------------------------------------------
# Sidebar
# --------------------------------------------------
st.sidebar.title("Dashboard Menu")

page = st.sidebar.radio(
    "Select a Dashboard",
    [
        "Overview",
        "Community Resources",
        "Unemployment",
        "Correlation",
        "Interactive Map",
        "Underlying Data"
    ]
)

st.sidebar.markdown("---")
st.sidebar.subheader("Author")
st.sidebar.write("Eumilsio Benhane")
st.sidebar.write("Master of Science in Data Science")
st.sidebar.write("Grand Canyon University")
st.sidebar.markdown("---")

st.sidebar.subheader("About")
st.sidebar.write(
    "This dashboard analyzes community resources and unemployment "
    "across Worcester, Massachusetts using interactive visualizations."
)

# --------------------------------------------------
# Overview
# --------------------------------------------------
if page == "Overview":

    st.header("Dashboard Overview")

    col1, col2, col3 = st.columns(3)
    col1.metric("ZIP Codes", "9")
    col2.metric("Community Resources", "100+")
    col3.metric("Hospitals", "8")

    st.info(
        """
        Welcome! Use the Dashboard Menu on the left to explore
        community resources, unemployment, correlation analysis,
        and the interactive map.
        """
    )

# --------------------------------------------------
# Community Resources
# --------------------------------------------------
elif page == "Community Resources":

    st.header("Community Resources")

    st.write(
        "The map below shows all community resources across Worcester. "
        "To filter and explore individual locations, use the "
        "Interactive Map page."
    )

    show_image("community_resources_worcester.png")

# --------------------------------------------------
# Unemployment
# --------------------------------------------------
elif page == "Unemployment":

    st.header("Unemployment by ZIP Code")

    show_image("worcester_unemployment_choropleth.png")

    st.subheader("Unemployment Rate by ZIP Code")
    st.bar_chart(unemployment.set_index("ZIP Code"))

# --------------------------------------------------
# Correlation
# --------------------------------------------------
elif page == "Correlation":

    st.header("Relationship Between Community Resources and Unemployment")

    show_image("worcester_correlation.png")

# --------------------------------------------------
# Interactive Map
# --------------------------------------------------
elif page == "Interactive Map":

    st.header("Interactive Community Resources Map")

    map_path = os.path.join(BASE_DIR, "worcester_resources_map.html")

    try:
        with open(map_path, "r", encoding="utf-8") as f:
            html = f.read()

        components.html(html, height=700, scrolling=True)

    except FileNotFoundError:
        st.error(f"worcester_resources_map.html was not found in {BASE_DIR}.")

# --------------------------------------------------
# Underlying Data
# --------------------------------------------------
elif page == "Underlying Data":

    st.header("Underlying Data")

    st.write("""
    This page allows users to inspect the datasets used in the dashboard.
    The data below summarizes unemployment and community resources in
    Worcester, Massachusetts.
    """)

    st.subheader("Unemployment Dataset")
    st.dataframe(unemployment, use_container_width=True)

    st.download_button(
        "Download Unemployment Data",
        unemployment.to_csv(index=False),
        file_name="unemployment_data.csv",
        mime="text/csv"
    )

    st.subheader("Community Resources Dataset")
    st.dataframe(resources, use_container_width=True)

    st.download_button(
        "Download Community Resources",
        resources.to_csv(index=False),
        file_name="community_resources.csv",
        mime="text/csv"
    )

# --------------------------------------------------
# Footer
# --------------------------------------------------
st.divider()

st.caption(
    "Worcester Interactive Dashboard for Community Resources | "
    "Master of Science in Data Science | Grand Canyon University"
)