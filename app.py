"""
Indonesia Palm Oil Dashboard (2010-2023)
Tema: "Dari Kebun ke Devisa" - perjalanan sawit dari provinsi ke ekspor/konsumsi.

Jalankan dengan:  streamlit run app.py
"""
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

import data_loader as dl

# ----------------------------------------------------------------------------
# Konfigurasi halaman
# ----------------------------------------------------------------------------
st.set_page_config(
    page_title="Dashboard Sawit Indonesia",
    page_icon="🌴",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Palet warna (selaras dengan tema poster: hijau & oranye)
GREEN = "#4F7A28"
GREEN_LIGHT = "#7CB342"
ORANGE = "#D2601A"
AMBER = "#E8A317"
TEAL = "#1F9E89"

OWNERSHIP_COLORS = {"PR": GREEN_LIGHT, "PBS": ORANGE, "PBN": TEAL}

# ----------------------------------------------------------------------------
# Load data
# ----------------------------------------------------------------------------
metrics = dl.load_province_metrics()
ownership = dl.load_ownership()
national = dl.load_national_trend()
eksim = dl.load_export_import()
geojson = dl.load_geojson()
geo_map = dl.build_geo_id_map()

# ----------------------------------------------------------------------------
# Sidebar - Filter global
# ----------------------------------------------------------------------------
st.sidebar.title("🌴 Filter")

year_range = st.sidebar.slider(
    "Rentang Tahun",
    min_value=dl.YEAR_MIN,
    max_value=dl.YEAR_MAX,
    value=(dl.YEAR_MIN, dl.YEAR_MAX),
)

provinces_all = sorted(metrics["Provinsi"].unique())
province_sel = st.sidebar.selectbox(
    "Provinsi",
    options=["Semua Provinsi"] + provinces_all,
)

ownership_sel = st.sidebar.radio(
    "Jenis Kepemilikan",
    options=["Semua", "Rakyat (PR)", "Swasta (PBS)", "Negara (PBN)"],
)

st.sidebar.markdown("---")
st.sidebar.caption(
    "Data: Outlook Kelapa Sawit (Pusdatin Kementan), BPS. "
    "Periode 2010–2023."
)

# Map filter kepemilikan -> nama kolom
OWN_COL = {
    "Semua": "Total",
    "Rakyat (PR)": "Rakyat",
    "Swasta (PBS)": "Swasta",
    "Negara (PBN)": "Negara",
}
own_key = OWN_COL[ownership_sel]

# ----------------------------------------------------------------------------
# Helper: filter dataframe sesuai pilihan
# ----------------------------------------------------------------------------
y0, y1 = year_range


def filter_years(df):
    return df[(df["Tahun"] >= y0) & (df["Tahun"] <= y1)]


m = filter_years(metrics)
if province_sel != "Semua Provinsi":
    m = m[m["Provinsi"] == province_sel]

# Kolom area/produksi sesuai kepemilikan terpilih
if own_key == "Total":
    area_col, prod_col, prodv_col = "Total_Area", "Total_Produksi", "Produktivitas_Total"
else:
    area_col = f"Luas_Area_{own_key}"
    prod_col = f"Produksi_{own_key}"
    prodv_col = f"Produktivitas_{own_key}"

# ----------------------------------------------------------------------------
# Header
# ----------------------------------------------------------------------------
st.title("Raksasa Sawit: Dari Kebun ke Devisa")
st.markdown(
    "Bagaimana industri sawit Indonesia berkembang, di mana produksi terkonsentrasi, "
    "dan provinsi mana yang paling produktif — *2010 hingga 2023*."
)

# ----------------------------------------------------------------------------
# Row 1: KPI Cards
# ----------------------------------------------------------------------------
latest_year = y1
m_latest = m[m["Tahun"] == latest_year]

total_area = m_latest[area_col].sum()
total_prod = m_latest[prod_col].sum()
productivity = (total_prod / total_area) if total_area > 0 else 0
n_provinces = (m_latest[m_latest[prod_col] > 0]["Provinsi"].nunique())

# Ekspor tahun terakhir (hanya relevan untuk "Semua" & "Semua Provinsi")
eksim_latest = eksim[eksim["Tahun"] == latest_year]
export_val = eksim_latest["Ekspor_Nilai_000USD"].sum() / 1e6 if not eksim_latest.empty else 0  # miliar USD

c1, c2, c3, c4, c5 = st.columns(5)
c1.metric(f"Total Luas ({latest_year})", f"{total_area/1e6:.2f} jt ha")
c2.metric(f"Total Produksi ({latest_year})", f"{total_prod/1e6:.2f} jt ton")
c3.metric("Produktivitas", f"{productivity:.2f} ton/ha")
c4.metric("Nilai Ekspor", f"${export_val:.1f} M")
c5.metric("Provinsi Produsen", f"{n_provinces}")

st.markdown("---")

# ----------------------------------------------------------------------------
# Row 2: Peta (kiri) + Donut kepemilikan (kanan)
# ----------------------------------------------------------------------------
col_map, col_donut = st.columns([7, 3])

with col_map:
    st.subheader(f"Distribusi Produksi per Provinsi ({latest_year})")

    map_df = metrics[metrics["Tahun"] == latest_year].copy()
    map_df["geo_name"] = map_df["Provinsi"].map(geo_map)
    map_df = map_df.dropna(subset=["geo_name"])

    fig_map = px.choropleth(
        map_df,
        geojson=geojson,
        locations="geo_name",
        featureidkey="properties.Propinsi",
        color=prod_col,
        color_continuous_scale="YlOrBr",
        hover_name="Provinsi",
        hover_data={
            "geo_name": False,
            area_col: ":,.0f",
            prod_col: ":,.0f",
            prodv_col: ":.2f",
        },
        labels={
            area_col: "Luas (ha)",
            prod_col: "Produksi (ton)",
            prodv_col: "Produktivitas",
        },
    )
    fig_map.update_geos(fitbounds="locations", visible=False)
    fig_map.update_layout(
        margin=dict(l=0, r=0, t=0, b=0),
        height=420,
        coloraxis_colorbar=dict(title="Produksi<br>(ton)"),
    )
    st.plotly_chart(fig_map, use_container_width=True)

with col_donut:
    st.subheader("Komposisi Kepemilikan")

    own_latest = ownership[ownership["Tahun"] == latest_year]
    if not own_latest.empty:
        row = own_latest.iloc[0]
        donut_df = pd.DataFrame({
            "Kepemilikan": ["Rakyat (PR)", "Swasta (PBS)", "Negara (PBN)"],
            "Produksi": [row["PR_Produksi"], row["PBS_Produksi"], row["PBN_Produksi"]],
        })
        fig_donut = px.pie(
            donut_df,
            names="Kepemilikan",
            values="Produksi",
            hole=0.55,
            color="Kepemilikan",
            color_discrete_map={
                "Rakyat (PR)": GREEN_LIGHT,
                "Swasta (PBS)": ORANGE,
                "Negara (PBN)": TEAL,
            },
        )
        fig_donut.update_traces(textposition="inside", textinfo="percent")
        fig_donut.update_layout(
            margin=dict(l=0, r=0, t=0, b=0),
            height=420,
            legend=dict(orientation="h", yanchor="bottom", y=-0.2),
        )
        st.plotly_chart(fig_donut, use_container_width=True)

st.markdown("---")

# ----------------------------------------------------------------------------
# Row 3: Tren produksi (kiri) + Bubble chart provinsi (kanan)
# ----------------------------------------------------------------------------
col_trend, col_bubble = st.columns([6, 4])

with col_trend:
    title_suffix = "" if province_sel == "Semua Provinsi" else f" — {province_sel}"
    st.subheader(f"Tren Produksi{title_suffix}")

    if province_sel == "Semua Provinsi":
        trend_df = m.groupby("Tahun", as_index=False)[prod_col].sum()
    else:
        trend_df = m.groupby("Tahun", as_index=False)[prod_col].sum()

    fig_trend = px.line(
        trend_df,
        x="Tahun",
        y=prod_col,
        markers=True,
        labels={prod_col: "Produksi (ton)"},
    )
    fig_trend.update_traces(line_color=GREEN, marker_color=GREEN)
    fig_trend.update_layout(
        margin=dict(l=0, r=0, t=10, b=0),
        height=380,
        hovermode="x unified",
    )
    st.plotly_chart(fig_trend, use_container_width=True)

with col_bubble:
    st.subheader(f"Efisiensi Provinsi ({latest_year})")

    bub_df = metrics[metrics["Tahun"] == latest_year].copy()
    bub_df = bub_df[bub_df["Total_Produksi"] > 0]

    fig_bub = px.scatter(
        bub_df,
        x="Total_Area",
        y="Total_Produksi",
        size="Pangsa_Produksi_Nasional_Persen",
        color="Produktivitas_Total",
        color_continuous_scale="YlOrBr",
        hover_name="Provinsi",
        size_max=45,
        labels={
            "Total_Area": "Luas (ha)",
            "Total_Produksi": "Produksi (ton)",
            "Produktivitas_Total": "Produktivitas",
        },
    )
    # Highlight provinsi terpilih
    if province_sel != "Semua Provinsi":
        sel = bub_df[bub_df["Provinsi"] == province_sel]
        if not sel.empty:
            fig_bub.add_trace(go.Scatter(
                x=sel["Total_Area"], y=sel["Total_Produksi"],
                mode="markers",
                marker=dict(size=18, color="rgba(0,0,0,0)",
                            line=dict(color=ORANGE, width=3)),
                hoverinfo="skip", showlegend=False,
            ))
    fig_bub.update_layout(
        margin=dict(l=0, r=0, t=10, b=0),
        height=380,
    )
    st.plotly_chart(fig_bub, use_container_width=True)

st.markdown("---")

# ----------------------------------------------------------------------------
# Row 4: Sankey - Dari Kebun ke Devisa
# ----------------------------------------------------------------------------
st.subheader(f"Aliran Sawit: Dari Kebun ke Devisa ({latest_year})")
st.markdown(
    "Bagaimana produksi mengalir dari **jenis kepemilikan** → **provinsi utama** → "
    "**produksi nasional** → terbelah menjadi **ekspor** dan **konsumsi domestik**."
)

sk = dl.build_sankey(latest_year, top_n=6)

# Warna node: kepemilikan, provinsi (abu kehijauan), nasional, ekspor, domestik
node_colors = []
for name in sk["labels"]:
    if name in ("Rakyat", "Swasta", "Negara"):
        node_colors.append({"Rakyat": GREEN_LIGHT, "Swasta": ORANGE, "Negara": TEAL}[name])
    elif name == "Produksi Nasional":
        node_colors.append(GREEN)
    elif name == "Ekspor":
        node_colors.append(ORANGE)
    elif name == "Domestik":
        node_colors.append(AMBER)
    else:
        node_colors.append("#9DB87C")  # provinsi

fig_sankey = go.Figure(go.Sankey(
    arrangement="snap",
    node=dict(
        label=[f"{n}" for n in sk["labels"]],
        color=node_colors,
        pad=16,
        thickness=18,
        line=dict(color="rgba(0,0,0,0.2)", width=0.5),
        hovertemplate="%{label}: %{value:,.0f} ton<extra></extra>",
    ),
    link=dict(
        source=sk["sources"],
        target=sk["targets"],
        value=sk["values"],
        color="rgba(124,179,66,0.25)",
        hovertemplate="%{source.label} → %{target.label}<br>%{value:,.0f} ton<extra></extra>",
    ),
))
fig_sankey.update_layout(
    margin=dict(l=0, r=0, t=10, b=0),
    height=440,
    font=dict(size=12),
)
st.plotly_chart(fig_sankey, use_container_width=True)

# Catatan ketersediaan data lapis negara tujuan
if latest_year < dl.DEST_YEAR_MIN:
    st.info(
        f"ℹ️ Rincian **negara tujuan ekspor** belum tersedia untuk {latest_year} "
        f"(data BPS dimulai {dl.DEST_YEAR_MIN}). Aliran berhenti di node *Ekspor*."
    )

st.caption(
    "Catatan: Bubble chart — sumbu X = luas, Y = produksi (kemiringan = produktivitas), "
    "ukuran = pangsa produksi nasional. Angka ekspor = volume CPO (Pusdatin Kementan); "
    "konsumsi domestik dihitung sebagai sisa (produksi − ekspor). "
    "Lapis negara tujuan & rincian konsumsi domestik menyusul."
)
