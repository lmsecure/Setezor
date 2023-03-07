from sqlalchemy.orm import class_mapper
from sqlalchemy_schemadisplay import create_uml_graph
import sys, os
sys.path.append(os.path.abspath('../'))
from database import models

if __name__ == '__main__':
    mappers = []
    for attr in dir(models):
        if attr[0] == '_': continue
        try:
            cls = getattr(models, attr)
            mappers.append(class_mapper(cls))
        except:
            pass
        
    graph = create_uml_graph(mappers,
        show_operations=False,
        show_multiplicity_one=False
    )
    graph.write_png(sys.argv[1])