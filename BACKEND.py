"""
BACKEND.py - Bridge geometry and load setup
Generates node/bar layouts for Pratt, Warren, and K-Truss bridges,
then delegates structural calculations to CORE.py.
"""

import CORE as pt


# ---------------------------------------------------------------------------
# Base class
# ---------------------------------------------------------------------------

class bridge:
    """Abstract base for all bridge types. Handles shared configuration."""

    def __init__(self):
        self.step_nodes = 0
        self.nodes_min = 0
        self.nodes = 0
        self.name = "Unknown"

    # --- Node count controls ------------------------------------------------

    def more_nodes(self):
        self.nodes += self.step_nodes

    def less_nodes(self):
        if self.nodes > self.nodes_min:
            self.nodes -= self.step_nodes

    # --- Parameter setters --------------------------------------------------

    def set_height(self, height):
        self.height = height

    def set_length(self, length):
        self.length = length

    def set_material(self, material):
        self.material = material

    def set_cross(self, cross):
        """Set cross-sectional area of all members (cm²)."""
        self.cross = cross

    # --- Structure assembly -------------------------------------------------

    def create_struct(self):
        """Build the pt.structure object from nodes_dir and bars_dir."""
        node_list = [self.nodes_dir[f"node{i+1}"] for i in range(len(self.nodes_dir))]
        bar_list  = [self.bars_dir[f"bar{i+1}"]   for i in range(len(self.bars_dir))]

        # node1 → pin (2 reactions), node2 → roller (1 reaction)
        corner1 = pt.corner(90, True,  True,  self.nodes_dir["node1"])
        corner2 = pt.corner(90, True,  False, self.nodes_dir["node2"])

        self.struct = pt.structure(self.name, node_list, bar_list, [corner1, corner2])

    def set_load(self, mod, angle, pos):
        """Apply a concentrated load (kN) at node number `pos`."""
        self.load = pt.load(mod, angle, self.nodes_dir[f"node{pos}"])

    def do_calc(self):
        """Run structural analysis; returns force array."""
        calc_var = pt.calculation(self.load, self.struct)
        return calc_var.calc_forces()


# ---------------------------------------------------------------------------
# Pratt truss
# ---------------------------------------------------------------------------

class pratt(bridge):
    """
    Pratt truss: vertical members in compression, diagonals in tension.
    Diagonals slope toward the centre.
    """

    def __init__(self):
        super().__init__()
        self.step_nodes = 4
        self.nodes_min  = 8
        self.nodes      = 8
        self.name       = "Pratt"

    def build_nodes_bars(self):
        base = int((self.nodes + 2) / 2)   # number of bottom-chord nodes
        dx   = self.length / (base - 1)
        dy   = self.height

        # Nodes: node1 = left support, node2 = right support
        nd = {}
        nd["node1"] = pt.node([0, 0])
        nd["node2"] = pt.node([self.length, 0])

        for i in range(base - 2):
            nd[f"node{i*2+3}"] = pt.node([dx * (i + 1), dy])   # top chord
            nd[f"node{i*2+4}"] = pt.node([dx * (i + 1), 0])    # bottom chord

        self.nodes_dir = nd

        # Bars: end panels
        bd = {}
        bd["bar1"] = pt.beam(self.material, nd["node1"], nd["node4"], self.cross)
        bd["bar2"] = pt.beam(self.material, nd["node1"], nd["node3"], self.cross)
        bd["bar3"] = pt.beam(self.material, nd["node2"], nd[f"node{base*2-3}"], self.cross)
        bd["bar4"] = pt.beam(self.material, nd["node2"], nd[f"node{base*2-2}"], self.cross)

        # Central panels (top chord + bottom chord + vertical)
        for i in range(base - 3):
            bd[f"bar{i*3+5}"] = pt.beam(self.material, nd[f"node{i*2+3}"], nd[f"node{i*2+5}"], self.cross)
            bd[f"bar{i*3+6}"] = pt.beam(self.material, nd[f"node{i*2+4}"], nd[f"node{i*2+6}"], self.cross)
            bd[f"bar{i*3+7}"] = pt.beam(self.material, nd[f"node{i*2+3}"], nd[f"node{i*2+4}"], self.cross)

        bd[f"bar{base*3-4}"] = pt.beam(self.material, nd[f"node{base*2-3}"], nd[f"node{base*2-2}"], self.cross)

        # Diagonals (symmetric, slope toward centre)
        bi     = base * 3 - 3
        n_diag = int((base - 3) / 2)

        for i in range(n_diag):
            bd[f"bar{bi + i*2}"]   = pt.beam(self.material, nd[f"node{i*2+3}"],              nd[f"node{i*2+6}"],              self.cross)
            bd[f"bar{bi + i*2+1}"] = pt.beam(self.material, nd[f"node{base*2-3-i*2}"],       nd[f"node{base*2-4-i*2}"],       self.cross)

        self.bars_dir = bd


