# =========================================================
# WIRA — Business Intelligence Dashboard (POWER BI STYLE)
# =========================================================

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import networkx as nx
from itertools import combinations
from pathlib import Path
import json

# =========================================================
# CONFIG
# =========================================================

st.set_page_config(
    page_title="WIRA BI Dashboard",
    layout="wide",
    initial_sidebar_state="expanded"
)

BASE_DIR = Path(__file__).resolve().parent

# =========================================================
# LOAD DATA
# =========================================================

@st.cache_data
def load_data():
    return pd.read_excel(BASE_DIR / "data" / "df_fe.xlsx")

df = load_data()

with open(BASE_DIR / "data" / "export.geojson") as f:
    geojson = json.load(f)

# =========================================================
# BUSINESS LIST
# =========================================================

usaha_list = [
    'cafe','fnb','laundry','gym','fashion','stationery',
    'carwash','photostudio','barbershop','salon','bengkel','elektronik'
]

for u in usaha_list:
    col = f"competitor_{u}"
    if col not in df.columns:
        df[col] = 0

df["total_competitor"] = df[
    [f"competitor_{u}" for u in usaha_list]
].sum(axis=1)

# =========================================================
# SIDEBAR
# =========================================================

with st.sidebar:
    st.markdown("## 🟦 WIRA")
    st.caption("Business Intelligence Dashboard — Semarang")

    st.markdown("---")

    st.markdown("### 📊 Dataset Overview")
    st.metric("Kecamatan", "16")
    st.metric("Kelurahan", "177")
    st.metric("Ruas Jalan", len(df))
    st.metric("Business Points", int(df["total_competitor"].sum()))

    st.markdown("---")
    st.info(
        "Analisis kompetisi, aksesibilitas, opportunity gap & network bisnis."
    )

# =========================================================
# HEADER
# =========================================================

st.title("Business Intelligence Dashboard")

# =========================================================
# SECTION 1
# =========================================================

st.markdown("## 1. Business Overview & Diversity")

col1, col2, col3 = st.columns(3)

with col1:
    level = st.selectbox(
        "Spatial Level",
        ["kecamatan","kelurahan","nama_jalan"]
    )

with col2:
    usaha = st.selectbox(
        "Jenis Usaha",
        ["all"] + usaha_list
    )

with col3:
    top_n = st.slider("Top N", 5, 15, 8)

val = (
    "total_competitor"
    if usaha == "all"
    else f"competitor_{usaha}"
)

agg = (
    df.groupby(level)[val]
    .sum()
    .sort_values(ascending=False)
    .head(top_n)
    .reset_index()
)

left, right = st.columns([3,1])

with left:
    fig = px.bar(
        agg,
        x=val,
        y=level,
        orientation="h",
        color=val,
        color_continuous_scale="Blues"
    )

    fig.update_layout(
        height=450,
        yaxis=dict(categoryorder="total ascending")
    )

    st.plotly_chart(fig, use_container_width=True)

with right:
    top_area = agg.iloc[0][level]
    top_value = agg.iloc[0][val]

    st.markdown(f"""
### 📍 Insight

Pada level **{level}**, wilayah **{top_area}**
merupakan pusat aktivitas bisnis tertinggi
untuk kategori **{usaha}**.

📌 Total aktivitas: **{int(top_value)}**

→ Konsentrasi tinggi menunjukkan market matang  
→ Kompetisi kuat & demand tinggi  
→ Cocok untuk strategi diferensiasi
""")

# =========================================================
# DIVERSITY
# =========================================================

st.markdown("### Business Diversity Composition")

div_raw = df.groupby("kecamatan")[
    [f"competitor_{u}" for u in usaha_list]
].sum()

div_raw["total"] = div_raw.sum(axis=1)

div_raw = div_raw.sort_values(
    "total",
    ascending=False
)

div = (
    div_raw.drop(columns="total")
    .replace(0, np.nan)
    .div(
        div_raw.drop(columns="total").sum(axis=1),
        axis=0
    )
    .fillna(0)
)

fig_div = go.Figure()

for u in usaha_list:
    fig_div.add_trace(
        go.Bar(
            name=u,
            x=div.index,
            y=div[f"competitor_{u}"]
        )
    )

fig_div.update_layout(
    barmode="stack",
    height=450,
    template="plotly_white"
)

st.plotly_chart(fig_div, use_container_width=True)

# =========================================================
# SECTION 2
# =========================================================

st.markdown("## 2. Accessibility & Traffic Intelligence")

# =========================
# TRAFFIC SCORE
# =========================

filter_level = st.selectbox(
    "Spatial Level (Traffic)",
    ["kecamatan","kelurahan","nama_jalan"]
)

top_n_traffic = st.slider(
    "Top Area Traffic",
    5, 15, 8
)

traffic_kec = (
    df.groupby(filter_level)["traffic_score"]
    .mean()
    .reset_index()
    .sort_values(
        "traffic_score",
        ascending=False
    )
    .head(top_n_traffic)
)

fig_acc = px.bar(
    traffic_kec,
    x="traffic_score",
    y=filter_level,
    orientation="h",
    color="traffic_score",
    color_continuous_scale="Teal"
)

