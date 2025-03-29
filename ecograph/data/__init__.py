import networkx as nx

class ecograph(nx.DiGraph):
    """
    A class representing an ecological graph, inheriting from networkx's DiGraph.
    """

    def __init__(self, *args, **kwargs):
        """
        Initializes the ecograph with the given arguments.
        """
        super().__init__(*args, **kwargs)