# ---------------------------------------------------------------------------
# Warren truss
# ---------------------------------------------------------------------------

class warren(bridge):
    """
    Warren truss: triangular panels without internal verticals.
    Note: the current diagonal logic mirrors Pratt; a fully standard
    Warren (equilateral triangles only) would need further refinement.
    """

    def __init__(self):
        super().__init__()
        self.step_nodes = 8
        self.nodes_min  = 8
        self.nodes      = 8
        self.name       = "Warren"

    def build_nodes_bars(self):
        base = int((self.nodes + 2) / 2)
        dx   = self.length / (base - 1)
        dy   = self.height

        nd = {}
        nd["node1"] = pt.node([0, 0])
        nd["node2"] = pt.node([self.length, 0])

        for i in range(base - 2):
            nd[f"node{i*2+3}"] = pt.node([dx * (i + 1), dy])
            nd[f"node{i*2+4}"] = pt.node([dx * (i + 1), 0])

        self.nodes_dir = nd

        bd = {}
        bd["bar1"] = pt.beam(self.material, nd["node1"], nd["node4"], self.cross)
        bd["bar2"] = pt.beam(self.material, nd["node1"], nd["node3"], self.cross)
        bd["bar3"] = pt.beam(self.material, nd["node2"], nd[f"node{base*2-3}"], self.cross)
        bd["bar4"] = pt.beam(self.material, nd["node2"], nd[f"node{base*2-2}"], self.cross)

        for i in range(base - 3):
            bd[f"bar{i*3+5}"] = pt.beam(self.material, nd[f"node{i*2+3}"], nd[f"node{i*2+5}"], self.cross)
            bd[f"bar{i*3+6}"] = pt.beam(self.material, nd[f"node{i*2+4}"], nd[f"node{i*2+6}"], self.cross)
            bd[f"bar{i*3+7}"] = pt.beam(self.material, nd[f"node{i*2+3}"], nd[f"node{i*2+4}"], self.cross)

        bd[f"bar{base*3-4}"] = pt.beam(self.material, nd[f"node{base*2-3}"], nd[f"node{base*2-2}"], self.cross)

        # Warren-specific diagonals (skip every other panel)
        bi     = base * 3 - 3
        n_diag = int((base - 3) / 2)

        for i in range(n_diag):
            bd[f"bar{bi + i*2}"]   = pt.beam(self.material, nd[f"node{i*4+3}"],          nd[f"node{i*4+6}"],          self.cross)
            bd[f"bar{bi + i*2+1}"] = pt.beam(self.material, nd[f"node{base*2-3-i*4}"],   nd[f"node{base*2-4-i*4}"],   self.cross)

        self.bars_dir = bd


# ---------------------------------------------------------------------------
# K-Truss
# ---------------------------------------------------------------------------

