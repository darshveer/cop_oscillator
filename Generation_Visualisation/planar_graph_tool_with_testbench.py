#!/usr/bin/env python3
"""
Single-file tool that:
 - Prompts for chip rows/cols
 - Prompts for number of graph nodes
 - Generates a connected planar graph (degree ≤6)
 - Optionally visualizes the graph
 - Writes an NGSPICE-runnable .cir testbench using a given network subckt file

Usage:
    python planar_graph_tool.py --network network_6x6.subckt.sp --visualize
"""

import random
import argparse
import math
import matplotlib.pyplot as plt
import os


# ============================================================
# Hex neighbor rule (same as chip)
# ============================================================
def hex_neighbors(rows, cols, r, c):
    if r % 2 == 0:
        cand = [
            (r, c-1), (r, c+1),
            (r-1, c-1), (r-1, c),
            (r+1, c-1), (r+1, c)
        ]
    else:
        cand = [
            (r, c-1), (r, c+1),
            (r-1, c), (r-1, c+1),
            (r+1, c), (r+1, c+1)
        ]
    return [(rr, cc) for rr, cc in cand if 0 <= rr < rows and 0 <= cc < cols]


# ============================================================
# Generate planar, connected graph on hex grid
# ============================================================
def generate_planar_graph(rows, cols, num_nodes, seed=None):
    if seed is not None:
        random.seed(seed)

    max_cells = rows * cols
    if num_nodes >= max_cells:
        raise ValueError("Nodes must be < rows*cols")

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

    # Build spanning tree first
    unvisited = set(nodes)
    visited = set()
    start = unvisited.pop()
    visited.add(start)

    while unvisited:
        nxt = unvisited.pop()
        r2, c2 = pos_map[nxt]

        # Find visited hex-adjacent parent
        parents = []
        for v in visited:
            r1, c1 = pos_map[v]
            if (r2, c2) in hex_neighbors(rows, cols, r1, c1):
                parents.append(v)

        if not parents:
            return generate_planar_graph(rows, cols, num_nodes, seed)  # retry

        parent = random.choice(parents)
        add_edge(parent, nxt)
        visited.add(nxt)

    # Add extra planar edges
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


def visualize_graph(nodes, edges, pos_map):
    plt.figure(figsize=(10, 8))
    coords = {}

    for n in nodes:
        r, c = pos_map[n]
        coords[n] = hex_xy(r, c)

    for u, v in edges:
        x1, y1 = coords[u]
        x2, y2 = coords[v]
        plt.plot([x1, x2], [y1, y2], '-', color='gray')

    for n in nodes:
        x, y = coords[n]
        plt.scatter(x, y, s=250, color='skyblue', edgecolors='black')
        plt.text(x, y, n, ha='center', va='center', fontsize=10)

    plt.axis("equal")
    plt.axis("off")
    plt.title("Planar Graph on Hex Grid")
    plt.show()


# ============================================================
# Coupler enable naming
# ============================================================
def en_ro(r, c):
    return f"EN_RO_{r}_{c}"


def en_c(r1, c1, r2, c2):
    return f"EN_C_{r1}_{c1}__{r2}_{c2}"


def probe_node(r, c):
    return f"N_{r}_{c}_1"


# ============================================================
# NGSPICE testbench writer
# ============================================================
def write_testbench(rows, cols, nodes, edges, pos_map, network_file, outname):
    # Build enables in correct order
    ro_en = [en_ro(r, c) for r in range(rows) for c in range(cols)]

    coupler_pairs = []
    for r in range(rows):
        for c in range(cols):
            for rr, cc in hex_neighbors(rows, cols, r, c):
                if (rr, cc, r, c) not in coupler_pairs:
                    coupler_pairs.append((r, c, rr, cc))

    coupler_en = [en_c(r, c, rr, cc) for (r, c, rr, cc) in sorted(coupler_pairs)]
    probe_ports = [probe_node(r, c) for r in range(rows) for c in range(cols)]

    # Reverse map: (r,c) → node label
    rev = {pos_map[n]: n for n in nodes}
    edge_set = set(tuple(sorted(e)) for e in edges)

    with open(outname, "w") as f:
        f.write(f"* Auto-testbench (planar graph mapped to RO grid)\n\n")

        # REQUIRED include files:
        f.write('.include "ptm_45nm_lp.l"\n')
        f.write('.include "inv.subckt"\n')
        f.write('.include "nand.subckt"\n')
        f.write('.include "ring_osc.subckt"\n')
        f.write('.include "coupling.subckt"\n')
        f.write(f'.include "{network_file}"\n\n')

        # DUT instance
        f.write("Xdut ")
        for p in ro_en: f.write(p + " ")
        for p in coupler_en: f.write(p + " ")
        for p in probe_ports: f.write(p + " ")
        f.write("vdd gnd RING_OSC_NETWORK\n\n")

        # RO enables
        f.write("* RO enables\n")
        active = set(pos_map[n] for n in nodes)
        for r in range(rows):
            for c in range(cols):
                val = 1 #if (r, c) in active else 0
                f.write(f"V_{en_ro(r,c)} {en_ro(r,c)} gnd {val}\n")
        f.write("\n")

        # Coupler enables
        f.write("* Coupler enables\n")
        for (r1, c1, r2, c2) in sorted(coupler_pairs):
            u = rev.get((r1, c1), None)
            v = rev.get((r2, c2), None)
            on = 0
            if u is not None and v is not None:
                if tuple(sorted((u, v))) in edge_set:
                    on = 1
            f.write(f"V_{en_c(r1,c1,r2,c2)} {en_c(r1,c1,r2,c2)} gnd {on}\n")
        f.write("\n")

        # Supplies
        f.write("VDD vdd gnd 1.0\n\n")

        # Control block
        f.write(".control\n")
        f.write("tran 5ps 5ns\n")
        f.write("set filetype=ascii\n")
        f.write("wrdata output_nodes.csv ")
        for p in probe_ports:
            f.write(p + " ")
        f.write("\nquit\n.endc\n\n")

        f.write(".end\n")

    print(f"\nTestbench written to: {outname}")


# ============================================================
# Main
# ============================================================
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--network", required=True,
                        help="Path to network subckt file (RING_OSC_NETWORK)")
    parser.add_argument("--visualize", action="store_true",
                        help="Show graph visualization")
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--out", default="testbench.cir")
    args = parser.parse_args()

    print("\n==== PLANAR GRAPH TOOL ====\n")

    rows = int(input("Chip rows: "))
    cols = int(input("Chip cols: "))
    num = int(input("Number of graph nodes (< rows*cols): "))

    print("\nGenerating graph...")
    nodes, edges, pos_map = generate_planar_graph(rows, cols, num, seed=args.seed)

    print("\nNodes:", nodes)
    print("Edges:", edges)
    print("Positions:", pos_map)

    if args.visualize:
        visualize_graph(nodes, edges, pos_map)

    write_testbench(rows, cols, nodes, edges, pos_map, args.network, args.out)


if __name__ == "__main__":
    main()
