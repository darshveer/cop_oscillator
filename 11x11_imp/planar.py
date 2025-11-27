#!/usr/bin/env python3

import random
import argparse

# ================================================================
#  HEX GRID NEIGHBOR FUNCTION
# ================================================================
def hex_neighbors(rows, cols, r, c):
    """Returns valid hex-grid neighbors around cell (r, c)."""

    if r % 2 == 0:  # even row
        cand = [
            (r, c-1), (r, c+1),
            (r-1, c-1), (r-1, c),
            (r+1, c-1), (r+1, c)
        ]
    else:  # odd row
        cand = [
            (r, c-1), (r, c+1),
            (r-1, c), (r-1, c+1),
            (r+1, c), (r+1, c+1)
        ]

    return [(rr, cc) for rr, cc in cand if 0 <= rr < rows and 0 <= cc < cols]


# ================================================================
#  SAFE PLANAR GRAPH GENERATOR (NO RECURSION! NO RESTARTS!)
# ================================================================
def generate_planar_graph_safe(rows, cols, num_nodes, seed=None):
    """
    SAFE planar graph generator:
    - NO recursion
    - NO restarts
    - Always produces a connected planar graph
    - Only hex-adjacent nodes can connect
    """

    if seed is not None:
        random.seed(seed)

    max_cells = rows * cols
    if num_nodes > max_cells:
        raise ValueError("num_nodes must be <= rows*cols")

    # 1. Choose positions randomly
    all_cells = [(r, c) for r in range(rows) for c in range(cols)]
    chosen = random.sample(all_cells, num_nodes)

    nodes = [str(i) for i in range(num_nodes)]
    pos_map = {nodes[i]: chosen[i] for i in range(num_nodes)}

    edges = set()
    degree = {n: 0 for n in nodes}
    MAXDEG = 6

    def add_edge(a, b):
        """Safe add: respects planar limits."""
        if a == b:
            return False
        if degree[a] >= MAXDEG or degree[b] >= MAXDEG:
            return False

        e = tuple(sorted((a, b)))
        if e in edges:
            return False

        edges.add(e)
        degree[a] += 1
        degree[b] += 1
        return True

    # 2. Build connected graph (BFS expansion)
    remaining = set(nodes)
    root = remaining.pop()
    visited = {root}
    queue = [root]

    while remaining:
        u = queue.pop(0)
        ru, cu = pos_map[u]

        hex_adj = hex_neighbors(rows, cols, ru, cu)
        neighbors = [w for w in list(remaining) if pos_map[w] in hex_adj]

        # connect BFS-style
        for w in neighbors:
            if add_edge(u, w):
                visited.add(w)
                remaining.remove(w)
                queue.append(w)

        # If BFS stuck but remaining nodes exist
        if not queue and remaining:

            # Pick some visited node with free degree
            parents = [p for p in visited if degree[p] < MAXDEG]
            p = random.choice(parents)
            pr, pc = pos_map[p]

            # Try to connect to remaining nodes
            fixed = False
            for w in list(remaining):
                wr, wc = pos_map[w]
                if (wr, wc) in hex_neighbors(rows, cols, pr, pc):
                    if add_edge(p, w):
                        visited.add(w)
                        remaining.remove(w)
                        queue.append(w)
                        fixed = True
                        break

            # FORCE FIX: If ZERO adjacency, connect to nearest node
            if not fixed:
                w = list(remaining)[0]

                wr, wc = pos_map[w]
                best_p = min(
                    visited,
                    key=lambda vv: (pos_map[vv][0] - wr) ** 2 +
                                   (pos_map[vv][1] - wc) ** 2
                )

                add_edge(best_p, w)
                visited.add(w)
                remaining.remove(w)
                queue.append(w)

    # 3. Add optional random planar edges
    for u in nodes:
        ru, cu = pos_map[u]
        for v in nodes:
            if u == v:
                continue
            rv, cv = pos_map[v]
            if (rv, cv) in hex_neighbors(rows, cols, ru, cu):
                if random.random() < 0.30:
                    add_edge(u, v)

    return nodes, list(edges), pos_map


# ================================================================
#  TESTBENCH UTILITY FUNCTIONS
# ================================================================
def en_ro(r, c):
    # Matches Visualize_edges.py: V_EN_RO_r_c ...
    return f"EN_RO_{r}_{c}"

def en_c(r1, c1, r2, c2):
    """
    VERY IMPORTANT:
    Must match Visualize_edges.py regex:
      V_EN_C_(\d+)_(\d+)__(\d+)_(\d+)
    so the enable node must be EN_C_r1_c1__r2_c2
    """
    return f"EN_C_{r1}_{c1}__{r2}_{c2}"

