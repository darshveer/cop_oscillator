import re
import sys
import matplotlib.pyplot as plt

# -------------------------------------------------------------
# Parse netlist (header-safe)
# -------------------------------------------------------------
def parse_netlist(path):
    ro_positions = []
    edges = []

    with open(path, "r") as f:
        for line in f:
            line = line.strip()

            # Skip blank lines & comments
            if not line or line.startswith("*"):
                continue

            # Skip includes and subckt beginnings/endings
            if line.startswith(".include"):
                continue
            if line.startswith(".subckt"):
                continue
            if line.startswith(".ends"):
                continue
            if line.startswith("."):
                continue  # handles .control, .model, etc.

            # ---- Parse RO instance ----
            # Example: XRO_3_5 N_3_5_1 N_3_5_2 ... EN_RO_3_5 vdd gnd RING_OSC
            m = re.match(r"XRO_(\d+)_(\d+)\b", line)
            if m:
                r, c = map(int, m.groups())
                ro_positions.append((r, c))
                continue

            # ---- Parse coupler instance ----
            # Example: XCPL_3_5__4_6 EN_C_3_5__4_6 N_3_5_1 N_4_6_3 vdd gnd COUPLING
            m = re.match(r"XCPL_(\d+)_(\d+)__(\d+)_(\d+)\b", line)
            if m:
                r1, c1, r2, c2 = map(int, m.groups())
                edges.append(((r1, c1), (r2, c2)))
                continue

    return ro_positions, edges


# -------------------------------------------------------------
# Convert (r,c) → flattened hex coordinates
# -------------------------------------------------------------
def hex_position(r, c, size=1.0):
    dx = (3**0.5) * size     # horizontal distance
    dy = 1.5 * size          # vertical distance

    # ODD rows shifted right (correct hex structure)
    x = c * dx + (r % 2) * (dx / 2)
    y = r * dy
    return x, y


# -------------------------------------------------------------
# Draw network
# -------------------------------------------------------------
def draw_network(ro_positions, edges):
    plt.figure(figsize=(14, 10))

    pos_map = {}

    # Assign coordinates
    for (r, c) in ro_positions:
        pos_map[(r, c)] = hex_position(r, c)

    # Draw edges
    for (a, b) in edges:
        x1, y1 = pos_map[a]
        x2, y2 = pos_map[b]
        plt.plot([x1, x2], [y1, y2], '-', color='gray', linewidth=1)

    # Draw oscillator nodes
    for (r, c), (x, y) in pos_map.items():
        plt.scatter([x], [y], s=200, color='skyblue', edgecolors='black')
        plt.text(x, y, f"{r},{c}", ha='center', va='center', fontsize=10)

    plt.title("Hexagonal Ring Oscillator Network (parsed from SPICE netlist)")
    plt.axis("equal")
    plt.axis("off")
    plt.tight_layout()
    plt.show()


# -------------------------------------------------------------
# Main
# -------------------------------------------------------------
if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python visualize_network.py <netlist.sp>")
        sys.exit(1)

    netfile = sys.argv[1]

    ro_positions, edges = parse_netlist(netfile)

    print(f"Found {len(ro_positions)} RING_OSC units.")
    print(f"Found {len(edges)} coupler connections.")
    print("Drawing network...")

    draw_network(ro_positions, edges)
