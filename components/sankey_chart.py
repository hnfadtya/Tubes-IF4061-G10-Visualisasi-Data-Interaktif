"""Sankey 'Dari Kebun ke Devisa'.

Alur aliran (volume, ton):
  Kepemilikan (Rakyat/Swasta/Negara)
    -> Top-N provinsi + 'Provinsi Lain'
      -> Produksi Nasional
        -> Ekspor / Domestik
           - Ekspor pecah ke top negara tujuan + 'Negara Lain'
             (proporsi dari BPS, diterapkan ke volume ekspor data utama)
           - Domestik berhenti sebagai satu node agregat (produksi - ekspor)

Catatan data:
  - Produksi & kepemilikan: data provinsi (CPO).
  - Ekspor: data ekspor-impor (CPO).
  - Proporsi negara tujuan: BPS (CPO+CPKO) -> dipakai sebagai persentase saja
    agar total tetap balance dengan node Ekspor.
  - Lapis negara tujuan hanya tersedia mulai DEST_YEAR_MIN (2012).
"""
import csv
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
BPS_FILE = DATA_DIR / "Ekspor_Minyak_Kelapa_Sawit_Menurut_Negara_Tujuan_Utama__2012-2024.csv"

DEST_YEAR_MIN = 2012  # lapis negara tujuan baru tersedia mulai tahun ini

# Palet selaras poster tubes 1
GREEN = "#3B6D11"
GREEN_LIGHT = "#97C459"
ORANGE = "#D2601A"
AMBER = "#E8A317"
TEAL = "#1D9E75"
PROV_COLOR = "#9DB87C"
DEST_COLOR = "#C0DD97"

OWN_COLORS = {"Rakyat": GREEN_LIGHT, "Swasta": ORANGE, "Negara": TEAL}


def _load_bps_volume():
    """Parse blok volume (000 ton) dari file BPS -> {negara: {tahun: nilai}}."""
    rows = list(csv.reader(open(BPS_FILE, encoding="utf-8-sig")))
    years = [int(y) for y in rows[2][1:14]]
    vol = {}
    for r in rows[4:]:
        name = r[0].strip()
        if name == "Jumlah":
            break
        if name == "" or name.startswith("Nilai"):
            continue
        vals = [float(c.strip().replace(",", "")) if c.strip() else 0.0 for c in r[1:14]]
        vol[name] = dict(zip(years, vals))
    return vol


_BPS_VOL = None


def _bps_volume():
    global _BPS_VOL
    if _BPS_VOL is None:
        _BPS_VOL = _load_bps_volume()
    return _BPS_VOL


def _dest_proportions(year, top_k=6):
    """Proporsi negara tujuan untuk satu tahun: (list[(negara, prop)], prop_lain).

    Mengembalikan None jika tahun di luar cakupan data BPS.
    """
    vol = _bps_volume()
    any_year = next(iter(vol.values()))
    if year not in any_year:
        return None
    total = sum(v[year] for v in vol.values())
    if total <= 0:
        return None
    ranked = sorted(
        [(n, v[year]) for n, v in vol.items() if n != "Lainnya"],
        key=lambda x: -x[1],
    )
    top = ranked[:top_k]
    props = [(n, val / total) for n, val in top]
    prop_lain = 1.0 - sum(p for _, p in props)
    return props, max(prop_lain, 0.0)


