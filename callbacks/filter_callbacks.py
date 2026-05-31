import dash
from dash import Input, Output, callback
from components.kpi_cards   import create_kpi_cards
from components.map_chart   import create_map
from components.trend_chart import create_trend
from components.donut_chart import create_donut
from components.bubble_chart import create_bubble

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