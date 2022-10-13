from sqlalchemy import MetaData
from sqlalchemy_schemadisplay import create_schema_graph
import sys

if __name__ == '__main__':
    graph = create_schema_graph(metadata=MetaData(f"sqlite:///database.sqlite"),
    show_datatypes=False,
    show_indexes=False, 
    rankdir='LR',
    concentrate=False
    )
    graph.write_png(sys.argv[1])