def create_sankey(df_prov, df_ekspor, year, kepemilikan, top_n=6):
    """Bangun figure Sankey untuk satu tahun.

    df_prov     : data provinsi mentah (punya kolom Produksi_<Kepemilikan>, Total_Produksi)
    df_ekspor   : data ekspor-impor (punya Ekspor_Volume_Ton per Tahun)
    year        : tahun snapshot (int)
    kepemilikan : list subset dari ['Rakyat','Swasta','Negara']
    """
    own_types = [k for k in ["Rakyat", "Swasta", "Negara"] if k in kepemilikan]
    if not own_types:
        own_types = ["Rakyat", "Swasta", "Negara"]

    m = df_prov[df_prov["Tahun"] == year].copy()

    # produksi per provinsi (sesuai kepemilikan terpilih)
    prod_cols = [f"Produksi_{k}" for k in own_types]
    m["ProdFilter"] = m[prod_cols].sum(axis=1)
    m = m[m["ProdFilter"] > 0]

    # top-N provinsi + gabung sisanya
    top = m.nlargest(top_n, "ProdFilter")
    top_names = list(top["Provinsi"])
    prov_labels = top_names + ["Provinsi Lain"]

    # daftar node dasar
    nodes = list(own_types) + prov_labels + ["Produksi Nasional", "Ekspor", "Domestik"]

    sources, targets, values, link_colors = [], [], [], []

    def add(idx_map, s, t, v):
        if v > 0:
            sources.append(idx_map[s])
            targets.append(idx_map[t])
            values.append(float(v))

    # Link 1: kepemilikan -> provinsi
    total_nasional = float(m["ProdFilter"].sum())
    exp_row = df_ekspor[df_ekspor["Tahun"] == year]
    ekspor = float(exp_row["Ekspor_Volume_Ton"].iloc[0]) if not exp_row.empty else 0.0
    ekspor = min(ekspor, total_nasional)
    domestik = total_nasional - ekspor

    # tambah node negara tujuan jika tersedia
    dest = _dest_proportions(year, top_k=6) if year >= DEST_YEAR_MIN else None
    dest_labels = []
    if dest is not None:
        props, prop_lain = dest
        dest_labels = [n for n, _ in props] + ["Negara Lain"]
        nodes = nodes + dest_labels

    idx = {name: i for i, name in enumerate(nodes)}

    # Link 1
    for _, row in m.iterrows():
        prov = row["Provinsi"] if row["Provinsi"] in top_names else "Provinsi Lain"
        for own in own_types:
            add(idx, own, prov, row[f"Produksi_{own}"])

    # Link 2: provinsi -> nasional
    for prov in prov_labels:
        if prov == "Provinsi Lain":
            val = m[~m["Provinsi"].isin(top_names)]["ProdFilter"].sum()
        else:
            val = m[m["Provinsi"] == prov]["ProdFilter"].sum()
        add(idx, prov, "Produksi Nasional", val)

    # Link 3: nasional -> ekspor / domestik
    add(idx, "Produksi Nasional", "Ekspor", ekspor)
    add(idx, "Produksi Nasional", "Domestik", domestik)

    # Link 4: ekspor -> negara tujuan (proporsi)
    if dest is not None:
        props, prop_lain = dest
        for n, p in props:
            add(idx, "Ekspor", n, p * ekspor)
        add(idx, "Ekspor", "Negara Lain", prop_lain * ekspor)

    # warna node
    node_colors = []
    for name in nodes:
        if name in OWN_COLORS:
            node_colors.append(OWN_COLORS[name])
        elif name == "Produksi Nasional":
            node_colors.append(GREEN)
        elif name == "Ekspor":
            node_colors.append(ORANGE)
        elif name == "Domestik":
            node_colors.append(AMBER)
        elif name in prov_labels:
            node_colors.append(PROV_COLOR)
        else:
            node_colors.append(DEST_COLOR)

    fig = go.Figure(go.Sankey(
        arrangement="snap",
        node=dict(
            label=nodes,
            color=node_colors,
            pad=16,
            thickness=18,
            line=dict(color="rgba(0,0,0,0.15)", width=0.5),
            hovertemplate="%{label}: %{value:,.0f} ton<extra></extra>",
        ),
        link=dict(
            source=sources,
            target=targets,
            value=values,
            color="rgba(124,179,66,0.25)",
            hovertemplate="%{source.label} → %{target.label}<br>%{value:,.0f} ton<extra></extra>",
        ),
    ))
    fig.update_layout(
        margin={"l": 8, "r": 8, "t": 8, "b": 8},
        font=dict(size=12, color="#374151"),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
    )
    return fig, (dest is None)
