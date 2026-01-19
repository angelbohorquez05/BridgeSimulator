#Entrada: Geometría + Cargas + Materiales
#Proceso: Matemáticas puras (álgebra matricial, resistencia de materiales)
#Salida: Fuerzas internas, tensiones, factores de seguridad
import numpy as np
import pandas as pd

material_table = pd.read_csv("PUENTE/progetto_materiale.csv", sep=";")

# oggetti - motore di calcolo struturale
class node:
    def __init__(self, coord):
        self.coord = coord
        self.x = coord[0]
        self.y = coord[1]
    
    def get_angle(self, beam):
        # Calcola seno e coseno dell'angolo della trave rispetto a questo nodo
        other = [x for x in beam.nodes if x != self][0]
        
        co = other.y - self.y  # Opposto
        ca = other.x - self.x  # Adiacente
        hyp = np.sqrt(co**2 + ca**2) #lunghezza trave
        
        sin_val = co / hyp
        cos_val = ca / hyp
        return sin_val, cos_val

class beam: #trave = viga
    def __init__(self, material, node1, node2, area=5):
        self.material = material
        self.nodes = [node1, node2]
        self.area = area  # (cm²)
        self.load_val = 0.0 # Forza assiale interna (kN)
    
    def set_load(self, load_val): #assegnare valore della forza assiale interna
        self.load_val = load_val
    
    def check_stress(self):
        # limite di snervamento del materiale
        limit_mpa = material_table.loc[material_table["Material"] == self.material, "(MPa)"].values[0]
        
        # Converte il limite di sforzo (MPa) in limite di forza (kN)
        # 1 MPa = 10 N/cm²; 1 kN = 1000 N. Quindi: MPa * Area / 10 = kN
        limit_kn = limit_mpa * self.area / 10
        
        if abs(self.load_val) > limit_kn:
            return "fail"
        else:
            return "ok"

class corner:                                                            # Tipo de fuerza: C=Compresión (negativo), T=Tracción (positivo)
    def __init__(self, angle, has_vertical, has_horizontal, node):
        self.angle = angle
        self.has_vertical = has_vertical      
        self.has_horizontal = has_horizontal  
        self.node = node
        
        # Conta: 1 per appoggio mobile, 2 per appoggio fisso
        if self.has_horizontal:
            self.react_count = 2
        else:
            self.react_count = 1

class reaction:
    def __init__(self, angle, node):
        self.angle = angle  # Angolo della forza di reazione (gradi)
        self.node = node

class structure:
    def __init__(self, type, nodes, beams, corners):
        self.type = type
        self.nodes = nodes
        self.beams = beams
        self.corners = corners # Appoggi (vincoli)
    
    def check_static(self):
        # Verifica la condizione di determinazione statica per le travature reticolari (b + r = 2n)
        n_nodes = len(self.nodes)
        n_beams = len(self.beams)
        reactions = [c.react_count for c in self.corners]
        
        total_reacts = sum(reactions)
        if n_beams + total_reacts - 2 * n_nodes == 0:
            print("estable") # Isostatica
        else:
            print("inestable") # Iperstatica o labili
    
    def get_reactions(self):
        # Scompone gli appoggi (corners) in forze di reazione individuali (reactions)
        react_list = []
        for corner in self.corners:
            r1 = reaction(corner.angle, corner.node)
            react_list.append(r1)
            
            if corner.has_vertical and corner.has_horizontal:
                # Appoggio fisso 
                r2 = reaction(corner.angle + 90, corner.node)
                react_list.append(r2)
        return react_list

# Cargas
class load:
    def __init__(self, value, angle, pos):
        self.value = value  # Magnitudine (kN)
        self.angle = angle  # Angolo (gradi)
        self.pos = pos      # Nodo di applicazione

