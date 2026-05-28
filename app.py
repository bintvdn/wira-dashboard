# =========================================================
# WIRA — Business Intelligence Dashboard
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
# FIX GEOJSON NAME
# =========================================================

for feature in geojson["features"]:
    
    props = feature.get("properties", {})
    
    if "name" not in props:
        if "@id" in props:
            props["name"] = props.get("name", "")
    
    props["name"] = str(props.get("name", "")).strip().upper()

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

    st.markdown("""
    <style>

    .sidebar-title {
        font-size: 30px;
        font-weight: 700;
        color: white;
        margin-bottom: -5px;
    }

    .sidebar-caption {
        font-size: 13px;
        color: #9CA3AF;
        margin-bottom: 20px;
    }

    .sidebar-card {
        background-color: #111827;
        padding: 16px;
        border-radius: 14px;
        border: 1px solid rgba(255,255,255,0.08);
        margin-bottom: 14px;
    }

    .sidebar-card-title {
        font-size: 15px;
        font-weight: 600;
        color: white;
        margin-bottom: 12px;
    }

    .sidebar-desc {
        font-size: 13px;
        line-height: 1.6;
        color: #E5E7EB;
    }

    </style>
    """, unsafe_allow_html=True)

    # =========================
    # TITLE
    # =========================

    st.markdown("""
    <div class="sidebar-title">
    WIRA
    </div>

    <div class="sidebar-caption">
    Business Intelligence Dashboard — Semarang
    </div>
    """, unsafe_allow_html=True)

    # =========================
    # DATASET OVERVIEW
    # =========================

    st.markdown("""
    <div class="sidebar-card">

    <div class="sidebar-card-title">
    📊 Dataset Overview
    </div>
    """, unsafe_allow_html=True)

    st.metric("Kecamatan", "16")
    st.metric("Kelurahan", "177")
    st.metric("Ruas Jalan", len(df))

    st.metric(
        "Business Points",
        int(df["total_competitor"].sum())
    )

    st.markdown("""
    </div>
    """, unsafe_allow_html=True)

    # =========================
    # DESCRIPTION
    # =========================

    st.markdown("""
    <div class="sidebar-card">

    <div class="sidebar-desc">
    Dashboard ini dirancang untuk mendukung analisis spasial bisnis melalui identifikasi konsentrasi usaha, tingkat aksesibilitas wilayah, opportunity gap, serta pola keterhubungan antar sektor bisnis di Kota Semarang.
    </div>

    </div>
    """, unsafe_allow_html=True)

# =========================================================
# HEADER
# =========================================================

st.title("Business Intelligence Dashboard")

# =========================================================
# SECTION 1
# =========================================================

st.markdown(
    "## Business Overview & Diversity"
)

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
    
    top_n = st.slider(
        "Top N",
        5, 15, 8
    )

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

# =========================================================
# BARPLOT
# =========================================================

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
        yaxis=dict(
            categoryorder="total ascending"
        )
    )

    st.plotly_chart(
        fig,
        use_container_width=True
    )

# =========================================================
# INSIGHT
# =========================================================

with right:

    top_area = agg.iloc[0][level]
    top_value = agg.iloc[0][val]

    st.markdown("""
    <style>
    .insight-box {
        background-color: #111827;
        padding: 18px;
        border-radius: 14px;
        border: 1px solid rgba(255,255,255,0.08);
    }

    .insight-title {
        font-size: 20px;
        font-weight: 600;
        color: white;
        margin-bottom: 10px;
    }

    .insight-text {
        font-size: 14px;
        line-height: 1.5;
        color: #E5E7EB;
    }
    </style>
    """, unsafe_allow_html=True)

    st.markdown(f"""
    <div class="insight-box">

    <div class="insight-title">
    Business Insight
    </div>

    <div class="insight-text">
    Wilayah <b>{top_area}</b> menunjukkan konsentrasi aktivitas bisnis tertinggi pada level <b>{level}</b> untuk kategori <b>{usaha}</b> dengan total aktivitas sebesar <b>{int(top_value)}</b>.<br><br>

    Tingginya konsentrasi usaha mengindikasikan kawasan dengan intensitas ekonomi yang lebih aktif, tingkat kompetisi yang relatif padat, serta demand pasar yang telah berkembang lebih kuat dibanding wilayah lainnya.
    </div>

    </div>
    """, unsafe_allow_html=True)

# =========================================================
# DIVERSITY
# =========================================================

st.markdown(
    "### Business Diversity Composition"
)

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
    height=320,
    template="plotly_white",
    margin=dict(t=20, b=20, l=20, r=20),
    xaxis_title="Kecamatan",
    yaxis_title="Business Composition Ratio",
    legend_title="Business Sector"
)

