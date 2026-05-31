import plotly.graph_objects as go
import pandas as pd
import numpy as np
import math

REGION_MAP = {
    'Aceh':                        ('Sumatera', '#E83E8C'),
    'Sumatera Utara':              ('Sumatera', '#E83E8C'),
    'Sumatera Barat':              ('Sumatera', '#E83E8C'),
    'Riau':                        ('Sumatera', '#E83E8C'),
    'Kepulauan Riau':              ('Sumatera', '#E83E8C'),
    'Jambi':                       ('Sumatera', '#E83E8C'),
    'Sumatera Selatan':            ('Sumatera', '#E83E8C'),
    'Kepulauan Bangka Belitung':   ('Sumatera', '#E83E8C'),
    'Bengkulu':                    ('Sumatera', '#E83E8C'),
    'Lampung':                     ('Sumatera', '#E83E8C'),

    'DKI Jakarta':                 ('Jawa', '#6F42C1'),
    'Jawa Barat':                  ('Jawa', '#6F42C1'),
    'Banten':                      ('Jawa', '#6F42C1'),
    'Jawa Tengah':                 ('Jawa', '#6F42C1'),
    'Daerah Istimewa Yogyakarta':  ('Jawa', '#6F42C1'),
    'Jawa Timur':                  ('Jawa', '#6F42C1'),

    'Kalimantan Barat':            ('Kalimantan', '#1D9E75'),
    'Kalimantan Tengah':           ('Kalimantan', '#1D9E75'),
    'Kalimantan Selatan':          ('Kalimantan', '#1D9E75'),
    'Kalimantan Timur':            ('Kalimantan', '#1D9E75'),
    'Kalimantan Utara':            ('Kalimantan', '#1D9E75'),

    'Sulawesi Utara':              ('Sulawesi', '#FFC107'),
    'Gorontalo':                   ('Sulawesi', '#FFC107'),
    'Sulawesi Tengah':             ('Sulawesi', '#FFC107'),
    'Sulawesi Barat':              ('Sulawesi', '#FFC107'),
    'Sulawesi Selatan':            ('Sulawesi', '#FFC107'),
    'Sulawesi Tenggara':           ('Sulawesi', '#FFC107'),

    'Maluku':                      ('Maluku & Papua', '#378ADD'),
    'Maluku Utara':                ('Maluku & Papua', '#378ADD'),
    'Papua':                       ('Maluku & Papua', '#378ADD'),
    'Papua Barat':                 ('Maluku & Papua', '#378ADD'),
    'Papua Selatan':               ('Maluku & Papua', '#378ADD'),
    'Papua Tengah':                ('Maluku & Papua', '#378ADD'),
    'Papua Pegunungan':            ('Maluku & Papua', '#378ADD'),
    'Papua Barat Daya':            ('Maluku & Papua', '#378ADD'),
}

REGION_ORDER = ['Sumatera', 'Jawa', 'Kalimantan', 'Sulawesi', 'Maluku & Papua']
REGION_COLORS = {
    'Sumatera':              '#E83E8C',
    'Jawa':                  '#6F42C1',
    'Kalimantan':            '#1D9E75',
    'Sulawesi':              '#FFC107',
    'Maluku & Papua':        '#378ADD',
}

def _fmt_axis(val):
    if val >= 1_000_000: return f"{val/1_000_000:.0f}M"
    if val >= 1_000:     return f"{val/1_000:.0f}K"
    return str(int(val))

