import plotly.graph_objects as go
import numpy as np
import pandas as pd

GREENS_CUSTOM = [
    [0.00, '#E8EDE8'],
    [0.15, '#C5D9C2'],
    [0.35, '#8BBF88'],
    [0.60, '#4D9E50'],
    [0.80, '#1E7A35'],
    [1.00, '#0A3D1F'],
]

def _fmt_tick(val):
    """Format angka asli (bukan log) untuk label colorbar."""
    if val >= 1_000_000:
        return f"{val/1_000_000:.0f}M"
    if val >= 1_000:
        return f"{val/1_000:.0f}K"
    return str(int(val))

def create_map(df_prov, geojson, tahun_range, kepemilikan):
    t_min, t_max = tahun_range

    df = df_prov[(df_prov['Tahun'] >= t_min) & (df_prov['Tahun'] <= t_max)]

    prod_cols = [f'Produksi_{k}' for k in kepemilikan
                 if f'Produksi_{k}' in df.columns]
    if not prod_cols:
        prod_cols = ['Total_Produksi']

    df_map = df.groupby('Provinsi')[prod_cols].sum()
    df_map['Produksi_Filter'] = df_map[prod_cols].sum(axis=1)
    df_map['Total_Area']      = df.groupby('Provinsi')['Total_Area'].sum()
    df_map['Produktivitas']   = (df_map['Produksi_Filter'] / df_map['Total_Area']).round(2)
    df_map = df_map.reset_index()

    df_nonzero = df_map[df_map['Produksi_Filter'] > 0].copy()
    df_zero    = df_map[df_map['Produksi_Filter'] == 0].copy()

    df_nonzero['z_log'] = np.log1p(df_nonzero['Produksi_Filter'])

    log_min = df_nonzero['z_log'].min()
    log_max = df_nonzero['z_log'].max()

    raw_landmarks = [
        df_nonzero['Produksi_Filter'].min(),  
        np.expm1(log_min + (log_max - log_min) * 0.25),
        np.expm1(log_min + (log_max - log_min) * 0.50),
        np.expm1(log_min + (log_max - log_min) * 0.75),
        df_nonzero['Produksi_Filter'].max(),   
    ]

    tick_vals = [np.log1p(v) for v in raw_landmarks]
    tick_text = [_fmt_tick(v) for v in raw_landmarks]

    traces = []

    if not df_zero.empty:
        traces.append(go.Choroplethmapbox(
            geojson=geojson,
            locations=df_zero['Provinsi'],
            z=[0] * len(df_zero),
            featureidkey='properties.PROVINSI',
            colorscale=[[0, '#FFCCCC'], [1, '#FFCCCC']],
            showscale=False,
            showlegend=False,
            hoverinfo='skip',
            marker=dict(line_width=0.4, line_color='rgba(255,255,255,0.8)', opacity=0.85),
        ))

    if not df_nonzero.empty:
        traces.append(go.Choroplethmapbox(
            geojson=geojson,
            locations=df_nonzero['Provinsi'],
            featureidkey='properties.PROVINSI',
            z=df_nonzero['z_log'],          
            zmin=log_min,
            zmax=log_max,
            colorscale=GREENS_CUSTOM,
            showscale=True,
            showlegend=False,
            customdata=df_nonzero[['Produksi_Filter', 'Total_Area', 'Produktivitas']].values,
            hovertemplate=(
                "<b>%{location}</b><br>"
                "Produksi      : %{customdata[0]:,.0f} ton<br>"
                "Luas          : %{customdata[1]:,.0f} ha<br>"
                "Produktivitas : %{customdata[2]:.2f} ton/ha"
                "<extra></extra>"
            ),
            marker=dict(line_width=0.4, line_color='rgba(255,255,255,0.8)', opacity=0.85),
            colorbar=dict(
                title=dict(text='Produksi<br>(ton)', font=dict(size=11, color='#6B7280')),
                thickness=8,
                len=0.55,
                x=0.97,
                tickvals=tick_vals,
                ticktext=tick_text,
                tickfont=dict(size=10, color='#6B7280'),
                outlinewidth=0,
                nticks=5,       
            ),
        ))

    traces.append(go.Scattermapbox(
        lat=[-99], lon=[-99],           
        mode='markers',
        marker=dict(
            size=16,
            color='#FFCCCC',
        ),
        name='  Non Produktif',         
        hoverinfo='skip',
        showlegend=True,
    ))

    fig = go.Figure(data=traces)

    fig.update_layout(
        mapbox=dict(style='white-bg', center={'lat': -2.5, 'lon': 118}, zoom=3.5),
        margin={'r': 0, 't': 0, 'l': 0, 'b': 0},
        paper_bgcolor='rgba(0,0,0,0)',
        uirevision='map-chart',
        showlegend=True,
        legend=dict(
            x=0.01, y=0.01,
            xanchor='left', yanchor='bottom',
            bgcolor='rgba(255,255,255,0.88)',
            bordercolor='rgba(229,231,235,1)',
            borderwidth=1,
            font=dict(size=12, color='#374151', family='"Inter", sans-serif'),
            itemsizing='constant',
            itemwidth=30,
        ),
    )

    return fig


def _nice_ticks(max_val, n=5):
    import math
    if max_val <= 0:
        return [0]

    magnitude = 10 ** math.floor(math.log10(max_val))
    step_candidates = [
        magnitude * m for m in [0.1, 0.2, 0.25, 0.5, 1, 2, 2.5, 5, 10]
    ]
    step = min(step_candidates, key=lambda s: abs(max_val / s - n))

    ticks = []
    v = 0
    while v <= max_val:
        ticks.append(round(v))
        v += step
    return ticks