st.plotly_chart(
    fig_div,
    use_container_width=True
)

st.markdown("""
<div class="insight-box">
<div class="insight-text">

Komposisi bisnis menunjukkan variasi sektor usaha pada masing-masing kecamatan. 
Wilayah dengan distribusi sektor yang lebih seimbang cenderung memiliki ekosistem ekonomi yang lebih terdiversifikasi, sedangkan dominasi sektor tertentu dapat mengindikasikan clustering aktivitas bisnis pada kawasan tersebut.

</div>
</div>
""", unsafe_allow_html=True)

# =========================================================
# SECTION 2
# =========================================================

st.markdown(
    "## Accessibility & Traffic Intelligence"
)

# =========================================================
# TRAFFIC SCORE
# =========================================================

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
    yaxis=dict(
        categoryorder="total ascending"
    )
)

st.plotly_chart(
    fig_acc,
    use_container_width=True
)

top_traffic_area = traffic_kec.iloc[0][filter_level]

top_traffic_value = traffic_kec.iloc[0]["traffic_score"]

st.markdown(f"""
<div class="insight-box">
<div class="insight-text">

Wilayah <b>{top_traffic_area}</b> memiliki nilai traffic tertinggi dengan skor sebesar <b>{top_traffic_value:.2f}</b>, tingginya traffic score menunjukkan kawasan dengan mobilitas dan aksesibilitas yang lebih aktif sehingga berpotensi menjadi pusat pergerakan konsumen dan aktivitas ekonomi harian.

</div>
</div>
""", unsafe_allow_html=True)

# =========================================================
# TRAFFIC DEPENDENCY
# =========================================================

dep = []

for u in usaha_list:

    temp = df[
        df[f"competitor_{u}"] > 0
    ]

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
    yaxis=dict(
        categoryorder="total ascending"
    )
)

st.plotly_chart(
    fig_dep,
    use_container_width=True
)

st.markdown("""
<div class="insight-box">
<div class="insight-text">

Traffic dependency merepresentasikan tingkat ketergantungan suatu sektor usaha terhadap area dengan mobilitas tinggi. 
Semakin tinggi nilainya, semakin besar kecenderungan sektor tersebut berkembang pada kawasan dengan arus konsumen dan aksesibilitas yang padat.

</div>
</div>
""", unsafe_allow_html=True)

# =========================================================
# SECTION 3
# =========================================================

st.markdown(
    "## Opportunity Gap & Ecosystem Network"
)

# =========================================================
# AGGREGASI KECAMATAN
# =========================================================

kec = df.groupby("kecamatan").agg({
    "demand_university": "sum",
    "demand_school": "sum",
    "demand_office": "sum",
    "total_competitor": "sum",
    "lat_centroid": "mean",
    "lng_centroid": "mean"
}).reset_index()

kec["demand_score"] = (
    kec["demand_university"] * 3 +
    kec["demand_school"] +
    kec["demand_office"] * 2
)

kec["gap_score"] = (
    kec["demand_score"] -
    kec["total_competitor"]
)

kec["kecamatan"] = (
    kec["kecamatan"]
    .astype(str)
    .str.strip()
    .str.upper()
)

# =========================================================
# CHOROPLETH MAP
# =========================================================

fig_map = px.choropleth_mapbox(
    kec,
    geojson=geojson,
    locations="kecamatan",
    featureidkey="properties.name",
    color="gap_score",
    color_continuous_scale="Viridis",
    mapbox_style="carto-positron",
    zoom=10,
    center={
        "lat": -6.97,
        "lon": 110.42
    },
    opacity=0.75
)

fig_map.update_layout(
    margin=dict(
        r=0,
        t=0,
        l=0,
        b=0
    ),
    height=600
)

st.plotly_chart(
    fig_map,
    use_container_width=True
)

st.markdown("""
<div class="insight-box">
<div class="insight-text">

Peta choropleth menggambarkan distribusi opportunity gap antar kecamatan di Kota Semarang. Wilayah dengan intensitas warna yang lebih tinggi menunjukkan potensi pasar yang relatif besar dibanding tingkat kompetisi bisnis yang saat ini tersedia.

</div>
</div>
""", unsafe_allow_html=True)

# =========================================================
# OPPORTUNITY GAP RANKING
# =========================================================

st.markdown(
    "### Strategic Opportunity Ranking"
)

col1, col2, col3 = st.columns(3)

with col1:

    opp_level = st.selectbox(
        "Spatial Level (Opportunity)",
        ["kecamatan", "kelurahan", "nama_jalan"]
    )

