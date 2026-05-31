import plotly.graph_objects as go
import pandas as pd

def create_donut(df_prov, tahun_range, provinsi, kepemilikan):
    t_min, t_max = tahun_range
    df = df_prov[(df_prov['Tahun'] >= t_min) & (df_prov['Tahun'] <= t_max)]

    if provinsi and provinsi != 'ALL':
        df = df[df['Provinsi'] == provinsi]

    values, labels, colors = [], [], []
    
    color_map = {
        'Rakyat': '#639922',   
        'Swasta': '#D2601A',   
        'Negara': '#B8860B',   
    }

    for k in ['Rakyat', 'Swasta', 'Negara']:
        if k in kepemilikan:
            col = f'Produksi_{k}'
            if col in df.columns:
                values.append(df[col].sum())
                labels.append(k)
                colors.append(color_map[k])

    fig = go.Figure(go.Pie(
        labels=labels,
        values=values,
        hole=0.75,              
        marker=dict(colors=colors),
        textinfo='none',        
        hovertemplate='%{label}<br>%{value:,.0f} ton<br>%{percent}<extra></extra>',
    ))

    fig.update_layout(
        margin={'r':10,'t':10,'l':10,'b':10},
        showlegend=True,
        legend=dict(
            orientation="h",        
            yanchor="bottom",
            y=-0.2,                 
            xanchor="center",
            x=0.5,                  
            font=dict(size=12)
        ),
        hoverlabel=dict(bgcolor='#1F3D1A', bordercolor='rgba(255,255,255,0.15)', font=dict(size=12, color='#F5EFE0')),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
    )

    return fig