def probe_node(r, c):
    return f"N_{r}_{c}_1"


# ================================================================
#  WRITE NGSPICE TESTBENCH (planar_old-style enables)
# ================================================================
def write_testbench(rows, cols, nodes, edges, pos_map, network_file, outname):
    """
    - Drives EN_RO_x_y = 1 only for grid locations used by the generated graph.
    - Drives EN_C_* = 1 only if both endpoints exist AND the corresponding edge exists.
    - All unused couplers and unused ROs are disabled (EN = 0), matching planar_old behavior.
    """

    # All RO enable nodes in the full grid
    all_ro_en = [en_ro(r, c) for r in range(rows) for c in range(cols)]

    # All possible coupler pairs for the full grid (hex neighbors)
    all_coupler_pairs = []
    for r in range(rows):
        for c in range(cols):
            for rr, cc in hex_neighbors(rows, cols, r, c):
                # avoid double counting (r,c,rr,cc) vs (rr,cc,r,c)
                if (rr, cc, r, c) not in all_coupler_pairs:
                    all_coupler_pairs.append((r, c, rr, cc))

    all_coupler_en = [
        en_c(r, c, rr, cc) for (r, c, rr, cc) in sorted(all_coupler_pairs)
    ]

    # Probe nodes for the full grid
    probe_ports = [probe_node(r, c) for r in range(rows) for c in range(cols)]

    # Map from (row,col) -> node label; only cells used by the graph are present
    rev = {pos_map[n]: n for n in nodes}
    edge_set = set(tuple(sorted(e)) for e in edges)

    with open(outname, "w") as f:
        f.write("* Auto-testbench (planar graph mapped to RO grid)\n\n")

        f.write('.include "ptm_45nm_lp.l"\n')
        f.write('.include "inv.subckt"\n')
        f.write('.include "nand.subckt"\n')
        f.write('.include "ring_osc.subckt"\n')
        f.write('.include "coupling.subckt"\n')
        f.write(f'.include "{network_file}"\n\n')

        # Instance of the entire network subcircuit:
        #  [all RO enables] [all coupler enables] [all probe ports] vdd gnd
        f.write("Xdut ")
        f.write(" ".join(all_ro_en + all_coupler_en + probe_ports))
        f.write(" vdd gnd RING_OSC_NETWORK\n\n")

        # ---------------- RO enables ----------------
        f.write("* RO enables\n")
        for r in range(rows):
            for c in range(cols):
                node = rev.get((r, c))  # None if no graph node at this grid cell
                val = 1 if node in nodes else 0
                f.write(f"V_EN_RO_{r}_{c} {en_ro(r,c)} gnd {val}\n")
        f.write("\n")

        # ---------------- Coupler enables ----------------
        f.write("* Coupler enables\n")
        for (r1, c1, r2, c2) in sorted(all_coupler_pairs):
            u = rev.get((r1, c1))  # node label or None
            v = rev.get((r2, c2))
            on = 1 if u and v and tuple(sorted((u, v))) in edge_set else 0
            # This matches Visualize_edges.py parse_enables()
            f.write(
                f"V_EN_C_{r1}_{c1}__{r2}_{c2} "
                f"{en_c(r1,c1,r2,c2)} gnd {on}\n"
            )
        f.write("\n")

        # Supply
        f.write("VDD vdd gnd 1.0\n\n")

        # Control block: write all probe nodes to CSV
        f.write(".control\n")
        f.write("save time " + " ".join(probe_ports) + "\n")
        f.write("tran 0.1ns 2us uic\n")
        f.write("set filetype=ascii\n")
        f.write("set wr_singlescale\n")
        f.write("set wr_vecnames\n")
        f.write("set csvdelim=comma\n")
        f.write("wrdata output_nodes.csv time " + " ".join(probe_ports) + "\n")
        f.write("quit\n")
        f.write(".endc\n\n")

        f.write(".end\n")

    print(f"\nTestbench written to: {outname}")


# ================================================================
#  MAIN
# ================================================================
def main():

    parser = argparse.ArgumentParser()
    parser.add_argument("--network", required=True)
    parser.add_argument("--out", default="testbench.cir")
    parser.add_argument("--rows", type=int, required=True)
    parser.add_argument("--cols", type=int, required=True)
    parser.add_argument("--num", type=int, required=True)
    parser.add_argument("--seed", type=int, default=None)

    args = parser.parse_args()

    nodes, edges, pos_map = generate_planar_graph_safe(
        args.rows, args.cols, args.num, seed=args.seed
    )

    print("Nodes:", nodes)
    print("Edges:", edges)
    print("Positions:", pos_map)

    write_testbench(args.rows, args.cols, nodes, edges, pos_map, args.network, args.out)


if __name__ == "__main__":
    main()