with col2:

    opp_usaha = st.selectbox(
        "Jenis Usaha Opportunity",
        ["all"] + usaha_list
    )

with col3:

    opp_top_n = st.slider(
        "Top Opportunity Areas",
        5, 20, 10
    )

group_cols = [
    "demand_university",
    "demand_school",
    "demand_office"
]

agg_dict = {
    col: "sum"
    for col in group_cols
}

if opp_usaha == "all":
    
    agg_dict["total_competitor"] = "sum"

else:
    
    agg_dict[
        f"competitor_{opp_usaha}"
    ] = "sum"

opp_df = (
    df.groupby(opp_level)
    .agg(agg_dict)
    .reset_index()
)

opp_df["demand_score"] = (
    opp_df["demand_university"] * 3 +
    opp_df["demand_school"] +
    opp_df["demand_office"] * 2
)

if opp_usaha == "all":

    opp_df["competitor_score"] = (
        opp_df["total_competitor"]
    )

else:

    opp_df["competitor_score"] = (
        opp_df[f"competitor_{opp_usaha}"]
    )

opp_df["gap_score"] = (
    opp_df["demand_score"] -
    opp_df["competitor_score"]
)

opp_rank = (
    opp_df.sort_values(
        "gap_score",
        ascending=False
    )
    .head(opp_top_n)
)

# =========================================================
# OPPORTUNITY BARPLOT
# =========================================================

fig_opp = px.bar(
    opp_rank,
    x="gap_score",
    y=opp_level,
    orientation="h",
    color="gap_score",
    color_continuous_scale="Greens"
)

fig_opp.update_layout(
    height=550,
    yaxis=dict(
        categoryorder="total ascending"
    )
)

st.plotly_chart(
    fig_opp,
    use_container_width=True
)

best_area = opp_rank.iloc[0][opp_level]

best_gap = opp_rank.iloc[0]["gap_score"]

st.markdown(f"""
<div class="insight-box">
<div class="insight-text">

Wilayah <b>{best_area}</b> memiliki opportunity gap tertinggi untuk kategori <b>{opp_usaha}</b> dengan nilai sebesar <b>{best_gap:.2f}</b>, kondisi ini menunjukkan potensi demand yang relatif tinggi dibanding tingkat kompetisi yang ada sehingga wilayah tersebut memiliki peluang pengembangan bisnis yang lebih optimal.

</div>
</div>
""", unsafe_allow_html=True)

# =========================================================
# TABLE
# =========================================================

st.markdown(
    "### Detailed Opportunity Analysis"
)

st.dataframe(
    opp_rank[
        [
            opp_level,
            "demand_score",
            "competitor_score",
            "gap_score"
        ]
    ],
    use_container_width=True
)

# =========================================================
# NETWORK GRAPH
# =========================================================

st.markdown(
    "### Ecosystem Network Graph"
)

binary = pd.DataFrame({
    u: (
        df[f"competitor_{u}"] > 0
    ).astype(int)
    for u in usaha_list
})

edges = []

for u1, u2 in combinations(
    usaha_list,
    2
):

    w = (
        (binary[u1] == 1) &
        (binary[u2] == 1)
    ).sum()

    if w > 3:

        edges.append(
            (u1, u2, w)
        )

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

    edge_x += [
        x0,
        x1,
        None
    ]

    edge_y += [
        y0,
        y1,
        None
    ]

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

node_x, node_y = [], []

text, size = [], []

for node in G.nodes():

    x, y = pos[node]

    node_x.append(x)
    node_y.append(y)

    text.append(node)

    size.append(
        G.degree[node] * 7 + 12
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

st.markdown("""
<div class="insight-box">
<div class="insight-text">

Visualisasi network graph menunjukkan keterhubungan antar sektor usaha berdasarkan kemunculan bisnis pada kawasan yang sama. Relasi dengan koneksi lebih tinggi dapat merepresentasikan pola clustering bisnis maupun potensi sinergi ekonomi antar sektor.

</div>
</div>
""", unsafe_allow_html=True)

# =========================================================
# TOP NETWORK TABLE
# =========================================================

top_edges = sorted(
    edges,
    key=lambda x: x[2],
    reverse=True
)[:10]

st.markdown(
    "### Top Network Relations"
)

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

st.markdown("""
<div class="insight-box">
<div class="insight-text">

Connection menunjukkan seberapa sering dua sektor usaha muncul pada area yang sama. 
Nilai connection dihitung berdasarkan total kemunculan bersama antar sektor bisnis dalam dataset spasial sehingga semakin tinggi nilainya menunjukkan hubungan spasial dan kecenderungan clustering bisnis yang semakin kuat.

</div>
</div>
""", unsafe_allow_html=True)
