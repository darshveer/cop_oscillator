import random

# ============================================================
#  Hex-grid geometric neighbor rule (same as your RO network)
# ============================================================
def hex_neighbors(rows, cols, r, c):
    if r % 2 == 0:  # even row
        cand = [
            (r, c-1), (r, c+1),
            (r-1, c-1), (r-1, c),
            (r+1, c-1), (r+1, c)
        ]
    else:           # odd row
        cand = [
            (r, c-1), (r, c+1),
            (r-1, c), (r-1, c+1),
            (r+1, c), (r+1, c+1)
        ]
    return [(rr, cc) for (rr, cc) in cand if 0 <= rr < rows and 0 <= cc < cols]


# ============================================================
#  Generate a guaranteed connected planar graph on hex grid
# ============================================================
def generate_planar_graph(rows, cols, num_nodes, seed=None):
    """
    Generates a connected, planar, degree<=6 graph using a subset of the hex grid.
    Each chosen node corresponds to a real RO cell -> perfect physical embedding.

    Returns:
        nodes: list of labels "0", "1", ...
        edges: list of tuples ("u","v")
        pos_map: mapping node_label → (r,c) physical coordinate
    """

    if seed is not None:
        random.seed(seed)

    max_cells = rows * cols
    if num_nodes >= max_cells:
        raise ValueError("Number of nodes must be strictly less than rows*cols")

    # -----------------------------------------
    # 1) Choose num_nodes cells uniformly at random from the grid
    # -----------------------------------------
    all_cells = [(r, c) for r in range(rows) for c in range(cols)]
    chosen_cells = random.sample(all_cells, num_nodes)

    # node labels "0", "1", ...
    nodes = [str(i) for i in range(num_nodes)]
    pos_map = {nodes[i]: chosen_cells[i] for i in range(num_nodes)}

    # degree bookkeeping
    degree = {n: 0 for n in nodes}
    maxdeg = 6
    edges = set()

    def add_edge(u, v):
        if u == v:
            return False
        if degree[u] >= maxdeg or degree[v] >= maxdeg:
            return False
        e = tuple(sorted((u, v)))
        if e in edges:
            return False
        edges.add(e)
        degree[u] += 1
        degree[v] += 1
        return True

    # -----------------------------------------
    # 2) Build a spanning tree to ensure connectivity
    # -----------------------------------------
    unvisited = set(nodes)
    visited = set()

    start = unvisited.pop()
    visited.add(start)

    while unvisited:
        nxt = unvisited.pop()

        # Connect nxt to ANY visited neighbor cell
        r2, c2 = pos_map[nxt]

        # find visited nodes that are hex-adjacent
        neighbors = []
        for v in visited:
            r1, c1 = pos_map[v]
            if (r2, c2) in hex_neighbors(rows, cols, r1, c1):
                neighbors.append(v)

        if not neighbors:
            # This cell is isolated geometrically → put back and retry by reshuffling
            return generate_planar_graph(rows, cols, num_nodes, seed)

        parent = random.choice(neighbors)
        add_edge(parent, nxt)
        visited.add(nxt)

    # -----------------------------------------
    # 3) Add random extra planar edges
    # -----------------------------------------
    for u in nodes:
        r1, c1 = pos_map[u]
        for v in nodes:
            if u == v:
                continue
            r2, c2 = pos_map[v]

            if (r2, c2) in hex_neighbors(rows, cols, r1, c1):
                # connect with some probability
                if random.random() < 0.35:
                    add_edge(u, v)

    return nodes, list(edges), pos_map
