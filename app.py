from gui.layout import generate_layout, create_alert
import dash_bootstrap_components as dbc
from dash_extensions.enrich import Output, DashProxy, Input, State, MultiplexerTransform
from core import Core
from config import CoreConfig
from gui.tree2elements import PositionManager
from gui.nodes_tree import Tree
import traceback
from scan.active_scan.nmap_scanning import NmapScanner


app = DashProxy(external_stylesheets=[dbc.themes.BOOTSTRAP],
                prevent_initial_callbacks=True,
                transforms=[MultiplexerTransform()])
app.layout = generate_layout([], [])

core = Core(CoreConfig.iface)


@app.callback(Output('cytoscape', 'elements'),
              Output('alert_node', 'children'),
              Input('btn_node_add', 'n_clicks'),
              State('cytoscape', 'elements'),
              *[State(f'input_node_{i}', 'value') for i in ['classes', 'group', 'id', 'label']])
def create_node(n_clicks, elements, node_class, node_group, node_id, node_label):
    if not n_clicks:
        return elements, None
    auto_id = [int(i.get('data').get('id')[:-2]) for i in elements if all(j.isdigit() for j in [i.get('data').get('id')[:-2]]) ]
    node = {'classes': node_class if node_class else 'node',
            'group': node_group if node_group else 'nodes',
            'data': {'id': node_id if node_id else str(max(auto_id) + 1 if auto_id else 1) + 'id',
                     'label': node_label if node_label else str(max(auto_id) + 1 if auto_id else 1) + ' node'}}
    if node.get('data').get('id') in [i.get('data').get('id') for i in elements]:
        return elements, create_alert(f'Node ID "{node.get("data").get("id")}" is already using')
    return elements + [node], None


@app.callback(*[Output(f'input_node_{i}', 'value') for i in ['classes', 'group', 'id', 'label']],
              Input('btn_node_clear', 'n_clicks'),
              *[State(f'input_node_{i}', 'value') for i in ['classes', 'group', 'id', 'label']])
def clear_node_inputs(n_clicks, node_class, node_group, node_id, node_label):
    if not n_clicks:
        return node_class, node_group, node_id, node_label
    else:
        return '', '', '', ''


@app.callback(Output('cytoscape', 'elements'),
              Output('alert_node', 'children'),
              Input('btn_node_delete', 'n_clicks'),
              State('cytoscape', 'elements'),
              State('input_node_id', 'value'))
def delete_node(n_clicks, elements, node_id):
    if not n_clicks:
        return elements, None
    else:
        if not node_id:
            return elements, create_alert('Wrong ID', color='warning')
        index = []
        for ind, i in enumerate(elements):
            if node_id in [i.get('data').get('id'), i.get('data').get('target'), i.get('data').get('source')]:
                index.append(ind)
        if not index:
            return elements, create_alert(f'Not find nodes with ID "{node_id}"', color='info')
        for i in sorted(index, reverse=True):
            elements.pop(i)
        return elements, create_alert(f'Node and edges with ID "{node_id}" deleted', color='success')


@app.callback(Output('cytoscape', 'elements'),
              Output('alert_edge', 'children'),
              Input('btn_edge_add', 'n_clicks'),
              State('cytoscape', 'elements'),
              *[State(f'input_edge_{i}', 'value') for i in ['classes', 'group', 'id', 'source', 'target', 'label']])
def create_edge(n_clicks, elements, edge_class, edge_group, edge_id, edge_source, edge_target, edge_label):
    if not n_clicks:
        return elements
    if not edge_source and not edge_target:
        return elements, create_alert('You did not specify source and target')
    edge_id = edge_id if edge_id else f'{edge_source}_{edge_target}'
    ids = [i for i in elements if edge_id == i.get('data').get('id')]
    if ids:
        return elements, create_alert(f'Edge with ID "{edge_id}" already using')
    edge = {'classes': edge_class if edge_class else 'edge',
            'group': edge_group if edge_group else 'edges',
            'data': {
                'id': f'{edge_id}',
                'source': edge_source,
                'target': edge_target,
                'label': edge_label if edge_label else ''
            }}
    elements.append(edge)
    return elements, create_alert(f'Edge from "{edge_source}" to "{edge_target}" with ID "{edge_id}{len(ids) + 1}" created', color='info')


@app.callback(Output('cytoscape', 'elements'),
              Output('alert_edge', 'children'),
              Input('btn_edge_delete', 'n_clicks'),
              State('cytoscape', 'elements'),
              *[State(f'input_edge_{i}', 'value') for i in ['id', 'source', 'target']])
