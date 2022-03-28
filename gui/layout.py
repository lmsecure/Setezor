from dash import html, dcc
import dash_cytoscape as cyto
import dash_bootstrap_components as dbc
import dash_loading_spinners as dls


def generate_layout(nodes: list, edges: list):
    '''Main application layouts'''
    return html.Div(
        children=[
            html.Div([create_graph(nodes, edges)],
                     style={'width': '80%'}),
            html.Div([
                html.Div([html.H3('Layout property'),
                          html.Div([dcc.Dropdown(['random', 'cose', 'grid', 'circle', 'concentric', 'breadthfirst', 'preset', 'radial'],
                                                 id='layouts1')],
                                   id='layout_props',
                                   style={'height': '200px'})],
                         style={'width': '100%'}),
                html.Div([dcc.Tabs(id='node_tabs', children=[
                                       dcc.Tab(label='Node', value='node', children=create_node_tab(True)),
                                       dcc.Tab(label='Edge', value='edge', children=create_node_tab(False))])
                          ]),
                html.Div([dcc.Tabs(id='scan_tabs', children=[
                    dcc.Tab(label='Active Scan', value='nmap', children=create_scan_tab('active')),
                    dcc.Tab(label='Passive Scan', value='scapy', children=create_scan_tab('passive'))
                ])])
            ],
                     style={'width': '19%'})
        ],
        style={'display': 'flex', 'flex-direction': 'row'})


def create_scan_tab(scan_type: str):
    if scan_type == 'passive':
        return html.Div([html.Button(i.upper(), disabled=True, id=f'passive_scan_{i}', style={'width': '50%', 'height': '40px'}) for i in ['start', 'stop']])
    elif scan_type == 'active':
        return html.Div(dls.Hash([html.Div([dcc.Input(id='input_nmap_target', placeholder='Target', type='text',
                                                      style={'width': '150%', 'height': '35px'}),
                                            dcc.Dropdown(['Quick', 'Quick traceroute', 'Version', 'Stealth scan', 'Scripts'], 'Quick', id='dd_scan_type',
                                                          style={'width': '100%', 'height': '35px'})
                                           ], style={'display': 'flex', 'flex-direction': 'row'}),
                                 dcc.Input(id='input_nmap_command', placeholder='NMAP command',
                                           type='text', style={'width': '100%', 'height': '30px', 'margin-top': '3px'}),
                                 html.Button('SCAN', id='active_scan_start', style={'width': '100%', 'height': '40px'})],
                                 color="#435278",
                                 speed_multiplier=2,
                                 size=50))
    else:
        return None


def create_node_tab(is_nodes):
    if is_nodes:
        inputs_labels = ['classes', 'group', 'id', 'label']
    else:
        inputs_labels = ['classes', 'group', 'id', 'source', 'target', 'label']
    tab_type = "node" if is_nodes else "edge"
    return html.Div([html.Div([dcc.Input(id=f'input_{tab_type}_{i}',
                               placeholder=i.upper(),
                               type='text',
                               style={'width': '100%', 'height': '30px'}) for i in inputs_labels]),
                     html.Div([html.Button(j.upper(),
                                           id=f'btn_{tab_type}_{j}',
                                           style={'width': '33.3%', 'height': '40px'}) for j in ['add', 'clear', 'delete']]),
                     html.Div(id=f'alert_{tab_type}')
                     ])


def create_alert(message, color='danger', is_open=True, duration=4000):
    return dbc.Alert(message, color=color, dismissable=True, duration=duration, is_open=is_open)


def create_graph(nodes: list, edges: list):
    '''Create network graph with nodes and edges'''
    cyto.load_extra_layouts()
    return cyto.Cytoscape(
        id='cytoscape',
        layout={'name': 'preset'},
        elements=[],
        style={'width': '100%', 'height': '1000px'},
    )
