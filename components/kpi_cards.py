from dash import html
from dash_svg import Svg, Path, Circle
import pandas as pd

def _fmt(n, suffix=''):
    if n >= 1_000_000: return f"{n/1_000_000:.2f} jt{suffix}"
    if n >= 1_000:     return f"{n/1_000:.1f} rb{suffix}"
    return f"{n:.0f}{suffix}"

def _delta_badge(val_awal, val_akhir):
    if val_awal == 0:
        return None, None
    pct = (val_akhir - val_awal) / val_awal * 100
    if pct > 0:
        return f"↑ +{pct:.1f}%", {'bg': '#E1F5EE', 'text': '#085041'}
    if pct < 0:
        return f"↓ {pct:.1f}%",  {'bg': '#FCEBEB', 'text': '#791F1F'}
    return "→ Tetap", {'bg': '#F1EFE8', 'text': '#444441'}

def create_kpi_cards(df_prov, df_ekspor, tahun_range, provinsi, kepemilikan):
    t_awal, t_akhir = tahun_range

    if provinsi != 'ALL':
        df_prov = df_prov[df_prov['Provinsi'] == provinsi]

    kepemilikan_lower = [k.lower() for k in kepemilikan]
    
    luas_cols = [c for c in ['Luas_Area_Negara', 'Luas_Area_Swasta', 'Luas_Area_Rakyat'] 
                 if c.replace('Luas_Area_','').lower() in kepemilikan_lower and c in df_prov.columns]
                 
    prod_cols = [c for c in ['Produksi_Negara', 'Produksi_Swasta', 'Produksi_Rakyat'] 
                 if c.replace('Produksi_','').lower() in kepemilikan_lower and c in df_prov.columns]

    def get_values(tahun):
        df = df_prov[df_prov['Tahun'] == tahun]
        
        luas = df[luas_cols].sum().sum() if luas_cols else (df['Total_Area'].sum() if 'Total_Area' in df.columns else 0)
        prod = df[prod_cols].sum().sum() if prod_cols else (df['Total_Produksi'].sum() if 'Total_Produksi' in df.columns else 0)
        produktivitas = prod / luas if luas > 0 else 0
        
        eks_row = df_ekspor[df_ekspor['Tahun'] == tahun]
        ekspor = eks_row['Ekspor_Nilai_000USD'].values[0] if len(eks_row) > 0 else 0
        jml_provinsi = df['Provinsi'].nunique()
        
        return luas, prod, produktivitas, ekspor, jml_provinsi

    v0 = get_values(t_awal)
    v1 = get_values(t_akhir)
    
    # Rata-rata pertumbuhan produksi tahunan dalam rentang
    df_growth = df_prov[
        (df_prov['Tahun'] >= t_awal) &
        (df_prov['Tahun'] <= t_akhir)
    ].copy()

    if prod_cols:
        df_growth['Produksi'] = df_growth[prod_cols].sum(axis=1)
    else:
        df_growth['Produksi'] = df_growth['Total_Produksi']

    df_growth = (
        df_growth
        .groupby('Tahun')['Produksi']
        .sum()
        .reset_index()
        .sort_values('Tahun')
    )

    if len(df_growth) >= 2:
        df_growth['growth'] = df_growth['Produksi'].pct_change() * 100
        avg_growth = df_growth['growth'].dropna().mean()
    else:
        avg_growth = 0

    defs = [
        ("Total Luas Area",  _fmt(v1[0], ' ha'),        v0[0], v1[0], "#E6F1FB", "#185FA5", "area"),
        ("Total Produksi",   _fmt(v1[1], ' ton'),       v0[1], v1[1], "#EAF3DE", "#3B6D11", "produksi"),
        ("Produktivitas",    f"{v1[2]:.2f} ton/ha",     v0[2], v1[2], "#FAEEDA", "#854F0B", "produktivitas"),
        ("Nilai Ekspor",     f"${_fmt(v1[3])}",         v0[3], v1[3], "#E1F5EE", "#0F6E56", "ekspor"),
        (
            "Pertumbuhan Produksi/Tahun",
            f"{avg_growth:.2f}%",
            0,
            avg_growth,
            "#EEEDFE",
            "#534AB7",
            "growth"
        ),
    ]

    cards = []

    for label, value, awal, akhir, bg, fg, icon_type in defs:
        badge_text, badge_style = _delta_badge(awal, akhir)
        ref_text = f"vs {t_awal}" if t_awal != t_akhir else None
        if icon_type == "growth":
            badge_text = None
            ref_text = f"{t_awal}–{t_akhir}"

        if icon_type == "area":
            icon_svg = Svg([
                Path(d="M12 2L2 7l10 5 10-5-10-5z", stroke=fg, strokeWidth="2", fill="none"),
                Path(d="M2 17l10 5 10-5", stroke=fg, strokeWidth="2", fill="none"),
                Path(d="M2 12l10 5 10-5", stroke=fg, strokeWidth="2", fill="none")
            ], viewBox="0 0 24 24", style={'width': '16px', 'height': '16px'})
        elif icon_type == "produksi":
            icon_svg = Svg([
                Path(d="M21 16V8a2 2 0 00-1-1.73l-7-4a2 2 0 00-2 0l-7 4A2 2 0 003 8v8a2 2 0 001 1.73l7 4a2 2 0 002 0l7-4A2 2 0 0021 16z", stroke=fg, strokeWidth="2", fill="none"),
                Path(d="M3.27 6.96L12 12.01l8.73-5-8.73 5V22", stroke=fg, strokeWidth="2", fill="none")
            ], viewBox="0 0 24 24", style={'width': '16px', 'height': '16px'})
        elif icon_type == "produktivitas":
            icon_svg = Svg([
                Path(d="M23 6l-9.5 9.5-5-5L1 18M17 6h6v6", stroke=fg, strokeWidth="2", fill="none", strokeLinecap="round", strokeLinejoin="round")
            ], viewBox="0 0 24 24", style={'width': '16px', 'height': '16px'})
        elif icon_type == "ekspor":
            icon_svg = Svg([
                Circle(cx="12", cy="12", r="10", stroke=fg, strokeWidth="2", fill="none"),
                Path(d="M2 12h20M12 2a15.3 15.3 0 014 10 15.3 15.3 0 01-4 10 15.3 15.3 0 01-4-10 15.3 15.3 0 014-10z", stroke=fg, strokeWidth="2", fill="none")
            ], viewBox="0 0 24 24", style={'width': '16px', 'height': '16px'})
        elif icon_type == "growth":
            icon_svg = Svg([
                Path(
                    d="M4 16l5-5 4 4 7-7",
                    stroke=fg,
                    strokeWidth="2",
                    fill="none",
                    strokeLinecap="round",
                    strokeLinejoin="round"
                ),
                Path(
                    d="M15 8h5v5",
                    stroke=fg,
                    strokeWidth="2",
                    fill="none",
                    strokeLinecap="round",
                    strokeLinejoin="round"
                )
            ], viewBox="0 0 24 24",
            style={'width': '16px', 'height': '16px'})
        else:  # provinsi
            icon_svg = Svg([
                Path(d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0118 0z", stroke=fg, strokeWidth="2", fill="none"),
                Circle(cx="12", cy="10", r="3", stroke=fg, strokeWidth="2", fill="none")
            ], viewBox="0 0 24 24", style={'width': '16px', 'height': '16px'})

        cards.append(
            html.Div([
                # Header
                html.Div([
                    html.P(label, style={'fontSize': '13px', 'fontWeight': '600', 'color': '#64748B', 'margin': '0'}),
                    html.Div(icon_svg, style={
                        'backgroundColor': bg, 'width': '30px', 'height': '30px', 'borderRadius': '8px',
                        'display': 'flex', 'alignItems': 'center', 'justifyContent': 'center', 'flexShrink': '0'
                    })
                ], style={'display': 'flex', 'justifyContent': 'space-between', 'alignItems': 'center'}),

                # Value
                html.Div(value, style={
                    'fontSize': '28px', 'fontWeight': '700', 'color': '#111827', 'marginTop': '12px', 'lineHeight': '1.1'
                }),

                # Footer 
                html.Div([
                    html.Span(badge_text, style={
                        'fontSize': '11px', 'fontWeight': '600', 'padding': '4px 10px', 'borderRadius': '999px',
                        'backgroundColor': badge_style['bg'], 'color': badge_style['text']
                    }) if badge_text else None,
                    html.Span(ref_text, style={'fontSize': '11px', 'color': '#94A3B8', 'marginLeft': '8px'}) if ref_text else None,
                ], style={'display': 'flex', 'alignItems': 'center', 'marginTop': '14px'})

            ], style={
                'backgroundColor': '#FFFFFF', 'border': '1px solid #E5E7EB', 'borderRadius': '18px',
                'padding': '22px', 'height': '140px', 'display': 'flex', 'flexDirection': 'column',
                'justifyContent': 'space-between', 'boxShadow': '0 4px 12px rgba(0,0,0,0.05)', 'transition': 'all 0.2s ease'
            })
        )

    return cards