def delete_edge(n_clicks: int, elements: list, edge_id: str, edge_source: str, edge_target: str):
    if not n_clicks:
        return elements, None
    if not any([bool(i) for i in [edge_id, edge_source, edge_target]]):
        return elements, create_alert('You not write any data to delete edge')
    edges_ids = [i.get('data').get('id') for i in elements]
    edges_sources = [i.get('data').get('source') for i in elements]
    edges_targets = [i.get('data').get('target') for i in elements]
    indexes = []
    if edge_id:
        indexes = [ind for ind, i in enumerate(edges_ids) if edge_id == i]
    elif edge_source:
        indexes = [ind for ind, i in enumerate(edges_sources) if edge_source == i]
    elif edge_target:
        indexes = [ind for ind, i in enumerate(edges_targets) if edge_target == i]
    if not indexes:
        return elements, create_alert(f'Not find edges to delete', color='warning')
    else:
        for i in sorted(indexes, reverse=True):
            elements.pop(i)
        return elements, create_alert('Edges deleted', color='info')


@app.callback(*[Output(f'input_edge_{i}', 'value') for i in ['classes', 'group', 'id', 'source', 'target', 'label']],
              Input('btn_edge_clear', 'n_clicks'),
              *[State(f'input_edge_{i}', 'value') for i in ['classes', 'group', 'id', 'source', 'target', 'label']])
def clear_edge_inputs(n_clicks, edge_class, edge_group, edge_id, edge_source, edge_target, edge_label):
    if not n_clicks:
        return edge_class, edge_group, edge_id, edge_source, edge_target, edge_label
    else:
        return '', '', '', '', '', '',


@app.callback(*[Output(f'input_edge_{i}', 'value') for i in ['id', 'source', 'target']],
              *[Output(f'input_node_{i}', 'value') for i in ['id', 'label']],
              Input('cytoscape', 'selectedNodeData'))
def selected_node(selected):
    if len(selected) == 1:
        return '', '', '', selected[0].get('id'), selected[0].get('label')
    elif len(selected) == 2:
        source = selected[0].get('id')
        target = selected[1].get('id')
        return f'{source}_{target}', source, target, '', ''
    return '', '', '', '', ''


@app.callback(*[Output(f'input_edge_{i}', 'value') for i in ['id', 'source', 'target', 'label']],
              Input('cytoscape', 'selectedEdgeData'))
def selected_edge(selected):
    if len(selected) == 1:
        id = selected[0].get('id')
        label = selected[0].get('label')
        source = selected[0].get('source')
        target = selected[0].get('target')
        return id, source, target, label
    return '', '', '', ''


# @app.callback(*[Output(f'input_node_{i}', 'value') for i in ['classes', 'group', 'id', 'label']],
#               Input('cytoscape', 'tapNode'))
# def tap_node(tap):
#     tap.pop('style')
#     tap_data = tap.get('data')
#     return tap.get('classes'), tap.get('group'), tap_data.get('id'), tap_data.get('label')


@app.callback(Output('cytoscape', 'layout'),
              Input('layouts1', 'value'))
def set_layout(layout):
    if layout:
        return {'name': layout}
    else:
        if name == 'radial':
            return {}
        return {'name': 'breadthfirst'}

@app.callback(Output('input_nmap_command', 'value'),
              Input('input_nmap_target', 'value'),
              Input('dd_scan_type', 'value'))
def make_nmap_command(targets, scan_type):
    start_command = NmapScanner.start_command
    extra_args = NmapScanner.scan_type.get(scan_type.lower().replace(' ', '_')) if scan_type else None
    extra_args = extra_args if extra_args else ['']
    return ' '.join(start_command + extra_args + [targets if targets else ''])


@app.callback(Output('cytoscape', 'elements'),
              Input('active_scan_start', 'n_clicks'),
              State('input_nmap_command', 'value'))
def active_scan(n_clicks, value):
    try:
        if not n_clicks:
            return []
        value = value.replace(' '.join(NmapScanner.start_command), '').strip()
        core.active_scan(value)
        tree = Tree()
        tree.create_tree(core.get_self_ip(CoreConfig.iface).get('ip'))
        elements = PositionManager().create_elements_with_positions(tree)
        return elements
    except:
        print(traceback.format_exc())
        return []


@app.callback(Output('passive_scan_start', 'value'),
              Input('passive_scan_start', 'n_clicks'))
def start_passive_scan(n_clicks):
    if not n_clicks:
        return 'START'
    print('start sniffers')
    return 'START'


@app.callback(Output('cytoscape', 'elements'),
              Input('passive_scan_stop', 'n_clicks'))
def start_passive_scan(n_clicks):
    if not n_clicks:
        return []
    print('stop sniffers')
    return []


if __name__ == '__main__':
    app.run_server(debug=True)
