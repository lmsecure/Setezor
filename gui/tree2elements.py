import math


class Geometry:
    def __init__(self):
        pass

    @staticmethod
    def get_coords_on_circle(radius, phi):
        phi_rad = phi * 2 * math.pi / 360
        x = radius * math.cos(phi_rad)
        y = radius * math.sin(phi_rad)
        return {'x': x, 'y': y}


class PositionManager:
    def __init__(self):
        pass

    def create_node(self, index, label, x, y):
        return {'classes': 'node',
                'data': {
                    'id': str(index),
                    'label': str(label)
                },
                'position': {'x': x, 'y': y}
                }

    def create_edge(self, source_id, target_id):
        return {'classes': 'edge',
                'data': {
                    'id': f'{source_id}_{target_id}',
                    'source': source_id,
                    'target': target_id
                }
                }

    def recur_creation(self, node, level, weight, ang, start_radius=300, phi_seek=0):
        r = []
        n = self.create_node(node.id, node.label,
                             **Geometry.get_coords_on_circle(level * start_radius, phi_seek + ang * weight))
        if node.children:
            edges = [self.create_edge(node.id, i.id) for i in node.children]
            ch_ch_count = len([j for i in node.children for j in i.children])
            ch_weights = [len(i.children) / ch_ch_count for i in node.children] if ch_ch_count else [1 / len(
                node.children)] * len(node.children)
            for index, i in enumerate(node.children):
                r += self.recur_creation(i, level + 1, ch_weights[index], ch_weights[index] * ang,
                                         phi_seek=ang * sum(ch_weights[:index]) + phi_seek)
            return [n] + edges + r
        return [n]

    def create_elements_with_positions(self, tree):
        result = self.recur_creation(tree.first, 0, 1, 360)
        return result
