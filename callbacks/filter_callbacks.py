import dash
from dash import Input, Output, State, callback, html
from components.kpi_cards   import create_kpi_cards
from components.map_chart   import create_map
from components.trend_chart import create_trend
from components.donut_chart import create_donut
from components.bubble_chart import create_bubble
from components.sankey_chart import create_sankey, DEST_YEAR_MIN

def register_callbacks(app, df_prov, df_ekspor, geojson):

    @callback(
        Output('map-chart',   'figure'),
        Output('donut-chart', 'figure'),
        Input('filter-tahun-map',   'value'),
        Input('filter-provinsi',    'value'),
        Input('filter-kepemilikan', 'value'),
    )
    def update_snapshot(tahun_map, provinsi, kepemilikan):
        snap = [tahun_map, tahun_map]
        return create_map(df_prov, geojson, snap, kepemilikan), \
               create_donut(df_prov, snap, provinsi, kepemilikan)

    @callback(
        Output('trend-chart',  'figure'),
        Output('bubble-chart', 'figure'),
        Input('filter-tahun',       'value'),
        Input('filter-provinsi',    'value'),
        Input('filter-kepemilikan', 'value'),
    )
    def update_trend(tahun_range, provinsi, kepemilikan):
        return create_trend(df_prov, tahun_range, provinsi, kepemilikan), \
               create_bubble(df_prov, provinsi, kepemilikan)

    @callback(
        Output('kpi-cards', 'children'),
        Input('filter-tahun',       'value'),
        Input('filter-provinsi',    'value'), 
        Input('filter-kepemilikan', 'value'),
    )
    def update_kpi(tahun_range, provinsi, kepemilikan):
        return create_kpi_cards(df_prov, df_ekspor, tahun_range, provinsi, kepemilikan)

    @callback(
        Output('sankey-chart', 'figure'),
        Output('sankey-note', 'children'),
        Input('filter-tahun-sankey', 'value'),
        Input('filter-kepemilikan', 'value'),
    )
    def update_sankey(tahun_sankey, kepemilikan):
        fig, no_dest = create_sankey(df_prov, df_ekspor, tahun_sankey, kepemilikan)
        note = None
        if no_dest:
            note = html.Div(
                f"Rincian negara tujuan ekspor belum tersedia untuk {tahun_sankey} "
                f"(data BPS dimulai {DEST_YEAR_MIN}); aliran berhenti di node Ekspor.",
                style={'fontSize': '11px', 'color': '#92400E',
                       'backgroundColor': '#FEF3C7', 'padding': '6px 10px',
                       'borderRadius': '6px', 'margin': '0 0 8px'}
            )
        return fig, note

    @callback(
        Output('filter-provinsi', 'value'),
        Input('map-chart', 'clickData'),
        prevent_initial_call=True,
    )
    def update_provinsi_from_map(clickData):
        if not clickData:
            return dash.no_update
        try:
            p = clickData['points'][0]
            nama = p.get('location') or p.get('text') or p.get('hovertext')
            if isinstance(nama, str):
                nama = nama.strip()
                for prov in df_prov['Provinsi'].astype(str).unique():
                    if prov.lower() == nama.lower():
                        return prov
                return nama
        except (KeyError, IndexError, TypeError):
            pass
        return dash.no_update
    
    @callback(
        Output('tahun-min-label', 'children'),
        Output('tahun-max-label', 'children'),
        Input('filter-tahun', 'value')
    )
    def update_tahun_labels(tahun_range):
        return str(tahun_range[0]), str(tahun_range[1])
    
    @callback(
        Output('filter-kepemilikan', 'value'),
        Output('kepemilikan-store', 'data'),
        Input('filter-kepemilikan', 'value'),
        State('kepemilikan-store', 'data')
    )
    def enforce_minimum_kepemilikan(current_value, last_valid):
        # User menghapus semua pilihan
        if not current_value:
            return last_valid, last_valid

        return current_value, current_value