fig_acc.update_layout(
    height=500,
    yaxis=dict(categoryorder="total ascending")
)

st.plotly_chart(
    fig_acc,
    use_container_width=True
)

# =========================
# INSIGHT
# =========================

top_traffic_area = traffic_kec.iloc[0][filter_level]
top_traffic_value = traffic_kec.iloc[0]["traffic_score"]

st.info(f"""
🚦 Traffic Insight:

**{top_traffic_area}**
memiliki traffic tertinggi.

Score: {top_traffic_value:.2f}

→ Magnet aktivitas ekonomi  
→ Cocok untuk retail & service expansion  
→ Area dengan mobilitas konsumen tertinggi
""")

# =========================
# TRAFFIC DEPENDENCY
# =========================

dep = []

for u in usaha_list:
    temp = df[df[f"competitor_{u}"] > 0]

    dep.append({
        "usaha": u,
        "traffic_dependency":
            temp["traffic_score"].mean()
    })

dep_df = (
    pd.DataFrame(dep)
    .sort_values(
        "traffic_dependency",
        ascending=False
    )
)

fig_dep = px.bar(
    dep_df,
    x="traffic_dependency",
    y="usaha",
    orientation="h",
    color="traffic_dependency",
    color_continuous_scale="OrRd"
)

fig_dep.update_layout(
    height=500,
    yaxis=dict(categoryorder="total ascending")
)

st.plotly_chart(
    fig_dep,
    use_container_width=True
)

# =========================================================
# SECTION 3
# =========================================================

st.markdown("## 3. Opportunity Gap & Ecosystem Network")

kec = df.groupby("kecamatan").agg({
    "demand_university":"sum",
    "demand_school":"sum",
    "demand_office":"sum",
    "total_competitor":"sum",
    "lat_centroid":"mean",
    "lng_centroid":"mean"
}).reset_index()

kec["demand_score"] = (
    kec["demand_university"]*3 +
    kec["demand_school"] +
    kec["demand_office"]*2
)

kec["gap_score"] = (
    kec["demand_score"] -
    kec["total_competitor"]
)

# =========================
# MAP
# =========================

fig_map = px.choropleth_mapbox(
    kec,
    geojson=geojson,
    locations="kecamatan",
    featureidkey="properties.name",
    color="gap_score",
    color_continuous_scale="Viridis",
    mapbox_style="carto-positron",
    zoom=10,
    center={"lat": -6.97, "lon": 110.42},
    opacity=0.75
)

fig_map.update_layout(
    margin=dict(r=0,t=0,l=0,b=0),
    height=600
)

st.plotly_chart(
    fig_map,
    use_container_width=True
)

# =========================
# TABLE
# =========================

st.markdown("### Top Opportunity Areas")

table_df = (
    kec.sort_values(
        "gap_score",
        ascending=False
    )
    .head(10)
)

st.dataframe(
    table_df[
        [
            "kecamatan",
            "gap_score",
            "demand_score",
            "total_competitor"
        ]
    ],
    use_container_width=True
)

# =========================================================
# NETWORK GRAPH
# =========================================================

st.markdown("### Ecosystem Network Graph")

binary = pd.DataFrame({
    u: (
        df[f"competitor_{u}"] > 0
    ).astype(int)
    for u in usaha_list
})

edges = []

for u1, u2 in combinations(usaha_list, 2):
    w = (
        (binary[u1] == 1) &
        (binary[u2] == 1)
    ).sum()

    if w > 3:
        edges.append((u1, u2, w))

G = nx.Graph()

for u1, u2, w in edges:
    G.add_edge(
        u1,
        u2,
        weight=w
    )

pos = nx.spring_layout(
    G,
    k=1.2,
    seed=42
)

edge_x, edge_y = [], []

for u, v in G.edges():
    x0, y0 = pos[u]
    x1, y1 = pos[v]

    edge_x += [x0, x1, None]
    edge_y += [y0, y1, None]

edge_trace = go.Scatter(
    x=edge_x,
    y=edge_y,
    mode="lines",
    line=dict(
        width=1.2,
        color="rgba(120,120,120,0.4)"
    ),
    hoverinfo="none"
)

node_x, node_y, text, size = [], [], [], []

for node in G.nodes():
    x, y = pos[node]

    node_x.append(x)
    node_y.append(y)
    text.append(node)
    size.append(
        G.degree[node]*7 + 12
    )

node_trace = go.Scatter(
    x=node_x,
    y=node_y,
    mode="markers+text",
    text=text,
    textposition="top center",
    marker=dict(
        size=size,
        color="#60A5FA",
        line=dict(
            width=1,
            color="black"
        )
    )
)

fig_net = go.Figure(
    data=[
        edge_trace,
        node_trace
    ]
)

fig_net.update_layout(
    height=600,
    template="plotly_white"
)

st.plotly_chart(
    fig_net,
    use_container_width=True
)

# =========================================================
# NETWORK TABLE
# =========================================================

top_edges = sorted(
    edges,
    key=lambda x: x[2],
    reverse=True
)[:10]

st.markdown("### 🔗 Top Network Relations")

st.dataframe(
    pd.DataFrame(
        top_edges,
        columns=[
            "Business A",
            "Business B",
            "Connection"
        ]
    ),
    use_container_width=True
)