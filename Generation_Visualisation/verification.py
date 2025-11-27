import re
import sys

# ============================================================
#  Parse netlist lines
# ============================================================

def load_netlist(path):
    with open(path, 'r') as f:
        lines = [line.strip() for line in f if line.strip() and not line.strip().startswith('*')]
    return lines


# ============================================================
#  Extract RO & Coupler instances
# ============================================================

def parse_ring_instance(line):
    """
    Example:
        XRO_2_3 N_2_3_1 N_2_3_2 ... EN_RO_2_3 vdd gnd RING_OSC
    """
    if "RING_OSC" not in line:
        return None
    
    tokens = line.split()
    inst = tokens[0]  # XRO_r_c

    m = re.match(r"XRO_(\d+)_(\d+)", inst)
    if not m:
        return None

    r, c = map(int, m.groups())

    # nodes N_r_c_1 ... N_r_c_7
    nodes = tokens[1:8]
    enable = tokens[8]

    return (r, c, nodes, enable)


def parse_coupler_instance(line):
    """
    Example:
        XCPL_1_2__1_3 EN_C_1_2__1_3 N_1_2_1 N_1_3_3 vdd gnd COUPLING
    """
    if "COUPLING" not in line:
        return None

    tokens = line.split()
    inst = tokens[0]  # XCPL_r1_c1__r2_c2

    m = re.match(r"XCPL_(\d+)_(\d+)__(\d+)_(\d+)", inst)
    if not m:
        return None

    r1, c1, r2, c2 = map(int, m.groups())
    enable = tokens[1]
    nodeA = tokens[2]
    nodeB = tokens[3]

    return (r1, c1, r2, c2, enable, nodeA, nodeB)


# ============================================================
#  Expected Hex Neighbors
# ============================================================

def expected_neighbors(rows, cols, r, c):
    nbrs = []
    if r % 2 == 0:  # even row
        cand = [
            (r, c - 1), (r, c + 1),
            (r - 1, c), (r - 1, c + 1),
            (r + 1, c), (r + 1, c + 1)
        ]
    else:  # odd row
        cand = [
            (r, c - 1), (r, c + 1),
            (r - 1, c - 1), (r - 1, c),
            (r + 1, c - 1), (r + 1, c)
        ]

    for rr, cc in cand:
        if 0 <= rr < rows and 0 <= cc < cols:
            nbrs.append((rr, cc))

    return nbrs


# ============================================================
#  Main verification logic
# ============================================================

def verify_network(netlist_path, rows, cols):

    lines = load_netlist(netlist_path)

    # Parsed data structures
    ring_nodes = {}
    couplings = set()
    couplings_reverse = set()

    # Parse all RING_OSC and COUPLING
    for line in lines:
        p = parse_ring_instance(line)
        if p:
            r, c, nodes, enable = p
            ring_nodes[(r, c)] = nodes
            continue

        q = parse_coupler_instance(line)
        if q:
            r1, c1, r2, c2, enable, nodeA, nodeB = q
            couplings.add((r1, c1, r2, c2))
            couplings_reverse.add((r2, c2, r1, c1))
            continue

    # Check RO count
    expected_count = rows * cols
    if len(ring_nodes) != expected_count:
        print(f"❌ ERROR: Expected {expected_count} RING_OSC blocks, found {len(ring_nodes)}")
        return

    print("✔ Correct number of RING_OSC units found.")

    # Check nodes
    for (r, c), nodes in ring_nodes.items():
        for pin in range(1, 8):
            expected = f"N_{r}_{c}_{pin}"
            if nodes[pin-1] != expected:
                print(f"❌ Node mismatch at RO({r},{c}) pin {pin}: expected {expected}, found {nodes[pin-1]}")
                return

    print("✔ All RING_OSC node names are correct.")

    # Check couplers
    for r in range(rows):
        for c in range(cols):

            want = set(expected_neighbors(rows, cols, r, c))
            have = set((rr, cc) for (rr, cc) in want if (r, c, rr, cc) in couplings)

            if want != have:
                print(f"❌ Wrong neighbors for RO({r},{c})")
                print("  Expected:", want)
                print("  Found   :", have)
                return

    print("✔ Coupler neighbor sets match expected hex connectivity.")

    # Check symmetric connections
    for (r1, c1, r2, c2) in couplings:
        if (r2, c2, r1, c1) not in couplings:
            print(f"❌ Asymmetric coupling: ({r1},{c1}) -> ({r2},{c2}) exists but reverse missing.")
            return

    print("✔ All couplings are symmetric.")

    # Check correct RO1->RO3 node mapping
    for line in lines:
        q = parse_coupler_instance(line)
        if not q:
            continue
        r1, c1, r2, c2, enable, nodeA, nodeB = q

        expA = f"N_{r1}_{c1}_1"
        expB = f"N_{r2}_{c2}_3"

        if nodeA != expA or nodeB != expB:
            print(f"❌ Coupler node mismatch XCPL_{r1}_{c1}__{r2}_{c2}")
            print(f"  Expected: {expA} -> {expB}")
            print(f"  Found   : {nodeA} -> {nodeB}")
            return

    print("✔ All couplers correctly connect RO(N1) → RO(N3).")

    print("\n🎉 VERIFICATION PASSED — network is correct.\n")


# ============================================================
#  Entry point
# ============================================================
if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Usage: python verify_network.py <netlist.sp> <rows> <cols>")
        sys.exit(1)

    netlist_path = sys.argv[1]
    rows = int(sys.argv[2])
    cols = int(sys.argv[3])

    verify_network(netlist_path, rows, cols)
