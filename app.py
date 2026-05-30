import dash
from dash import dcc, html
import pandas as pd
import json
from geojson_rewind import rewind

df_prov = pd.read_csv('data/palm_oil_area_and_production_by_province.csv')
df_ekspor = pd.read_csv('data/ekspor_impor_palm_oil_2010_2023.csv')

with open('data/indonesia.json', 'r') as f:
    geojson = json.load(f)

geojson = rewind(geojson)

tahun_min = int(df_prov['Tahun'].min())   
tahun_max = int(df_prov['Tahun'].max()) 
list_provinsi = sorted(df_prov['Provinsi'].unique())

app = dash.Dash(__name__)
app.title = "Dashboard Kelapa Sawit Indonesia"

app.layout = html.Div([

    html.Div([
        html.Div([
            html.H1("Dashboard Industri Kelapa Sawit Indonesia",
                    style={
                        'margin': '0', 
                        'fontSize': '20px', 
                        'fontWeight': '700', 
                        'color': '#111827',      
                        'letterSpacing': '-0.5px' 
                    }),
            html.P("Data 2010–2023 · Sumber: BPS & Ditjenbun",
                   style={
                       'margin': '6px 0 0', 
                       'fontSize': '12px', 
                       'fontWeight': '400',
                       'color': '#6B7280'      
                   }),
        ]),

        html.Div([
            html.Div([
                html.Label("RENTANG TAHUN",
                           style={
                               'fontSize': '10px', 
                               'fontWeight': '700', 
                               'color': '#4B5563',
                               'letterSpacing': '0.5px', 
                               'marginBottom': '6px', 
                               'display': 'block'
                           }),
                dcc.RangeSlider(
                    id='filter-tahun',
                    min=tahun_min, max=tahun_max,
                    value=[tahun_min, tahun_max],
                    step=1,
                    marks={y: {'label': str(y), 'style': {'fontSize': '10px', 'color': '#9CA3AF'}} for y in range(tahun_min, tahun_max+1, 2)},
                    tooltip={'placement': 'bottom', 'always_visible': False},
                ),
            ], style={'width': '260px'}),

            html.Div([
                html.Label("PROVINSI",
                           style={
                               'fontSize': '10px', 
                               'fontWeight': '700', 
                               'color': '#4B5563', 
                               'letterSpacing': '0.5px', 
                               'marginBottom': '6px', 
                               'display': 'block'
                           }),
                dcc.Dropdown(
                    id='filter-provinsi',
                    options=[{'label': 'Semua Provinsi', 'value': 'ALL'}] +
                            [{'label': p, 'value': p} for p in list_provinsi],
                    value='ALL',
                    clearable=False,
                    style={
                        'fontSize': '13px', 
                        'minWidth': '180px', 
                        'borderRadius': '6px',
                        'color': '#374151'
                    },
                ),
            ]),

            html.Div([
                html.Label("JENIS KEPEMILIKAN",
                           style={
                               'fontSize': '10px', 
                               'fontWeight': '700', 
                               'color': '#4B5563', 
                               'letterSpacing': '0.5px', 
                               'marginBottom': '6px', 
                               'display': 'block'
                           }),
                dcc.Checklist(
                    id='filter-kepemilikan',
                    options=[
                        {'label': ' Swasta',  'value': 'Swasta'},
                        {'label': ' Rakyat',  'value': 'Rakyat'},
                        {'label': ' Negara',  'value': 'Negara'},
                    ],
                    value=['Rakyat', 'Swasta', 'Negara'],
                    labelStyle={
                        'display': 'inline-flex', 
                        'alignItems': 'center',
                        'fontSize': '13px', 
                        'fontWeight': '500',
                        'color': '#374151',
                        'marginRight': '14px', 
                        'cursor': 'pointer'
                    },
                    inline=True,
                ),
            ]),
        ], style={
            'display': 'flex',
            'alignItems': 'center',
            'gap': '28px',
            'flexWrap': 'wrap',
        }),

    ], style={
        'display': 'flex',
        'alignItems': 'center',
        'justifyContent': 'space-between',
        'padding': '18px 32px',
        'backgroundColor': '#ffffff',
        'borderBottom': '1px solid #E5E7EB',
        'boxShadow': '0 1px 3px 0 rgba(0, 0, 0, 0.05)', 
        'flexWrap': 'wrap',
        'gap': '16px',
        'boxSizing': 'border-box',
        'width': '100%'
    }),

    html.Div([

        html.Div(id='kpi-cards', style={
            'display': 'grid',
            'gridTemplateColumns': 'repeat(5, 1fr)',
            'gap': '16px',
            'marginBottom': '24px',
        }),

        html.Div([
            
            html.Div([
                html.Div([
                    html.P("Distribusi Produksi per Provinsi",
                           style={'fontSize': '20px', 'fontWeight': '600', 'color': '#111827', 'margin': '0'}),
                    html.Div([
                        html.Label("Snapshot tahun",
                                   style={'fontSize': '10px', 'fontWeight': '700', 'color': '#9CA3AF',
                                          'letterSpacing': '0.5px', 'marginRight': '8px', 'whiteSpace': 'nowrap'}),
                        dcc.Dropdown(
                            id='filter-tahun-map',
                            options=[{'label': str(y), 'value': y} for y in range(tahun_min, tahun_max+1)],
                            value=tahun_max,
                            clearable=False,
                            style={'fontSize': '13px', 'width': '90px'},
                        ),
                    ], style={'display': 'flex', 'alignItems': 'center'}),
                ], style={'display': 'flex', 'alignItems': 'center', 'justifyContent': 'space-between', 'marginBottom': '16px'}),
                
                dcc.Graph(id='map-chart', style={'height': '420px'}),
            ], style={
                'flex': '7', 
                'backgroundColor': '#ffffff',
                'border': '1px solid #E5E7EB', 
                'borderRadius': '12px', 
                'padding': '20px',
                'boxShadow': '0 1px 3px 0 rgba(0, 0, 0, 0.02)'
            }),

            html.Div([
                html.P("Komposisi Kepemilikan",
                       style={
                           'fontSize': '20px', 
                           'fontWeight': '600', 
                           'color': '#111827', 
                           'margin': '0 0 16px'
                       }),
                dcc.Graph(id='donut-chart', style={'height': '420px'}),
            ], style={
                'flex': '3', 
                'backgroundColor': '#ffffff',
                'border': '1px solid #E5E7EB', 
                'borderRadius': '12px', 
                'padding': '20px',
                'boxShadow': '0 1px 3px 0 rgba(0, 0, 0, 0.02)'
            }),
            
        ], style={'display': 'flex', 'gap': '20px', 'marginBottom': '20px'}),

        html.Div([
            html.Div([
                html.P("Tren Produksi",
                       style={
                           'fontSize': '20px', 
                           'fontWeight': '600', 
                           'color': '#111827', 
                           'margin': '0 0 16px'
                       }),
                dcc.Graph(id='trend-chart', style={'height': '360px'}),
            ], style={
                'flex': '6', 
                'backgroundColor': '#ffffff',
                'border': '1px solid #E5E7EB', 
                'borderRadius': '12px', 
                'padding': '20px',
                'boxShadow': '0 1px 3px 0 rgba(0, 0, 0, 0.02)'
            }),

            html.Div([
                html.P("Efisiensi Provinsi",
                       style={
                           'fontSize': '20px', 
                           'fontWeight': '600', 
                           'color': '#111827', 
                           'margin': '0 0 16px'
                       }),
                dcc.Graph(id='bubble-chart', style={'height': '360px'}),
            ], style={
                'flex': '4', 
                'backgroundColor': '#ffffff',
                'border': '1px solid #E5E7EB', 
                'borderRadius': '12px', 
                'padding': '20px',
                'boxShadow': '0 1px 3px 0 rgba(0, 0, 0, 0.02)'
            }),
        ], style={'display': 'flex', 'gap': '20px'}),

    ], style={
        'padding': '24px 32px', 
        'overflowY': 'auto',
        'flex': '1',
        'boxSizing': 'border-box'
    }),

], style={
    'fontFamily': '"Inter", -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif', 
    'backgroundColor': '#F9FAFB', 
    'height': '100vh',
    'overflow': 'hidden',
    'display': 'flex',
    'flexDirection': 'column'
})

if __name__ == '__main__':
    from callbacks.filter_callbacks import register_callbacks
    register_callbacks(app, df_prov, df_ekspor, geojson)
    app.run(debug=True)