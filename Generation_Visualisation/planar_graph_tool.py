#!/usr/bin/env python3
"""
planar_graph_tool.py

A single file that:
 - Asks user for chip rows, cols
 - Asks for number of graph nodes
 - Generates a connected planar graph with degree <= 6
 - Ensures all nodes map to hex-grid positions
 - Optionally visualizes the graph (CLI flag: --visualize)

Dependencies: ONLY matplotlib (standard scientific stack)
"""

import random
import argparse
import math
import matplotlib.pyplot as plt


# ============================================================
# Hex neighbor rule (matches your chip exactly)
# ============================================================
def hex_neighbors(rows, cols, r, c):
    if r % 2 == 0:  # even row
        cand = [
            (r, c - 1), (r, c + 1),
            (r - 1, c - 1), (r - 1, c),
            (r + 1, c - 1), (r + 1, c)
        ]
    else:  # odd row
        cand = [
            (r, c - 1), (r, c + 1),
            (r - 1, c), (r - 1, c + 1),
            (r + 1, c), (r + 1, c + 1)
        ]
    return [(rr, cc) for rr, cc in cand if 0 <= rr < rows and 0 <= cc < cols]


# ============================================================
# Generate a connected planar graph (degree <= 6 always)
# ============================================================
def generate_planar_graph(rows, cols, num_nodes, seed=None):
    if seed is not None:
        random.seed(seed)

    max_cells = rows * cols
    if num_nodes >= max_cells:
        raise ValueError("Number of nodes must be STRICTLY less than rows*cols")

    # Select random RO positions for graph nodes
    all_cells = [(r, c) for r in range(rows) for c in range(cols)]
    chosen_cells = random.sample(all_cells, num_nodes)

    nodes = [str(i) for i in range(num_nodes)]
    pos_map = {nodes[i]: chosen_cells[i] for i in range(num_nodes)}

    degree = {n: 0 for n in nodes}
    edges = set()
    maxdeg = 6

    def add_edge(a, b):
        if a == b:
            return False
        if degree[a] >= maxdeg or degree[b] >= maxdeg:
            return False
        e = tuple(sorted((a, b)))
        if e in edges:
            return False
        edges.add(e)
        degree[a] += 1
        degree[b] += 1
        return True

    # ---- Build spanning tree for connectivity ----
    unvisited = set(nodes)
    visited = set()

    start = unvisited.pop()
    visited.add(start)

    while unvisited:
        nxt = unvisited.pop()
        r2, c2 = pos_map[nxt]

        # Find visited nodes that are hex-adjacent
        possible_parents = []
        for v in visited:
            r1, c1 = pos_map[v]
            if (r2, c2) in hex_neighbors(rows, cols, r1, c1):
                possible_parents.append(v)

        if not possible_parents:
            # Geometrically disconnected → rerun to get another placement
            return generate_planar_graph(rows, cols, num_nodes, seed)

        parent = random.choice(possible_parents)
        add_edge(parent, nxt)
        visited.add(nxt)

    # ---- Add more planar/hex edges randomly ----
    for u in nodes:
        r1, c1 = pos_map[u]
        for v in nodes:
            if u == v:
                continue
            r2, c2 = pos_map[v]
            if (r2, c2) in hex_neighbors(rows, cols, r1, c1):
                if random.random() < 0.35:
                    add_edge(u, v)

    return nodes, list(edges), pos_map


# ============================================================
# Visualization
# ============================================================
def hex_xy(r, c, size=1.0):
    dx = math.sqrt(3) * size
    dy = 1.5 * size
    x = c * dx + (r % 2) * (dx / 2)
    y = r * dy
    return x, y


def visualize_graph(nodes, edges, pos_map, title="Planar Graph"):
    plt.figure(figsize=(10, 8))

    coords = {}

    for n in nodes:
        r, c = pos_map[n]
        x, y = hex_xy(r, c)
        coords[n] = (x, y)

    # Draw edges
    for (u, v) in edges:
        x1, y1 = coords[u]
        x2, y2 = coords[v]
        plt.plot([x1, x2], [y1, y2], '-', color='gray')

    # Draw nodes
    for n in nodes:
        x, y = coords[n]
        plt.scatter([x], [y], s=250, color='skyblue', edgecolors='black')
        plt.text(x, y, n, ha='center', va='center', fontsize=10)

    plt.title(title)
    plt.axis("equal")
    plt.axis("off")
    plt.show()


# ============================================================
# Main CLI
# ============================================================
def main():
    parser = argparse.ArgumentParser(description="Planar Graph Generator + Visualizer")
    parser.add_argument("--visualize", action="store_true",
                        help="Display a visual of the generated planar graph")
    parser.add_argument("--seed", type=int, default=None, help="Random seed")

    args = parser.parse_args()

    print("\n==== PLANAR GRAPH GENERATOR ====")
    print("Enter chip dimensions:\n")

    rows = int(input("Number of rows in chip: "))
    cols = int(input("Number of columns in chip: "))

    print(f"Total RO cells = {rows * cols}")
    num_nodes = int(input("Number of graph nodes (must be < total cells): "))

    print("\nGenerating planar graph...")
    nodes, edges, pos_map = generate_planar_graph(rows, cols, num_nodes, seed=args.seed)

    print("\n=== GRAPH GENERATED ===")
    print(f"Nodes: {nodes}")
    print(f"Edges ({len(edges)}):")
    for e in edges:
        print(" ", e)

    print("\nNode positions on chip:")
    for n in nodes:
        print(f"  Node {n} -> RO cell {pos_map[n]}")

    if args.visualize:
        print("\nOpening visualization window...")
        visualize_graph(nodes, edges, pos_map, title="Generated Planar Graph")


if __name__ == "__main__":
    main()
