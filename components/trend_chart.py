import plotly.graph_objects as go
import pandas as pd

def _fmt_y(val):
    if val >= 1_000_000:
        return f"{val/1_000_000:.0f}M"
    if val >= 1_000:
        return f"{val/1_000:.0f}K"
    return str(int(val))

def create_trend(df_prov, tahun_range, provinsi, kepemilikan):
    t_min, t_max = tahun_range

    df = df_prov[(df_prov['Tahun'] >= t_min) & (df_prov['Tahun'] <= t_max)]
    if provinsi != 'ALL':
        df = df[df['Provinsi'] == provinsi]

    prod_cols = [f'Produksi_{k}' for k in kepemilikan
                 if f'Produksi_{k}' in df.columns]
    if not prod_cols:
        prod_cols = ['Total_Produksi']

    df_trend = df.groupby('Tahun')[prod_cols].sum().reset_index()
    df_trend['Total'] = df_trend[prod_cols].sum(axis=1)

    color_map = {
        'Rakyat': '#639922',  
        'Swasta': '#D2601A',   
        'Negara': '#B8860B',   
    }

    fig = go.Figure()

    for k in kepemilikan:
        col = f'Produksi_{k}'
        if col not in df_trend.columns:
            continue

        warna = color_map.get(k, '#888')

        fig.add_trace(go.Scatter(
            x=df_trend['Tahun'],
            y=df_trend[col],
            name=k,
            mode='lines+markers',
            line=dict(
                width=3,
                color=warna,
                shape='spline',         
                smoothing=0.8,          
            ),
            marker=dict(
                size=7,
                color='white',          
                line=dict(width=2, color=warna),  
            ),
            # Area fill tipis di bawah line
            fill='tozeroy',
            fillcolor=warna.replace(')', ', 0.06)').replace('rgb', 'rgba')
                if warna.startswith('rgb')
                else _hex_to_rgba(warna, 0.06),
            hovertemplate=f'<b>{k}</b>: %{{y:,.0f}} ton<extra></extra>',
        ))

    fig.add_trace(go.Scatter(
        x=df_trend['Tahun'],
        y=df_trend['Total'],
        name='Total',
        mode='lines+markers',
        line=dict(
            width=2.5,
            color='#94A3B8',        
            shape='spline',
            smoothing=0.8,
            dash='dot',
        ),
        marker=dict(size=5, color='#94A3B8'),
        hovertemplate='<b>Total</b>: %{y:,.0f} ton<extra></extra>',
    ))

    
    max_y = df_trend['Total'].max()
    tick_step = _step(max_y, n_ticks=5)
    tick_vals = list(range(0, int(max_y * 1.1), tick_step))
    tick_text = [_fmt_y(v) for v in tick_vals]

    fig.update_layout(
        margin={'r': 8, 't': 8, 'l': 8, 'b': 8},
        legend=dict(
            orientation='h',
            yanchor='bottom', y=1.02,
            xanchor='left', x=0,
            font=dict(size=12, color='#374151'),
            bgcolor='rgba(0,0,0,0)',
            borderwidth=0,
        ),
        xaxis=dict(
            dtick=1,
            tickfont=dict(size=11, color='#9CA3AF'),
            showgrid=False,           
            zeroline=False,
        ),
        yaxis=dict(
            tickvals=tick_vals,
            ticktext=tick_text,
            tickfont=dict(size=11, color='#9CA3AF'),
            showgrid=True,
            gridcolor='#F3F4F6',       
            gridwidth=1,
            zeroline=False,
            title=None,               
        ),
        hovermode='x unified',
        hoverlabel=dict(
            bgcolor='white',
            bordercolor='#CBD5E1',
            font=dict(size=12, color='#1A2410'),
        ),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
    )

    return fig


def _hex_to_rgba(hex_color, alpha):
    hex_color = hex_color.lstrip('#')
    r, g, b = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
    return f'rgba({r},{g},{b},{alpha})'


def _step(max_val, n_ticks=5):
    import math
    if max_val <= 0:
        return 1
    raw_step = max_val / n_ticks
    magnitude = 10 ** math.floor(math.log10(raw_step))
    candidates = [magnitude * m for m in [1, 2, 2.5, 5, 10]]
    return int(min(candidates, key=lambda s: abs(s - raw_step)))