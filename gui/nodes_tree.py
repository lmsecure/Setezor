from database.db_connection import DBConnection
from database.queries import get_all_l3_links
import pandas as pd


class Node:
    __slots__ = ['id', 'parent', 'label', 'children']

    def __init__(self, index, parent, label=None, children=None):
        self.id = index
        self.parent = parent
        self.label = f'{index} node' if not label else label
        self.children = children if children else list()


class Tree:
    def __init__(self):
        self.first = []

    def create_tree(self, start_ip: str):

        def recursive_tree_creation(ip: str, df: pd.DataFrame, parent: Node):
            try:
                children_ip = df[df.parent_ip == ip].child_ip.tolist()
                node = Node(ip, parent, ip)
                children_node = [recursive_tree_creation(i, df, node) for i in children_ip]
                node.children = children_node if children_node else []
                return node
            except Exception as e:
                print(df)
                raise e

        links = get_all_l3_links(DBConnection().create_session())
        links_df = pd.DataFrame([{'parent_ip': i.parent_ip.ip, 'child_ip': i.child_ip.ip} for i in links])
        self.first = recursive_tree_creation(start_ip, links_df, None)