class calculation:
    def __init__(self, load, structure):
        self.load = load
        self.structure = structure
    
    def calc_reactions(self):
        # Calcolo delle 3 reazioni globali
        load_obj = self.load
        reactions = self.structure.get_reactions()
        
        if len(reactions) != 3:
            print("No resoluble") # Non isostatico
            return
        
        k = load_obj.value
        theta_k = load_obj.angle * (np.pi / 180) # Angolo del carico (radianti)
        node_k = load_obj.pos # Punto di applicazione del carico (riferimento per il momento)
        
        # Vettore dei carichi esterni [-Fx, -Fy, -Mz]
        col_k = np.array([-k * np.cos(theta_k), -k * np.sin(theta_k), 0])
        
        # Recupera dati per le 3 reazioni
        r1, r2, r3 = reactions[0], reactions[1], reactions[2]
        
        t1 = r1.angle * (np.pi / 180) # Angolo R1
        dx1 = r1.node.x - node_k.x     # Distanza orizzontale al punto di momento
        dy1 = r1.node.y - node_k.y     # Distanza verticale al punto di momento
        
        t2 = r2.angle * (np.pi / 180)
        dx2 = r2.node.x - node_k.x
        dy2 = r2.node.y - node_k.y 
        
        t3 = r3.angle * (np.pi / 180)
        dx3 = r3.node.x - node_k.x
        dy3 = r3.node.y - node_k.y
        
        # Matrice dei coefficienti del sistema (Somma Fx, Somma Fy, Somma Mz)
        mat = np.array([
            [np.cos(t1), np.cos(t2), np.cos(t3)],                                    
            [np.sin(t1), np.sin(t2), np.sin(t3)],                                  
            [np.cos(t1) * dy1 - dx1 * np.sin(t1),                                
             np.cos(t2) * dy2 - dx2 * np.sin(t2),
             np.cos(t3) * dy3 - dx3 * np.sin(t3)]
        ])
        
        # Risolve l'equazione Ax = b (sol contiene i valori delle 3 reazioni)
        sol = np.linalg.solve(mat, col_k)
        print(sol)
    
    def calc_forces(self):
        # Calcolo delle forze interne (b) e delle reazioni (r)
        n = len(self.structure.nodes)
        
        # La matrice è 2n x 2n (2 equazioni per nodo, 2n incognite tra forze interne e reazioni)
        node_mat = np.zeros((2 * n, 2 * n))
        
        # Riempie la matrice con i coefficienti delle travi e delle reazioni
        for i, node_i in enumerate(self.structure.nodes):
            # 1. Coefficienti delle travi (forze interne)
            for j, beam_j in enumerate(self.structure.beams):
                if node_i in beam_j.nodes:
                    sin_val, cos_val = node_i.get_angle(beam_j)
                    # coefficiente cos
                    node_mat[i * 2][j] = cos_val
                    # coefficiente sin
                    node_mat[i * 2 + 1][j] = sin_val
            
            # 2. Coefficienti delle reazioni (incognite aggiuntive)
            for k, react_k in enumerate(self.structure.get_reactions()):
                if node_i == react_k.node:
                    # Somma Fx = 0
                    node_mat[i * 2][k + len(self.structure.beams)] = np.cos(react_k.angle * np.pi / 180)
                    # Somma Fy = 0
                    node_mat[i * 2 + 1][k + len(self.structure.beams)] = np.sin(react_k.angle * np.pi / 180)
        
        # Vettore dei termini noti (carichi esterni negativi)
        vec_result = np.zeros(2 * n)
        for i, node_i in enumerate(self.structure.nodes):
            if node_i == self.load.pos:
                # Carichi esterni applicati (portati a destra dell'equazione con segno negativo)
                vec_result[i * 2] = -self.load.value * np.cos(self.load.angle * np.pi / 180)
                vec_result[i * 2 + 1] = -self.load.value * np.sin(self.load.angle * np.pi / 180)
        
        # Risolve il sistema lineare: [Forze Interne | Reazioni]
        solution = np.linalg.solve(node_mat, vec_result) #resuelve sistema de ecuaciones
        return solution

def check_safety(forces, limit):

    # Trova la forza massima assoluta (compressione o trazione)
    max_f = max(abs(f) for f in forces)
    
    # que tanto de la capacidad resistente estás usando
    ratio = (max_f / limit) * 100
    safe = max_f < limit
    
    return {
        "safe": safe,
        "max": round(max_f, 2),
        "ratio": round(ratio, 2),
        "msg": "Struttura Sicura" if safe else "Pericolo"
    }