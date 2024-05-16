class Gateway {
    constructor(node) {
        this.node = node
    }
}

class Network {

    constructor(id, label, nodes, subnets = []) {
        this.id = id
        this.label = label
        this.shape = 'icon'
        this.icon = new NetworkIcon('')
        this.nodes = nodes
    }
}

class NetworkLink {
    constructor(from, to) {
        this.from = from
        this.to = to
    }
}

class NetworkIcon {
    constructor(color, size = 50) {
        this.color = color
        this.shape = 'icon'
        this.size = size
        this.face = '"bootstrap-icons"'
        this.code = '\uF18B'
    }
}

class NetworkStorage {

    constructor(networks, links, networkData) {
        this.networks = networks
        this.links = links
        this.networkData = networkData
        this.clustered = false
        var source_nodes = []
        var source_edges = []

        networkData.nodes.forEach(node => {
            source_nodes.push(JSON.parse(JSON.stringify(node)))
        });

        networkData.edges.forEach(edge => {
            source_edges.push(JSON.parse(JSON.stringify(edge)))
        });

        this.source_nodes = source_nodes
        this.source_edges = source_edges
    }


    cluster() {
        if (!this.clustered) {
            this.networkData.nodes.clear()
            this.networks.forEach(net => {
                this.networkData.nodes.add(net)
            })

            this.networkData.edges.clear()
            this.links.forEach(net_link => {
                this.networkData.edges.add(net_link)
            })

            this.clustered = true
        }
    }

    deCluster() {

        if (this.clustered) {
            this.networkData.nodes.clear()
            this.source_nodes.forEach(node => {
                this.networkData.nodes.add(node)
            })

            this.networkData.edges.clear()
            this.source_edges.forEach(edge => {
                this.networkData.edges.add(edge)
            })
            
            this.clustered = false
        }
    }
}

first_net = new Network(1, '192.168.105.0/24', [1, 2])
NetworkStorage.create = async function () {
    return new NetworkStorage([first_net, { id: 2, label: 'jopa' }], [{ from: 1, to: 2 }], networkData)
}
