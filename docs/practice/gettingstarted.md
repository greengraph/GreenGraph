# Getting Started

```
import greengraph as gg

G_ecoinvent = gg.importers.databases.ecoinvent()
G_exiobase = gg.importers.databases.exiobase()

G_hybrid = gg.hybridizers.ecoinvent_exiobase(
    graph_ecoinvent = G_ecoinvent,
    graph_exiobase = G_exiobase,
    concordance_matrix = H,
    nodes_ecoinvent_to_hybridize = list_nodes_to_hybridize,
)

M_hybrid = G_hybrid.generate_matrices_from_graph()

M_hybrid.lca(
    demand='abc123', # some node
    amount=100,
)
M_hybrid.score(
    method={
        'name': 'climate something something',
        'unit': 'temperature something something',
    }
)
```