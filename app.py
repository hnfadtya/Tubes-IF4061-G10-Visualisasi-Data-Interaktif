import dash
from dash import dcc, html
import pandas as pd
import json
from geojson_rewind import rewind
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / 'data'

df_prov = pd.read_csv(DATA_DIR / 'palm_oil_area_and_production_by_province.csv')
df_ekspor = pd.read_csv(DATA_DIR / 'ekspor_impor_palm_oil_2010_2023.csv')

with open(DATA_DIR / 'indonesia.json', 'r') as f:
    geojson = json.load(f)
    
geojson = rewind(geojson)

tahun_min = int(df_prov['Tahun'].min())   
tahun_max = int(df_prov['Tahun'].max()) 
list_provinsi = sorted(df_prov['Provinsi'].unique())

app = dash.Dash(
    __name__,
    external_stylesheets=[
        "https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap"
    ]
)
app.title = "Dashboard Kelapa Sawit Indonesia"

app.layout = html.Div([
    dcc.Store(
        id='kepemilikan-store',
        data=['Rakyat', 'Swasta', 'Negara']
    ),
    html.Div([
        html.Div([
            html.H1("SawitHub",
                    style={
                        'margin': '0',
                        'fontSize': '30px',
                        'fontWeight': '800',
                        'color': '#1F3D1A',
                        'letterSpacing': '-0.8px'
                    }),
            html.P("Menyediakan Informasi Industri Kelapa Sawit Indonesia",
                    style={
                        'margin': '6px 0 0',
                        'fontSize': '14px',
                        'fontWeight': '400',
                        'color': '#6B7280'
                    }),
        ], style={
            'marginBottom': '24px'
        }),

        html.Div([
            html.Div([
                html.Label(
                    "RENTANG TAHUN",
                    style={
                        'fontSize': '10px',
                        'fontWeight': '700',
                        'color': '#4B5563',
                        'letterSpacing': '0.5px',
                        'marginBottom': '16px',
                        'display': 'block'
                    }
                ),

                html.Div([
                    html.Span(
                        str(tahun_min),
                        id  = 'tahun-min-label',
                        style={
                            'fontSize': '13px',
                            'fontWeight': '600',
                            'color': '#6B7280',
                            'minWidth': '36px',
                            'textAlign': 'center',
                            'position': 'relative',
                            'top': '-12px'
                        }
                    ),
                    # Slider
                    html.Div([
                        dcc.RangeSlider(
                            id='filter-tahun',
                            min=tahun_min,
                            max=tahun_max,
                            value=[tahun_min, tahun_max],
                            step=1,
                            className='tahun-slider',
                            marks={
                                y: {
                                    'label': str(y),
                                    'style': {
                                        'fontSize': '10px',
                                        'color': '#9CA3AF'
                                    }
                                }
                                for y in range(tahun_min, tahun_max + 1, 2)
                            },
                            tooltip={
                                'placement': 'bottom',
                                'always_visible': False
                            }
                        )
                    ], style={
                        'flex': '1',
                        'padding': '0 12px'
                    }),

                    html.Span(
                        str(tahun_max),
                        id  = 'tahun-max-label',
                        style={
                            'fontSize': '13px',
                            'fontWeight': '600',
                            'color': '#6B7280',
                            'minWidth': '36px',
                            'textAlign': 'center',
                            'position': 'relative',
                            'top': '-12px'
                        }
                    ),

                ], style={
                    'display': 'flex',
                    'alignItems': 'center'
                })

            ], style={
                'flex': '2.6',
                'paddingRight': '24px'
            }),

            # garis vertikal
            html.Div(style={
                'width': '1px',
                'backgroundColor': '#E5E7EB'
            }),

            # provinsi
            html.Div([
                html.Label(
                    "PROVINSI",
                    style={
                        'fontSize': '10px',
                        'fontWeight': '700',
                        'color': '#4B5563',
                        'letterSpacing': '0.5px',
                        'marginBottom': '10px',
                        'display': 'block'
                    }
                ),

                dcc.Dropdown(
                    id='filter-provinsi',
                    options=[
                        {'label': 'Semua Provinsi', 'value': 'ALL'}
                    ] + [
                        {'label': p, 'value': p}
                        for p in list_provinsi
                    ],
                    value='ALL',
                    clearable=False,
                    className='dropdown-provinsi',
                    style={
                        'fontSize': '13px',
                        'color': '#374151'
                    }
                ),
            ], style={
                'flex': '1',
                'padding': '0 24px'
            }),

            # garis vertikal
            html.Div(style={
                'width': '1px',
                'backgroundColor': '#E5E7EB'
            }),

            # kepemilikan
            html.Div([
                html.Label(
                    "JENIS KEPEMILIKAN",
                    style={
                        'fontSize': '10px',
                        'fontWeight': '700',
                        'color': '#4B5563',
                        'letterSpacing': '0.5px',
                        'marginBottom': '10px',
                        'display': 'block'
                    }
                ),

                dcc.Checklist(
                    id='filter-kepemilikan',
                    options=[
                        {'label': 'Swasta', 'value': 'Swasta'},
                        {'label': 'Rakyat', 'value': 'Rakyat'},
                        {'label': 'Negara', 'value': 'Negara'},
                    ],
                    value=['Rakyat', 'Swasta', 'Negara'],
                    inline=True,
                    className='tag-checklist'
                ),
            ], style={
                'flex': '1.4',
                'paddingLeft': '24px'
            }),

        ], style={
            'display': 'flex',
            'alignItems': 'stretch',
            'backgroundColor': '#ffffff',
            'border': '1px solid #E5E7EB',
            'borderRadius': '12px',
            'padding': '20px 24px',
            'marginBottom': '28px',
            'boxShadow': '0 1px 3px 0 rgba(0, 0, 0, 0.02)'
        }),

        html.Div(
            id='kpi-cards',
            style={
                'display': 'grid',
                'gridTemplateColumns': 'repeat(5, minmax(220px, 1fr))',
                'gap': '20px',
                'marginBottom': '28px'
            }
        ),

        html.Div([
            html.Div([
                html.Div([
                    html.P(
                        "Distribusi Produksi per Provinsi",
                        style={'fontSize': '20px', 'fontWeight': '600', 'color': '#111827', 'margin': '0'}
                    ),
                    html.Div([
                        html.Label(
                            "Snapshot tahun",
                            style={'fontSize': '10px', 'fontWeight': '700', 'color': '#9CA3AF',
                                    'letterSpacing': '0.5px', 'marginRight': '8px', 'whiteSpace': 'nowrap'}
                        ),
                        dcc.Dropdown(
                            id='filter-tahun-map',
                            options=[{'label': str(y), 'value': y} for y in range(tahun_min, tahun_max+1)],
                            value=tahun_max,
                            clearable=False,
                            style={'fontSize': '13px', 'width': '90px'},
                        ),
                    ], style={'display': 'flex', 'alignItems': 'center'}),
                ], style={'display': 'flex', 'alignItems': 'center', 'justifyContent': 'space-between', 'marginBottom': '16px'}),
                
                dcc.Graph(
                    id='map-chart',
                    config={'scrollZoom': True, 'displayModeBar': True},
                    style={'height': '420px'}
                ),
            ], style={
                'flex': '7', 
                'backgroundColor': '#ffffff',
                'border': '1px solid #E5E7EB', 
                'borderRadius': '12px', 
                'padding': '20px',
                'boxShadow': '0 1px 3px 0 rgba(0, 0, 0, 0.02)'
            }),

            html.Div([
                html.P(
                    "Komposisi Kepemilikan",
                    style={
                        'fontSize': '20px', 
                        'fontWeight': '600', 
                        'color': '#111827', 
                        'margin': '0 0 16px'
                    }
                ),
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
                html.P(
                    "Tren Produksi",
                    style={
                        'fontSize': '20px', 
                        'fontWeight': '600', 
                        'color': '#111827', 
                        'margin': '0 0 16px'
                    }
                ),
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
                html.P(
                    "Efisiensi Provinsi",
                    style={
                        'fontSize': '20px', 
                        'fontWeight': '600', 
                        'color': '#111827', 
                        'margin': '0 0 16px'
                    }
                ),
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

        html.Div([
            html.Div([
                html.Div([
                    html.P(
                        "Aliran Sawit: Dari Kebun ke Devisa",
                        style={'fontSize': '20px', 'fontWeight': '600', 'color': '#111827', 'margin': '0'}
                    ),
                    html.Div([
                        html.Label(
                            "Snapshot tahun",
                            style={'fontSize': '10px', 'fontWeight': '700', 'color': '#9CA3AF',
                                    'letterSpacing': '0.5px', 'marginRight': '8px', 'whiteSpace': 'nowrap'}
                        ),
                        dcc.Dropdown(
                            id='filter-tahun-sankey',
                            options=[{'label': str(y), 'value': y} for y in range(tahun_min, tahun_max+1)],
                            value=tahun_max,
                            clearable=False,
                            style={'fontSize': '13px', 'width': '90px'},
                        ),
                    ], style={'display': 'flex', 'alignItems': 'center'}
                    ),
                ], style={'display': 'flex', 'alignItems': 'center', 'justifyContent': 'space-between', 'marginBottom': '8px'}
                ),

                html.P(
                    "Kepemilikan → provinsi utama → produksi nasional → terbelah menjadi ekspor "
                    "(ke negara tujuan) dan konsumsi domestik.",
                    style={'fontSize': '12px', 'color': '#6B7280', 'margin': '0 0 8px'}
                ),
                html.Div(id='sankey-note'),
                dcc.Graph(
                    id='sankey-chart',
                    config={'displayModeBar': True},
                    style={'height': '520px'}
                ),
            ], style={
                'flex': '1',
                'backgroundColor': '#ffffff',
                'border': '1px solid #E5E7EB',
                'borderRadius': '12px',
                'padding': '20px',
                'boxShadow': '0 1px 3px 0 rgba(0, 0, 0, 0.02)'
            }),
        ], style={'display': 'flex', 'gap': '20px', 'marginTop': '20px'}),

        html.Div(
            "Sumber data: BPS & Direktorat Jenderal Perkebunan (Ditjenbun) · Data 2010–2023",
            style={
                'textAlign': 'center',
                'fontSize': '12px',
                'color': '#9CA3AF',
                'marginTop': '32px',
                'paddingTop': '20px',
                'borderTop': '1px solid #E5E7EB'
            }
        ),

    ], style={
        'padding': '28px 32px',
        'overflowY': 'auto',
        'height': '100vh',
        'boxSizing': 'border-box'
    }),

], style={
    'fontFamily': '"Plus Jakarta Sans", -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif', 
    'backgroundColor': '#F9FAFB', 
    'height': '100vh',
    'overflow': 'hidden',
    'display': 'flex',
    'flexDirection': 'column'
})

from callbacks.filter_callbacks import register_callbacks
register_callbacks(app, df_prov, df_ekspor, geojson)

server = app.server

if __name__ == '__main__':
    app.run(debug=True)