class k_type(bridge):
    """
    K-Truss: each vertical is split at mid-height so that diagonals
    meet in a 'K' shape, reducing diagonal length and buckling risk.
    """

    def __init__(self):
        super().__init__()
        self.step_nodes = 6
        self.nodes_min  = 14
        self.nodes      = 14
        self.name       = "K"

    def build_nodes_bars(self):
        base  = int((self.nodes + 7) / 3)       # number of main sections
        dx    = self.length / (base - 3)          # horizontal spacing
        dy    = self.height

        nd = {}
        # Fixed boundary nodes
        nd["node1"] = pt.node([0,                         0])
        nd["node2"] = pt.node([self.length,               0])
        nd["node3"] = pt.node([dx / 2,                   dy / 2])
        nd["node4"] = pt.node([self.length - dx / 2,     dy / 2])
        nd["node5"] = pt.node([dx / 2,                   0])
        nd["node6"] = pt.node([self.length - dx / 2,     0])

        # Interior nodes: top, mid (if not at centreline), bottom
        counter = 7
        for i in range(base - 4):
            nd[f"node{counter}"] = pt.node([dx * (i + 1), dy])
            counter += 1
            if dx * (i + 1) != self.length / 2:
                nd[f"node{counter}"] = pt.node([dx * (i + 1), dy / 2])
                counter += 1
            nd[f"node{counter}"] = pt.node([dx * (i + 1), 0])
            counter += 1

        counter -= 1   # total node count
        self.nodes_dir = nd

        bd = {}
        # Left end panel
        bd["bar1"]  = pt.beam(self.material, nd["node1"], nd["node3"], self.cross)
        bd["bar2"]  = pt.beam(self.material, nd["node1"], nd["node5"], self.cross)
        bd["bar3"]  = pt.beam(self.material, nd["node3"], nd["node5"], self.cross)
        bd["bar4"]  = pt.beam(self.material, nd["node3"], nd["node7"], self.cross)
        bd["bar5"]  = pt.beam(self.material, nd["node3"], nd["node9"], self.cross)
        bd["bar6"]  = pt.beam(self.material, nd["node5"], nd["node9"], self.cross)
        # Right end panel
        bd["bar7"]  = pt.beam(self.material, nd["node2"], nd["node4"], self.cross)
        bd["bar8"]  = pt.beam(self.material, nd["node2"], nd["node6"], self.cross)
        bd["bar9"]  = pt.beam(self.material, nd["node4"], nd["node6"], self.cross)
        bd["bar10"] = pt.beam(self.material, nd["node4"], nd[f"node{counter-2}"], self.cross)
        bd["bar11"] = pt.beam(self.material, nd["node4"], nd[f"node{counter}"],   self.cross)
        bd["bar12"] = pt.beam(self.material, nd["node6"], nd[f"node{counter}"],   self.cross)

        half   = int((base - 5) / 2)
        middle = 13

        # Left-half interior panels
        for i in range(half):
            bd[f"bar{i*6+13}"] = pt.beam(self.material, nd[f"node{i*3+7}"],  nd[f"node{i*3+10}"], self.cross)
            bd[f"bar{i*6+14}"] = pt.beam(self.material, nd[f"node{i*3+7}"],  nd[f"node{i*3+8}"],  self.cross)
            bd[f"bar{i*6+15}"] = pt.beam(self.material, nd[f"node{i*3+8}"],  nd[f"node{i*3+9}"],  self.cross)

            next_node = f"node{i*3+11}" if i == half - 1 else f"node{i*3+12}"
            bd[f"bar{i*6+16}"] = pt.beam(self.material, nd[f"node{i*3+9}"],  nd[next_node],        self.cross)
            bd[f"bar{i*6+17}"] = pt.beam(self.material, nd[f"node{i*3+8}"],  nd[f"node{i*3+10}"], self.cross)
            bd[f"bar{i*6+18}"] = pt.beam(self.material, nd[f"node{i*3+8}"],  nd[next_node],        self.cross)

        # Centre vertical
        top    = half * 3 + 7
        bottom = top + 1
        middle = 13 + half * 6
        bd[f"bar{middle}"] = pt.beam(self.material, nd[f"node{top}"], nd[f"node{bottom}"], self.cross)
        middle += 1

        # Right-half interior panels (mirrored)
        for i in range(half):
            prev_node = f"node{i*3+top}" if i == 0 else f"node{i*3+top-1}"
            bd[f"bar{i*6+middle}"]   = pt.beam(self.material, nd[f"node{i*3+top+2}"], nd[prev_node],             self.cross)
            bd[f"bar{i*6+middle+1}"] = pt.beam(self.material, nd[f"node{i*3+top+2}"], nd[f"node{i*3+top+3}"],   self.cross)
            bd[f"bar{i*6+middle+2}"] = pt.beam(self.material, nd[f"node{i*3+top+3}"], nd[f"node{i*3+top+4}"],   self.cross)
            bd[f"bar{i*6+middle+3}"] = pt.beam(self.material, nd[f"node{i*3+top+4}"], nd[f"node{i*3+top+1}"],   self.cross)
            bd[f"bar{i*6+middle+4}"] = pt.beam(self.material, nd[f"node{i*3+top+3}"], nd[f"node{i*3+top+1}"],   self.cross)
            bd[f"bar{i*6+middle+5}"] = pt.beam(self.material, nd[f"node{i*3+top+3}"], nd[prev_node],             self.cross)

        self.bars_dir = bd
