import { DataSet, Network } from 'visjs-network';

class GraphNode {
    constructor(id, label) {
        this.id = id
        this.label = label
    }
}

class GraphLink {
    constructor(from_node, to_node) {
        this.from = from_node
        this.to = to_node
    }
}

class Graph {
    constructor(id) {
        this.id = id
        this.nodes = DataSet()
        this.edges = DataSet()
    }

    create(id) {
        container = document.getElementById(id)
        var nodes = new DataSet([
            new GraphNode(1, 'Node 1'),
            new GraphNode(2, 'Node 2'),
            new GraphNode(3, 'Node 3'),
            new GraphNode(4, 'Node 4'),
            new GraphNode(5, 'Node 5')
        ]);
        
        
        var edges = new DataSet([
            { from: 1, to: 3 },
            { from: 1, to: 2 },
            { from: 2, to: 4 },
            { from: 2, to: 5 }
        ]);
        
        
        var data = {
            nodes: nodes,
            edges: edges
        };
        var options = {};
        var container = document.getElementById(id);
        var network = new Network(container, data, options);
        return network
    }
}

export {GraphNode, GraphLink, Graph}