def create_bubble(df_prov, provinsi_highlight, kepemilikan):
    tahun_list = sorted(df_prov['Tahun'].unique())
    is_filtered = provinsi_highlight and provinsi_highlight != 'ALL'

    df_all = df_prov.copy()
    df_all['Dynamic_Area']     = 0.0
    df_all['Dynamic_Produksi'] = 0.0

    for k in ['Rakyat', 'Swasta', 'Negara']:
        if k in kepemilikan:
            if f'Luas_Area_{k}' in df_all.columns:
                df_all['Dynamic_Area']     += df_all[f'Luas_Area_{k}'].fillna(0)
            if f'Produksi_{k}' in df_all.columns:
                df_all['Dynamic_Produksi'] += df_all[f'Produksi_{k}'].fillna(0)

    kondisi_aman = df_all['Dynamic_Area'] > 0
    df_all['Produktivitas'] = 0.0
    df_all.loc[kondisi_aman, 'Produktivitas'] = (
        df_all.loc[kondisi_aman, 'Dynamic_Produksi'] /
        df_all.loc[kondisi_aman, 'Dynamic_Area']
    ).round(2)

    df_all['Region'] = df_all['Provinsi'].map(
        lambda p: REGION_MAP.get(p, ('Lainnya', '#94A3B8'))[0]
    )
    df_all['Warna'] = df_all['Provinsi'].map(
        lambda p: REGION_MAP.get(p, ('Lainnya', '#94A3B8'))[1]
    )

    prod_max = df_all['Produktivitas'].max()
    sizeref  = 2.0 * (prod_max if prod_max > 0 else 1) / (40 ** 2)

    x_max = df_all['Dynamic_Area'].max()     * 1.12 or 1000
    y_max = df_all['Dynamic_Produksi'].max() * 1.12 or 1000

    dummy_row = pd.DataFrame([{
        'Tahun': 2010, 'Provinsi': 'None', 'Region': 'Lainnya', 'Warna': '#94A3B8',
        'Dynamic_Area': np.nan, 'Dynamic_Produksi': np.nan, 'Produktivitas': 0.0
    }])

    def nice_step(mx, n=5):
        if mx <= 0: return 1
        rs = mx / n
        mag = 10 ** math.floor(math.log10(rs))
        return int(min([mag*m for m in [1,2,2.5,5,10]], key=lambda s: abs(s-rs)))

    y_tick_step = nice_step(df_all['Dynamic_Produksi'].max())
    y_tick_vals = list(range(0, int(y_max), y_tick_step))
    y_tick_text = [_fmt_axis(v) for v in y_tick_vals]

    x_tick_step = nice_step(df_all['Dynamic_Area'].max())
    x_tick_vals = list(range(0, int(x_max), x_tick_step))
    x_tick_text = [_fmt_axis(v) for v in x_tick_vals]

    frames = []
    for t in tahun_list:
        df_t = df_all[df_all['Tahun'] == t]
        traces = []

        for region in REGION_ORDER:
            warna = REGION_COLORS[region]
            df_r  = df_t[df_t['Region'] == region]

            if is_filtered:
                df_lain  = df_r[df_r['Provinsi'] != provinsi_highlight]
                df_pilih = df_r[df_r['Provinsi'] == provinsi_highlight]

                if not df_lain.empty:
                    traces.append(go.Scatter(
                        x=df_lain['Dynamic_Area'],
                        y=df_lain['Dynamic_Produksi'],
                        mode='markers',
                        name=region,
                        legendgroup=region,
                        showlegend=True,
                        marker=dict(
                            size=df_lain['Produktivitas'].fillna(0),
                            sizemode='area', sizeref=sizeref, sizemin=5,
                            color=warna,
                            opacity=0.2,
                            line=dict(width=0),
                        ),
                        text=df_lain['Provinsi'],
                        customdata=df_lain[['Dynamic_Area','Dynamic_Produksi','Produktivitas']].fillna(0).values,
                        hovertemplate=(
                            '<b>%{text}</b><br>'
                            'Luas: %{customdata[0]:,.0f} ha<br>'
                            'Produksi: %{customdata[1]:,.0f} ton<br>'
                            'Produktivitas: %{customdata[2]:.2f} ton/ha'
                            '<extra></extra>'
                        ),
                    ))

                if not df_pilih.empty:
                    traces.append(go.Scatter(
                        x=df_pilih['Dynamic_Area'],
                        y=df_pilih['Dynamic_Produksi'],
                        mode='markers',
                        name=f'{provinsi_highlight} ★',
                        legendgroup='highlight',
                        showlegend=True,
                        marker=dict(
                            size=df_pilih['Produktivitas'].fillna(0),
                            sizemode='area', sizeref=sizeref, sizemin=8,
                            color=warna,
                            opacity=1.0,
                            line=dict(width=3, color='white'),
                        ),
                        text=df_pilih['Provinsi'],
                        customdata=df_pilih[['Dynamic_Area','Dynamic_Produksi','Produktivitas']].fillna(0).values,
                        hovertemplate=(
                            '<b>%{text}</b> ★<br>'
                            'Luas: %{customdata[0]:,.0f} ha<br>'
                            'Produksi: %{customdata[1]:,.0f} ton<br>'
                            'Produktivitas: %{customdata[2]:.2f} ton/ha'
                            '<extra></extra>'
                        ),
                    ))
            else:
                if df_r.empty:
                    df_r = dummy_row[dummy_row['Region'] == region] if region in dummy_row['Region'].values else dummy_row

                traces.append(go.Scatter(
                    x=df_r['Dynamic_Area'],
                    y=df_r['Dynamic_Produksi'],
                    mode='markers',
                    name=region,
                    legendgroup=region,
                    showlegend=True,
                    marker=dict(
                        size=df_r['Produktivitas'].fillna(0),
                        sizemode='area', sizeref=sizeref, sizemin=5,
                        color=warna,
                        opacity=0.75,
                        line=dict(width=1.5, color='white'),
                    ),
                    text=df_r['Provinsi'],
                    customdata=df_r[['Dynamic_Area','Dynamic_Produksi','Produktivitas']].fillna(0).values,
                    hovertemplate=(
                        '<b>%{text}</b><br>'
                        'Luas: %{customdata[0]:,.0f} ha<br>'
                        'Produksi: %{customdata[1]:,.0f} ton<br>'
                        'Produktivitas: %{customdata[2]:.2f} ton/ha'
                        '<extra></extra>'
                    ),
                ))

        frames.append(go.Frame(data=traces, name=str(t)))

    active_idx = len(tahun_list) - 1
    init_data  = frames[active_idx].data

    fig = go.Figure(data=init_data, frames=frames)

    fig.update_layout(
        margin={'r': 8, 't': 8, 'l': 8, 'b': 8},
        legend=dict(
            orientation='h',
            yanchor='bottom', y=1.02,
            xanchor='left', x=0,
            font=dict(size=11, color='#374151'),
            itemsizing='constant',
            bgcolor='rgba(0,0,0,0)',
            borderwidth=0,
        ),
        xaxis=dict(
            title=dict(text='Luas Area (ha)', font=dict(size=11, color='#9CA3AF')),
            range=[None, x_max],
            tickvals=x_tick_vals, ticktext=x_tick_text,
            tickfont=dict(size=10, color='#9CA3AF'),
            showgrid=True, gridcolor='#F3F4F6', gridwidth=1,
            zeroline=False,
        ),
        yaxis=dict(
            title=dict(text='Produksi (ton)', font=dict(size=11, color='#9CA3AF')),
            range=[None, y_max],
            tickvals=y_tick_vals, ticktext=y_tick_text,
            tickfont=dict(size=10, color='#9CA3AF'),
            showgrid=True, gridcolor='#F3F4F6', gridwidth=1,
            zeroline=False,
        ),
        hovermode='closest',
        hoverlabel=dict(bgcolor='white', bordercolor='#E5E7EB', font=dict(size=12, color='black')),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',

        updatemenus=[dict(
            type='buttons',
            showactive=False,
            x=0.0, y=-0.34, xanchor='left', yanchor='top',
            direction='left',
            bgcolor="#3b6d11",        
            font=dict(color='white', size=14),
            borderwidth=0,
            pad=dict(r=10, t=10, b=0, l=0),
            buttons=[
                dict(label='▶', method='animate',
                     args=[None, {'frame': {'duration': 700, 'redraw': False},
                                  'fromcurrent': True,
                                  'transition': {'duration': 500, 'easing': 'cubic-in-out'}}]),
                dict(label='⏸', method='animate',
                     args=[[None], {'frame': {'duration': 0, 'redraw': False},
                                    'mode': 'immediate',
                                    'transition': {'duration': 0}}]),
            ],
        )],

        sliders=[dict(
            active=active_idx,
            currentvalue=dict(prefix='Tahun: ', font=dict(size=12, color='#6B7280'), visible=True, xanchor='right'),
            pad=dict(t=15, b=0, l=20), len=0.82, x=0.18, y=-0.22,
            xanchor='left', yanchor='top',
            bgcolor='#F3F4F6',
            bordercolor='#E5E7EB',
            tickcolor='#E5E7EB',
            font=dict(size=10, color='#9CA3AF'),
            steps=[
                dict(args=[[str(t)], {'frame': {'duration': 700, 'redraw': False},
                                       'mode': 'immediate',
                                       'transition': {'duration': 500, 'easing': 'cubic-in-out'}}],
                     label=str(t), method='animate')
                for t in tahun_list
            ],
        )],
    )

    return fig