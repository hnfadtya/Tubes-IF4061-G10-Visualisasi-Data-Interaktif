"""
Data loading & preparation untuk Indonesia Palm Oil Dashboard.
Membaca CSV induk + turunan, plus GeoJSON provinsi.
Semua fungsi di-cache agar dashboard responsif.
"""
import json
from pathlib import Path

import pandas as pd
import streamlit as st

DATA_DIR = Path(__file__).parent / "data"
PROCESSED_DIR = DATA_DIR / "processed"

# Mapping nama provinsi (data -> properti GeoJSON "Propinsi")
# Sebagian besar cocok via normalisasi; ini hanya untuk yang khusus.
PROV_TO_GEO = {
    "Aceh": "DI. ACEH",
    "D.I. Yogyakarta": "DAERAH ISTIMEWA YOGYAKARTA",
}


def _norm(s: str) -> str:
    return s.upper().replace(".", "").replace(" ", "")


@st.cache_data
def load_province_metrics() -> pd.DataFrame:
    """Data per provinsi per tahun: luas, produksi, produktivitas per kepemilikan + total."""
    return pd.read_csv(PROCESSED_DIR / "palm_oil_province_metrics_by_year.csv")


@st.cache_data
def load_ownership() -> pd.DataFrame:
    """Komposisi kepemilikan nasional per tahun (PBN/PBS/PR)."""
    return pd.read_csv(PROCESSED_DIR / "palm_oil_ownership_composition_by_year.csv")


@st.cache_data
def load_national_trend() -> pd.DataFrame:
    """Tren produksi & luas nasional per tahun."""
    return pd.read_csv(PROCESSED_DIR / "palm_oil_national_trend_by_year.csv")


@st.cache_data
def load_export_import() -> pd.DataFrame:
    """Ekspor-impor nasional (CPO) per tahun: volume, nilai, neraca."""
    return pd.read_csv(DATA_DIR / "ekspor_impor_palm_oil_2010_2023.csv")


@st.cache_data
def load_geojson() -> dict:
    """GeoJSON 34 provinsi Indonesia."""
    with open(DATA_DIR / "indonesia-prov.geojson") as f:
        return json.load(f)


@st.cache_data
def build_geo_id_map() -> dict:
    """Map nama provinsi di data -> nama 'Propinsi' di GeoJSON."""
    geo = load_geojson()
    geo_names = [f["properties"]["Propinsi"] for f in geo["features"]]
    geo_norm = {_norm(g): g for g in geo_names}
    metrics = load_province_metrics()
    mapping = {}
    for p in metrics["Provinsi"].unique():
        if p in PROV_TO_GEO:
            mapping[p] = PROV_TO_GEO[p]
        elif _norm(p) in geo_norm:
            mapping[p] = geo_norm[_norm(p)]
    return mapping


@st.cache_data
def build_sankey(year: int, top_n: int = 6) -> dict:
    """Bangun struktur node & link Sankey untuk satu tahun.

    Alur: Kepemilikan -> Top-N Provinsi + Lainnya -> Produksi Nasional
          -> Ekspor / Domestik.
    Semua angka diturunkan dari data sendiri sehingga aliran balance.
    """
    metrics = load_province_metrics()
    eksim = load_export_import()

    m = metrics[metrics["Tahun"] == year].copy()
    m = m[m["Total_Produksi"] > 0]

    # --- Tentukan top-N provinsi + gabung sisanya jadi "Provinsi Lain" ---
    top = m.nlargest(top_n, "Total_Produksi")
    top_names = list(top["Provinsi"])
    prov_labels = top_names + ["Provinsi Lain"]

    own_types = ["Rakyat", "Swasta", "Negara"]

    # --- Daftar node ---
    nodes = own_types + prov_labels + ["Produksi Nasional", "Ekspor", "Domestik"]
    idx = {name: i for i, name in enumerate(nodes)}

    sources, targets, values = [], [], []

    # Link 1: kepemilikan -> provinsi
    for _, row in m.iterrows():
        prov = row["Provinsi"] if row["Provinsi"] in top_names else "Provinsi Lain"
        for own in own_types:
            val = row[f"Produksi_{own}"]
            if val > 0:
                sources.append(idx[own])
                targets.append(idx[prov])
                values.append(float(val))

    # Link 2: provinsi -> produksi nasional
    for prov in prov_labels:
        if prov == "Provinsi Lain":
            val = m[~m["Provinsi"].isin(top_names)]["Total_Produksi"].sum()
        else:
            val = m[m["Provinsi"] == prov]["Total_Produksi"].sum()
        if val > 0:
            sources.append(idx[prov])
            targets.append(idx["Produksi Nasional"])
            values.append(float(val))

    # Link 3: produksi nasional -> ekspor / domestik
    total_nasional = m["Total_Produksi"].sum()
    exp_row = eksim[eksim["Tahun"] == year]
    ekspor = float(exp_row["Ekspor_Volume_Ton"].iloc[0]) if not exp_row.empty else 0.0
    ekspor = min(ekspor, total_nasional)  # jaga-jaga agar tidak melebihi produksi
    domestik = total_nasional - ekspor

    sources += [idx["Produksi Nasional"], idx["Produksi Nasional"]]
    targets += [idx["Ekspor"], idx["Domestik"]]
    values += [ekspor, domestik]

    return {
        "labels": nodes,
        "sources": sources,
        "targets": targets,
        "values": values,
        "own_types": own_types,
        "prov_labels": prov_labels,
        "ekspor": ekspor,
        "domestik": domestik,
        "total": total_nasional,
    }


# Konstanta periode
YEAR_MIN = 2010
YEAR_MAX = 2023
DEST_YEAR_MIN = 2012  # lapis negara tujuan baru tersedia mulai 2012
