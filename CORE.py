"""
CORE.py - Structural calculation engine
Input:  geometry + loads + materials
Process: linear algebra (stiffness matrix method)
Output: internal forces, stresses, safety factors
"""

import os
import numpy as np
import pandas as pd

# Load material table from the same directory as this file
_CSV_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "materials.csv")
material_table = pd.read_csv(_CSV_PATH, sep=";")


# ---------------------------------------------------------------------------
# Geometry
# ---------------------------------------------------------------------------

class node:
    """A 2-D joint defined by its (x, y) coordinates."""

    def __init__(self, coord):
        self.coord = coord
        self.x = coord[0]
        self.y = coord[1]

    def get_angle(self, beam):
        """Return (sin, cos) of the angle this beam makes at this node."""
        other = [n for n in beam.nodes if n is not self][0]
        dx = other.x - self.x
        dy = other.y - self.y
        length = np.sqrt(dx**2 + dy**2)
        return dy / length, dx / length   # sin, cos


class beam:
    """A truss member connecting two nodes."""

    def __init__(self, material, node1, node2, area=5):
        self.material = material
        self.nodes = [node1, node2]
        self.area = area        # cross-sectional area (cm²)
        self.load_val = 0.0     # internal axial force (kN)

    def set_load(self, load_val):
        self.load_val = load_val

    def check_stress(self):
        """Return 'ok' if within yield limit, 'fail' otherwise."""
        limit_mpa = material_table.loc[
            material_table["Material"] == self.material, "(MPa)"
        ].values[0]
        # 1 MPa = 10 N/cm²; convert to kN → MPa × area / 10
        limit_kn = limit_mpa * self.area / 10
        return "ok" if abs(self.load_val) <= limit_kn else "fail"


# ---------------------------------------------------------------------------
# Supports and reactions
# ---------------------------------------------------------------------------

class corner:
    """
    Structural support (pin or roller).
      has_vertical=True,  has_horizontal=True  → pin   (2 reactions)
      has_vertical=True,  has_horizontal=False → roller (1 reaction)
    """

    def __init__(self, angle, has_vertical, has_horizontal, node):
        self.angle = angle
        self.has_vertical = has_vertical
        self.has_horizontal = has_horizontal
        self.node = node
        self.react_count = 2 if has_horizontal else 1


class reaction:
    """A single reaction force at a support node."""

    def __init__(self, angle, node):
        self.angle = angle  # degrees
        self.node = node


# ---------------------------------------------------------------------------
# Structure
# ---------------------------------------------------------------------------

class structure:
    """Assembly of nodes, beams, and supports."""

    def __init__(self, type, nodes, beams, corners):
        self.type = type
        self.nodes = nodes
        self.beams = beams
        self.corners = corners

    def check_static(self):
        """Check determinacy condition: b + r == 2n."""
        b = len(self.beams)
        r = sum(c.react_count for c in self.corners)
        n = len(self.nodes)
        status = "statically determinate" if b + r == 2 * n else "indeterminate / unstable"
        print(status)

    def get_reactions(self):
        """Expand each support into individual reaction objects."""
        react_list = []
        for c in self.corners:
            react_list.append(reaction(c.angle, c.node))
            if c.has_vertical and c.has_horizontal:
                react_list.append(reaction(c.angle + 90, c.node))
        return react_list


# ---------------------------------------------------------------------------
# Loads
# ---------------------------------------------------------------------------

class load:
    """Concentrated external force applied to a single node."""

    def __init__(self, value, angle, pos):
        self.value = value  # magnitude (kN)
        self.angle = angle  # direction (degrees)
        self.pos = pos      # target node


# ---------------------------------------------------------------------------
# Calculation
# ---------------------------------------------------------------------------

class calculation:
    """Solves the truss using the method of joints (matrix form)."""

    def __init__(self, load, structure):
        self.load = load
        self.structure = structure

    def calc_reactions(self):
        """Compute the three global support reactions (isostatica only)."""
        reactions = self.structure.get_reactions()
        if len(reactions) != 3:
            print("Not solvable: structure is not statically determinate")
            return

        k = self.load.value
        theta_k = np.radians(self.load.angle)
        node_k = self.load.pos

        col_k = np.array([
            -k * np.cos(theta_k),
            -k * np.sin(theta_k),
            0.0
        ])

        r1, r2, r3 = reactions
        t1, t2, t3 = np.radians(r1.angle), np.radians(r2.angle), np.radians(r3.angle)

        def moment_arm(r, t):
            dx = r.node.x - node_k.x
            dy = r.node.y - node_k.y
            return np.cos(t) * dy - dx * np.sin(t)

        mat = np.array([
            [np.cos(t1), np.cos(t2), np.cos(t3)],
            [np.sin(t1), np.sin(t2), np.sin(t3)],
            [moment_arm(r1, t1), moment_arm(r2, t2), moment_arm(r3, t3)]
        ])

        sol = np.linalg.solve(mat, col_k)
        print(sol)

    def calc_forces(self):
        """
        Build and solve the global equilibrium matrix.
        Returns a 1-D array [internal forces | reactions].
        """
        n = len(self.structure.nodes)
        nb = len(self.structure.beams)
        reactions = self.structure.get_reactions()
        nr = len(reactions)

        # Square matrix: 2n equations, (nb + nr) unknowns
        node_mat = np.zeros((2 * n, nb + nr))

        for i, node_i in enumerate(self.structure.nodes):
            # Beam contributions
            for j, beam_j in enumerate(self.structure.beams):
                if node_i in beam_j.nodes:
                    sin_val, cos_val = node_i.get_angle(beam_j)
                    node_mat[2 * i][j] = cos_val
                    node_mat[2 * i + 1][j] = sin_val

            # Reaction contributions
            for k, react_k in enumerate(reactions):
                if node_i is react_k.node:
                    t = np.radians(react_k.angle)
                    node_mat[2 * i][nb + k] = np.cos(t)
                    node_mat[2 * i + 1][nb + k] = np.sin(t)

        # Right-hand side: external loads (moved to RHS with negative sign)
        rhs = np.zeros(2 * n)
        for i, node_i in enumerate(self.structure.nodes):
            if node_i is self.load.pos:
                t = np.radians(self.load.angle)
                rhs[2 * i] = -self.load.value * np.cos(t)
                rhs[2 * i + 1] = -self.load.value * np.sin(t)

        return np.linalg.solve(node_mat, rhs)


# ---------------------------------------------------------------------------
# Safety check (standalone helper)
# ---------------------------------------------------------------------------

def check_safety(forces, limit):
    """
    Compare peak force against an allowable limit.
    Returns a dict with keys: safe, max, ratio, msg.
    """
    max_f = max(abs(f) for f in forces)
    ratio = (max_f / limit) * 100
    return {
        "safe": max_f < limit,
        "max": round(max_f, 2),
        "ratio": round(ratio, 2),
        "msg": "Structure safe" if max_f < limit else "Danger — limit exceeded"
    }
