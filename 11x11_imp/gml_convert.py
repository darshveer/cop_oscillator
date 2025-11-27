import re
import sys
import csv
import math


def load_signum_csv(csv_file):
    """Node -> signum (+1/-1/0 or None if NaN)."""
    signum = {}
    with open(csv_file, "r") as f:
        reader = csv.DictReader(f)
        for row in reader:
            name = row["Node"]
            raw_val = row["Signum"].strip()

            m = re.match(r"N_(\d+)_(\d+)_\d+", name)
            if not m:
                continue
            r, c = map(int, m.groups())

            try:
                if raw_val.lower() == "nan" or raw_val == "":
                    val = None
                else:
                    v = float(raw_val)
                    val = int(v) if not math.isnan(v) else None
            except Exception:
                val = None

            signum[(r, c)] = val
    return signum


def parse_enables(enable_file):
    """From testbench.cir get: enabled ROs and couplers."""
    ro_enable = {}
    c_enable = {}

    with open(enable_file, "r") as f:
        for line in f:
            line = line.strip()

            # V_EN_RO_r_c EN_RO_r_c gnd 0/1
            m = re.match(r"V_EN_RO_(\d+)_(\d+)\s+\S+\s+\S+\s+([01])$", line)
            if m:
                r, c, val = m.groups()
                ro_enable[(int(r), int(c))] = int(val)
                continue

            # V_EN_C_r1_c1__r2_c2 EN_C_r1_c1__r2_c2 gnd 0/1
            m = re.match(r"V_EN_C_(\d+)_(\d+)__(\d+)_(\d+)\s+\S+\s+\S+\s+([01])$", line)
            if m:
                r1, c1, r2, c2, val = m.groups()
                c_enable[(int(r1), int(c1), int(r2), int(c2))] = int(val)
                continue

    return ro_enable, c_enable


def parse_network(net_file):
    """From network.sp get all ROs and coupler connections."""
    ro_positions = []
    edges = []

    with open(net_file, "r") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("*"):
                continue

            # XRO_r_c ...
            m = re.match(r"XRO_(\d+)_(\d+)\b", line)
            if m:
                ro_positions.append(tuple(map(int, m.groups())))
                continue

            # XCPL_r1_c1__r2_c2 ...
            m = re.match(r"XCPL_(\d+)_(\d+)__(\d+)_(\d+)\b", line)
            if m:
                r1, c1, r2, c2 = map(int, m.groups())
                edges.append(((r1, c1), (r2, c2)))
                continue

    return ro_positions, edges


def hex_position(r, c, size=1.0):
    """Same layout coordinates as the visualizer."""
    dx = math.sqrt(3) * size
    dy = 1.5 * size
    x = c * dx + (r % 2) * (dx / 2)
    y = r * dy
    return x, y


def write_gml(ro_positions, edges, ro_enable, c_enable, signum_map, out_gml):
    # Only ROs with enable=1
    active_nodes = [p for p in ro_positions if ro_enable.get(p, 0) == 1]
    id_for_node = {p: i for i, p in enumerate(sorted(active_nodes))}

    with open(out_gml, "w") as f:
        f.write("graph [\n")
        f.write("  directed 0\n")

        # ----- Nodes -----
        for (r, c), nid in id_for_node.items():
            x, y = hex_position(r, c)
            sig = signum_map.get((r, c), None)

            f.write("  node [\n")
            f.write(f"    id {nid}\n")
            f.write(f"    label \"{r},{c}\"\n")
            f.write(f"    r {r}\n")
            f.write(f"    c {c}\n")
            if sig is None:
                f.write("    signum -999\n")   # use -999 for NaN
            else:
                f.write(f"    signum {sig}\n")
            f.write(f"    x {x}\n")
            f.write(f"    y {y}\n")
            f.write("  ]\n")

        # ----- Edges -----
        for a, b in edges:
            key = (a[0], a[1], b[0], b[1])
            rkey = (b[0], b[1], a[0], a[1])

            if not (c_enable.get(key, 0) == 1 or c_enable.get(rkey, 0) == 1):
                continue
            if a not in id_for_node or b not in id_for_node:
                continue

            src = id_for_node[a]
            tgt = id_for_node[b]
            f.write("  edge [\n")
            f.write(f"    source {src}\n")
            f.write(f"    target {tgt}\n")
            f.write("  ]\n")

        f.write("]\n")

    print(f"GML written to {out_gml}")
    print(f"Nodes: {len(id_for_node)}")


if __name__ == "__main__":
    if len(sys.argv) != 5:
        print("Usage:")
        print("  python netlist_to_gml.py <testbench.cir> <network.sp> <signum_output.csv> <output.gml>")
        sys.exit(1)

    enable_file = sys.argv[1]     # testbench_7.cir
    network_file = sys.argv[2]    # your network.sp
    signum_csv = sys.argv[3]      # signum_output.csv
    out_gml = sys.argv[4]

    ro_enable, c_enable = parse_enables(enable_file)
    ro_positions, edges = parse_network(network_file)
    signum_map = load_signum_csv(signum_csv)

    write_gml(ro_positions, edges, ro_enable, c_enable, signum_map, out_gml)
