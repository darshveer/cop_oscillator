def generate_hex_network(rows, cols, network_name="RING_OSC_NETWORK"):

    lines = []
    #
    # Include all required models / subcircuits
    #
    lines.append('.include "ptm_45nm_lp.l"')
    lines.append('.include "inv.subckt"')
    lines.append('.include "nand.subckt"')
    lines.append('.include "ring_osc.subckt"')
    lines.append('.include "coupling.subckt"')
    lines.append("")  # spacing


    def node_name(r, c, pin):
        return f"N_{r}_{c}_{pin}"

    def enable_name_r(r, c):
        return f"EN_RO_{r}_{c}"

    def enable_name_c(r1, c1, r2, c2):
        return f"EN_C_{r1}_{c1}__{r2}_{c2}"


    # ----------------------------------------------------------
    #  HEX NEIGHBOR RULE
    # ----------------------------------------------------------
    def neighbors(r, c):
        if r % 2 == 0:  # EVEN row
            cand = [
                (r, c-1), (r, c+1),
                (r-1, c-1), (r-1, c),
                (r+1, c-1), (r+1, c)
            ]
        else:  # ODD row
            cand = [
                (r, c-1), (r, c+1),
                (r-1, c), (r-1, c+1),
                (r+1, c), (r+1, c+1)
            ]
        return [(rr, cc) for (rr, cc) in cand if 0 <= rr < rows and 0 <= cc < cols]


    # ----------------------------------------------------------
    # Collect enables
    # ----------------------------------------------------------
    ro_enables = [enable_name_r(r, c) for r in range(rows) for c in range(cols)]

    coupling_pairs = set()
    for r in range(rows):
        for c in range(cols):
            for (rr, cc) in neighbors(r, c):
                if (rr, cc, r, c) not in coupling_pairs:
                    coupling_pairs.add((r, c, rr, cc))

    coup_enables = [
        enable_name_c(r1, c1, r2, c2)
        for (r1, c1, r2, c2) in sorted(coupling_pairs)
    ]


    # ----------------------------------------------------------
    # NEW: Probe outputs (node 1 of each RO)
    # ----------------------------------------------------------
    probe_ports = [node_name(r, c, 1) for r in range(rows) for c in range(cols)]


    # ----------------------------------------------------------
    # Build .subckt header
    # ----------------------------------------------------------
    ports = ro_enables + coup_enables + probe_ports + ["vdd", "gnd"]
    lines.append(f".subckt {network_name} " + " ".join(ports))
    lines.append("")


    # ----------------------------------------------------------
    # Instantiate all RING_OSC blocks
    # ----------------------------------------------------------
    for r in range(rows):
        for c in range(cols):
            nodes = " ".join(node_name(r, c, pin) for pin in range(1, 8))

            lines.append(
                f"XRO_{r}_{c} {nodes} {enable_name_r(r,c)} vdd gnd RING_OSC"
            )

            # No need for buffers — exported directly:
            #   N_r_c_1 is already exposed as a subckt pin
            # That means the user can measure it from outside.


    lines.append("")


    # ----------------------------------------------------------
    # Instantiate all COUPLERS (node1 → node3)
    # ----------------------------------------------------------
    for (r1, c1, r2, c2) in sorted(coupling_pairs):

        en = enable_name_c(r1, c1, r2, c2)
        nodeA = node_name(r1, c1, 1)
        nodeB = node_name(r2, c2, 3)

        lines.append(
            f"XCPL_{r1}_{c1}__{r2}_{c2} {en} {nodeA} {nodeB} vdd gnd COUPLING"
        )


    lines.append(f"\n.ends {network_name}\n")

    return "\n".join(lines)


if __name__ == "__main__":
    import sys

    if len(sys.argv) != 4:
        print("Usage: python gen_network.py <rows> <cols> <outfile>")
        sys.exit(1)

    rows = int(sys.argv[1])
    cols = int(sys.argv[2])
    outfile = sys.argv[3]

    netlist = generate_hex_network(rows, cols)

    with open(outfile, "w") as f:
        f.write(netlist)

    print(f"Generated hex lattice network:")
    print(f"  rows      = {rows}")
    print(f"  cols      = {cols}")
    print(f"  output    = {outfile}")