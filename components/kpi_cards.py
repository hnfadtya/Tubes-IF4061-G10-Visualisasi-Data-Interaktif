from dash import html
import pandas as pd

def create_kpi_cards(df_prov, df_ekspor, tahun_range, provinsi, kepemilikan):
    t_min, t_max = tahun_range

    df = df_prov[(df_prov['Tahun'] >= t_min) & (df_prov['Tahun'] <= t_max)]
    if provinsi != 'ALL':
        df = df[df['Provinsi'] == provinsi]

    df_eks = df_ekspor[(df_ekspor['Tahun'] >= t_min) & (df_ekspor['Tahun'] <= t_max)]
    df_last = df[df['Tahun'] == df['Tahun'].max()]
    luas_cols  = [c for c in ['Luas_Area_Negara','Luas_Area_Swasta','Luas_Area_Rakyat'] 
                  if c.replace('Luas_Area_','') in kepemilikan or 
                  c.replace('Luas_Area_','').lower() in [k.lower() for k in kepemilikan]]
    prod_cols  = [c for c in ['Produksi_Negara','Produksi_Swasta','Produksi_Rakyat']
                  if c.replace('Produksi_','') in kepemilikan or
                  c.replace('Produksi_','').lower() in [k.lower() for k in kepemilikan]]

    total_luas      = df_last[luas_cols].sum().sum()   if luas_cols  else df_last['Total_Area'].sum()
    total_produksi  = df_last[prod_cols].sum().sum()   if prod_cols  else df_last['Total_Produksi'].sum()
    produktivitas   = (total_produksi / total_luas) if total_luas > 0 else 0
    ekspor_nilai    = df_eks['Ekspor_Nilai_000USD'].iloc[-1] if len(df_eks) > 0 else 0
    jml_provinsi    = df_last['Provinsi'].nunique()

    def fmt_number(n, suffix=''):
        if n >= 1_000_000:
            return f"{n/1_000_000:.2f} jt{suffix}"
        elif n >= 1_000:
            return f"{n/1_000:.1f} rb{suffix}"
        return f"{n:.0f}{suffix}"

    cards = [
        ("Total Luas Area",      fmt_number(total_luas, ' ha'),     "#E6F1FB", "#185FA5"),
        ("Total Produksi",       fmt_number(total_produksi, ' ton'),"#EAF3DE", "#3B6D11"),
        ("Produktivitas",        f"{produktivitas:.2f} ton/ha",     "#FAEEDA", "#854F0B"),
        ("Nilai Ekspor",         f"${fmt_number(ekspor_nilai)}",    "#E1F5EE", "#0F6E56"),
        ("Jumlah Provinsi",      str(jml_provinsi),                 "#EEEDFE", "#534AB7"),
    ]

    return [
        html.Div([
            html.P(label, style={
                'fontSize': '11px', 'color': color_text,
                'margin': '0 0 6px', 'fontWeight': '500',
                'textTransform': 'uppercase', 'letterSpacing': '0.05em'
            }),
            html.P(value, style={
                'fontSize': '22px', 'fontWeight': '600',
                'margin': '0', 'color': color_text
            }),
        ], style={
            'backgroundColor': color_bg,
            'borderRadius': '8px',
            'padding': '16px',
        })
        for label, value, color_bg, color_text in cards
    ]


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

def create_kpi_cards(df_prov, df_ekspor, tahun_range, kepemilikan):
    t_awal, t_akhir = tahun_range

    luas_cols = [f'Luas_Area_{k}' for k in kepemilikan if f'Luas_Area_{k}' in df_prov.columns]
    prod_cols = [f'Produksi_{k}'  for k in kepemilikan if f'Produksi_{k}'  in df_prov.columns]

    def get_values(tahun):
        df = df_prov[df_prov['Tahun'] == tahun]
        luas = df[luas_cols].sum().sum() if luas_cols else df['Total_Area'].sum()
        prod = df[prod_cols].sum().sum() if prod_cols else df['Total_Produksi'].sum()
        produktivitas = prod / luas if luas > 0 else 0
        eks_row = df_ekspor[df_ekspor['Tahun'] == tahun]
        ekspor = eks_row['Ekspor_Nilai_000USD'].values[0] if len(eks_row) > 0 else 0
        provinsi = df['Provinsi'].nunique()
        return luas, prod, produktivitas, ekspor, provinsi

    v0 = get_values(t_awal)
    v1 = get_values(t_akhir)

    defs = [
        ("Total Luas Area",  _fmt(v1[0], ' ha'),        v0[0], v1[0], "#E6F1FB", "#185FA5"),
        ("Total Produksi",   _fmt(v1[1], ' ton'),        v0[1], v1[1], "#EAF3DE", "#3B6D11"),
        ("Produktivitas",    f"{v1[2]:.2f} ton/ha",      v0[2], v1[2], "#FAEEDA", "#854F0B"),
        ("Nilai Ekspor",     f"${_fmt(v1[3])}",          v0[3], v1[3], "#E1F5EE", "#0F6E56"),
        ("Jumlah Provinsi",  str(v1[4]),                 v0[4], v1[4], "#EEEDFE", "#534AB7"),
    ]

    cards = []
    for label, value, awal, akhir, bg, fg in defs:
        badge_text, badge_style = _delta_badge(awal, akhir)
        ref_text = f"vs {t_awal}" if t_awal != t_akhir else None

        cards.append(html.Div([
            html.P(label, style={
                'fontSize':'11px','color':fg,'margin':'0 0 4px',
                'fontWeight':'500','textTransform':'uppercase','letterSpacing':'0.05em'
            }),
            html.P(value, style={
                'fontSize':'22px','fontWeight':'600','margin':'0 0 8px','color':fg
            }),
            html.Div([
                html.Span(badge_text, style={
                    'fontSize':'11px','fontWeight':'500',
                    'padding':'2px 8px','borderRadius':'20px',
                    'backgroundColor': badge_style['bg'],
                    'color': badge_style['text'],
                }) if badge_text else None,
                html.Span(ref_text, style={
                    'fontSize':'10px','color':fg,'opacity':'0.6','marginLeft':'6px'
                }) if ref_text else None,
            ], style={'display':'flex','alignItems':'center'}),
        ], style={
            'backgroundColor': bg, 'borderRadius':'8px', 'padding':'16px',
        }))

    return cards