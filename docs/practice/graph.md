# Working with the Graph

GreenGraph is using the [NetworkX library](https://networkx.org/documentation/stable/) to store information in a graph structure. This means that all of the methods and algorithms available in NetworkX can be used to manipulate the graph. Also, large language models (LLMs) can be used for graph-related queries with high accuracy, since NetworkX is a well-known library with a large user base.

!!! note
    some note
    ```python
    G = nx.MultiDiGraph()

    # Add three nodes with attributes
    G.add_node(1, type='biosphere', label='Forest', size=100)
    G.add_node(2, type='technosphere', label='Factory', size=50)
    G.add_node(3, type='biosphere', label='River', size=75)
    ```

!!! tip
    We recommend following the [NetworkX Tutorial](https://networkx.org/documentation/stable/tutorial.html) for basic usage of the library.

## Selecting Nodes

### How can I select a specific node from a graph?

```python

```

### How can I view all nodes that have a specific attribute?

!!! info
    [`graph.nodes(data=True)`](https://networkx.org/documentation/stable/reference/classes/generated/networkx.Graph.nodes.html) returns a networkx `NodeDataView` object, which is a dictionary-like object that allows to iterate over the nodes and their attributes.

We can use a [Python list comprehension](https://docs.python.org/3/tutorial/datastructures.html#list-comprehensions) to filter the nodes based on their attributes. For example, to get all nodes with the attribute `type` equal to `technosphere`, we can do:

```python
[
    (node, attrs) for node, attrs in gg.graph.nodes(data=True)
    if attrs['type'] == 'technosphere'
]
```

### How can I count the number of nodes with a specific attribute?

We can use a [Python list comprehension](https://docs.python.org/3/tutorial/datastructures.html#list-comprehensions) to filter the nodes based on their attributes. Then, we can use the `len()` function to count the number of nodes in the list. For example, to count the number of nodes with the attribute `type` equal to `technosphere`, we can do:

```python
len([node for node, attrs in gg.graph.nodes(data=True) if attrs['type'] == 'technosphere'])
```

### How can I get the attributes of a specific node?

We can use the `graph.nodes[node]` method to get the attributes of a specific node. For example, to get the attributes of the node with [UUID](https://en.wikipedia.org/wiki/Universally_unique_identifier) `1234`, we can do:

```python
gg.graph.nodes[1234]
```

!!! info
    In GreenGraph, every node has a unique identifier (UUID) that is used to identify the node in the graph. This UUID is not human-readable, but it is guaranteed to be unique across all nodes in the graph. The UUID is generated using the [uuid4()](https://docs.python.org/3/library/uuid.html#uuid.uuid4) function from the Python standard library. Only node attributes (`name`, `unit`, etc.) are  human-readable.

### How can I modify the attributes of a specific node?

We can use the `graph.nodes[node].update()` method to modify the attributes of a specific node. For example, to change the `label` attribute of the node with UUID `1234` to `New label`, we can do:

```python
gg.graph.nodes[1234].update({'label': 'New label'})
```

### How can I view all nodes connected to a specific node?

!!! info
    NetworkX offers the [`neighbors()`](https://networkx.org/documentation/stable/reference/classes/generated/networkx.Graph.neighbors.html) method for outgoing connections and [`predecessors()`](https://networkx.org/documentation/stable/reference/classes/generated/networkx.DiGraph.successors.html) for incoming connections to nodes.

To get a list of the names of all nodes connected to a specific node, we can use the `graph.successors(node)` method and then use a list comprehension to get the names of the nodes. For example, to get the names of all nodes connected to the node with UUID `1234`, we can do:

```python
[gg.graph.nodes[n]['name'] for n in gg.graph.successors(1234)]
```