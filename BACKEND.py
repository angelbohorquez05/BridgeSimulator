import CORE as pt

class bridge:  # clase padre per tutti tipi di ponte - fabricazione dei ponti
    def __init__(self):
        self.step_nodes = 0 #aun/min numro di nodi
        self.nodes_min = 0
        self.nodes = 0
        self.name = "Ni idea"
    
    def more_nodes(self): #aumentare il n di nodi
        self.nodes += self.step_nodes
    
    def less_nodes(self):#disminuire il n di nodi
        if self.nodes > self.nodes_min:
            self.nodes -= self.step_nodes
    
    def set_height(self, height):
        self.height = height
    
    def set_length(self, length):
        self.length = length
    
    def set_material(self, material):
        self.material = material
    
    def set_cross(self, cross): #sezione traversale
        self.cross = cross
    
    def create_struct(self):
        node_list = []
        bar_list = []
        #riempie le liste di nodi e barre dagli attributi della classe
        for i in range(len(self.nodes_dir)):
            node_list.append(self.nodes_dir["node" + str(i + 1)])
        
        for i in range(len(self.bars_dir)):
            bar_list.append(self.bars_dir["bar" + str(i + 1)])
        # corner1: appoggio a cerniera
        corner1 = pt.corner(90, 1, 1, self.nodes_dir["node1"])  # 2 reacciones
        # corner2: appoggio a carrello 
        corner2 = pt.corner(90, 1, 0, self.nodes_dir["node2"])  # 1 reacción
        corner_list = [corner1, corner2]
        #crea l'0ggetto struttura ocn i componenti definiti
        self.struct = pt.structure(self.name, node_list, bar_list, corner_list)
    
    def set_load(self, mod, angle, pos):  # fuerza de K = mod
        #il carico e applicato al nodo "pos"
        self.load = pt.load(mod, angle, self.nodes_dir["node" + str(pos)])
    
    def do_calc(self): #calcolo froze interne
        calc_var = pt.calculation(self.load, self.struct)
        return calc_var.calc_forces()

class pratt(bridge):
    def __init__(self):
        super().__init__()
        self.step_nodes = 4
        self.nodes_min = 8
        self.nodes = 8
        self.name = "Pratt"
    
    def build_nodes_bars(self): #logica per la costruzione in un Pratt
        base_line = int((self.nodes + 2) / 2)  # línea de abajo del puente
        x_dist = self.length / (base_line - 1) #distanza orizzontale tra i nodi della base
        y_dist = self.height
        
        nodes_dict = {} #nodi estremita
        nodes_dict["node1"] = pt.node([0, 0])
        nodes_dict["node2"] = pt.node([self.length, 0])
        
        for i in range(base_line - 2):
            nodes_dict["node" + str(i * 2 + 3)] = pt.node([x_dist * (i + 1), y_dist])
            nodes_dict["node" + str(i * 2 + 4)] = pt.node([x_dist * (i + 1), 0])
        
        self.nodes_dir = nodes_dict
        
        bars_dict = {} # costruzione delle barre
        bars_dict["bar1"] = pt.beam(self.material, nodes_dict["node1"], nodes_dict["node4"], self.cross)
        bars_dict["bar2"] = pt.beam(self.material, nodes_dict["node1"], nodes_dict["node3"], self.cross)
        bars_dict["bar3"] = pt.beam(self.material, nodes_dict["node2"], nodes_dict["node" + str(base_line * 2 - 3)], self.cross)
        bars_dict["bar4"] = pt.beam(self.material, nodes_dict["node2"], nodes_dict["node" + str(base_line * 2 - 2)], self.cross)
        #barre centrali
        for i in range(base_line - 3):
            bars_dict["bar" + str(i * 3 + 5)] = pt.beam(self.material, nodes_dict["node" + str(i * 2 + 3)], nodes_dict["node" + str(i * 2 + 5)], self.cross)
            bars_dict["bar" + str(i * 3 + 6)] = pt.beam(self.material, nodes_dict["node" + str(i * 2 + 4)], nodes_dict["node" + str(i * 2 + 6)], self.cross)
            bars_dict["bar" + str(i * 3 + 7)] = pt.beam(self.material, nodes_dict["node" + str(i * 2 + 3)], nodes_dict["node" + str(i * 2 + 4)], self.cross)
        
        bars_dict["bar" + str(base_line * 3 - 4)] = pt.beam(self.material, nodes_dict["node" + str(base_line * 2 - 3)], nodes_dict["node" + str(base_line * 2 - 2)], self.cross)
        
        bi = int(base_line * 3 - 3)
        #diagonali a sinistra
        n_diag = int((base_line - 3) / 2)
        
        for i in range(n_diag):
            #diagonali verso al centro
            bars_dict["bar" + str(bi + (i * 2))] = pt.beam(self.material, nodes_dict["node" + str((i * 2) + 3)],  nodes_dict["node" + str((i * 2) + 6)], self.cross)
            #diagonali simmetriche per la parte destra
            bars_dict["bar" + str(bi + 1 + (i * 2))] = pt.beam(self.material, nodes_dict["node" + str((base_line * 2) - 3 - (2 * i))], nodes_dict["node" + str((base_line * 2) - 4 - (2 * i))], self.cross)
        
        self.bars_dir = bars_dict

class warren(bridge):
    def __init__(self):
        super().__init__()
        self.step_nodes = 8
        self.nodes_min = 8
        self.nodes = 8
        self.name = "Warren"
    # Warren utilizza triangoli equilateri o isosceli (senza montanti verticali intermedi)
    def build_nodes_bars(self):
        base_line = int((self.nodes + 2) / 2)  # línea de abajo del puente
        x_dist = self.length / (base_line - 1)
        y_dist = self.height
        
        nodes_dict = {}
        nodes_dict["node1"] = pt.node([0, 0])
        nodes_dict["node2"] = pt.node([self.length, 0])
        
        for i in range(base_line - 2):
            nodes_dict["node" + str(i * 2 + 3)] = pt.node([x_dist * (i + 1), y_dist])
            nodes_dict["node" + str(i * 2 + 4)] = pt.node([x_dist * (i + 1), 0])
        
        self.nodes_dir = nodes_dict
        
        bars_dict = {}
        bars_dict["bar1"] = pt.beam(self.material, nodes_dict["node1"], nodes_dict["node4"], self.cross)
        bars_dict["bar2"] = pt.beam(self.material, nodes_dict["node1"], nodes_dict["node3"], self.cross)
        bars_dict["bar3"] = pt.beam(self.material, nodes_dict["node2"], nodes_dict["node" + str(base_line * 2 - 3)], self.cross)
        bars_dict["bar4"] = pt.beam(self.material, nodes_dict["node2"], nodes_dict["node" + str(base_line * 2 - 2)], self.cross)
        
        for i in range(base_line - 3):
            bars_dict["bar" + str(i * 3 + 5)] = pt.beam(self.material, nodes_dict["node" + str(i * 2 + 3)], nodes_dict["node" + str(i * 2 + 5)], self.cross)
            bars_dict["bar" + str(i * 3 + 6)] = pt.beam(self.material, nodes_dict["node" + str(i * 2 + 4)], nodes_dict["node" + str(i * 2 + 6)], self.cross)
            bars_dict["bar" + str(i * 3 + 7)] = pt.beam(self.material, nodes_dict["node" + str(i * 2 + 3)], nodes_dict["node" + str(i * 2 + 4)], self.cross)
        
        bars_dict["bar" + str(base_line * 3 - 4)] = pt.beam(self.material, nodes_dict["node" + str(base_line * 2 - 3)], nodes_dict["node" + str(base_line * 2 - 2)], self.cross)
        
        bi = int(base_line * 3 - 3)
        n_diag = int((base_line - 3) / 2)
        # Barre diagonali: L'implementazione qui sembra utilizzare diagonali molto diverse da Pratt, ma la logica di calcolo dei nodi è la stessa.
        # ATTENZIONE: La logica del Warren qui non sembra costruire una capriata Warren *standard* # che dovrebbe avere una griglia di triangoli equilateri senza montanti verticali interni.
        # Controllare la logica delle diagonali
        for i in range(n_diag):
            bars_dict["bar" + str(bi + (i * 2))] = pt.beam(self.material, nodes_dict["node" + str((i * 4) + 3)], nodes_dict["node" + str((i * 4) + 6)], self.cross)
            bars_dict["bar" + str(bi + 1 + (i * 2))] = pt.beam(self.material, nodes_dict["node" + str((base_line * 2) - 3 - (4 * i))], nodes_dict["node" + str((base_line * 2) - 4 - (4 * i))], self.cross)
        
        self.bars_dir = bars_dict

class k_type(bridge):
    def __init__(self):
        super().__init__()
        self.step_nodes = 6
        self.nodes_min = 14
        self.nodes = 14
        self.name = "K"
    
    def build_nodes_bars(self):
        # La capriata a K aggiunge nodi intermedi a metà altezza
        base_line = int((self.nodes + 7) / 3) # Numero di sezioni (base - 3)
        x_dist = self.length / (base_line - 3)# Distanza orizzontale tra le sezioni principali
        y_dist = self.height
        
        nodes_dict = {}
        # Nodi di estremità:
        nodes_dict["node1"] = pt.node([0, 0]) #basso sinistra
        nodes_dict["node2"] = pt.node([self.length, 0]) #basso destra
        nodes_dict["node3"] = pt.node([x_dist / 2, y_dist / 2]) #meta siinistra (diagonale d'inizio)
        nodes_dict["node4"] = pt.node([self.length - (x_dist / 2), y_dist / 2]) #Metà Destra (diagonale di fine)
        nodes_dict["node5"] = pt.node([x_dist / 2, 0]) #basso intemredio sisnistra
        nodes_dict["node6"] = pt.node([self.length - (x_dist / 2), 0]) #basso intermedio destra
        
        counter = 7 
        # Ciclo per creare i nodi interni di ciascun pannello/sezione
        for i in range(base_line - 4):
            # 1. Nodo Superiore (all'altezza y_dist)
            nodes_dict["node" + str(counter)] = pt.node([x_dist * (i + 1), y_dist])
            counter += 1
            # 2. Nodo Intermedio (solo se non siamo al centro del ponte)
            # La condizione assicura che il nodo centrale a metà altezza non venga creato due volte 
            # se la lunghezza del ponte è pari, oppure non venga creato affatto se non c'è una mezzeria esatta.
            if (x_dist * (i + 1)) != (self.length / 2):
                nodes_dict["node" + str(counter)] = pt.node([x_dist * (i + 1), y_dist / 2])
                counter += 1
            # 3. Nodo Inferiore (all'altezza 0)
            nodes_dict["node" + str(counter)] = pt.node([x_dist * (i + 1), 0])
            counter += 1 #counter = counter + 1
        
        counter -= 1 #ora tiene il n totale di nodi creati
        self.nodes_dir = nodes_dict
        
        bars_dict = {}
        bars_dict["bar1"] = pt.beam(self.material, nodes_dict["node1"], nodes_dict["node3"], self.cross)
        bars_dict["bar2"] = pt.beam(self.material, nodes_dict["node1"], nodes_dict["node5"], self.cross)
        bars_dict["bar3"] = pt.beam(self.material, nodes_dict["node3"], nodes_dict["node5"], self.cross)
        bars_dict["bar4"] = pt.beam(self.material, nodes_dict["node3"], nodes_dict["node7"], self.cross)
        bars_dict["bar5"] = pt.beam(self.material, nodes_dict["node3"], nodes_dict["node9"], self.cross)
        bars_dict["bar6"] = pt.beam(self.material, nodes_dict["node5"], nodes_dict["node9"], self.cross)
        bars_dict["bar7"] = pt.beam(self.material, nodes_dict["node2"], nodes_dict["node4"], self.cross)
        bars_dict["bar8"] = pt.beam(self.material, nodes_dict["node2"], nodes_dict["node6"], self.cross)
        bars_dict["bar9"] = pt.beam(self.material, nodes_dict["node4"], nodes_dict["node6"], self.cross)
        bars_dict["bar10"] = pt.beam(self.material, nodes_dict["node4"], nodes_dict["node" + str(counter - 2)], self.cross)
        bars_dict["bar11"] = pt.beam(self.material, nodes_dict["node4"], nodes_dict["node" + str(counter)], self.cross)
        bars_dict["bar12"] = pt.beam(self.material, nodes_dict["node6"], nodes_dict["node" + str(counter)], self.cross)
        
        half = int((base_line - 5) / 2)  # half = 1
        
        for i in range(half):
            bars_dict["bar" + str(i * 6 + 13)] = pt.beam(self.material, nodes_dict["node" + str(i * 3 + 7)], nodes_dict["node" + str(i * 3 + 10)], self.cross)
            bars_dict["bar" + str(i * 6 + 14)] = pt.beam(self.material, nodes_dict["node" + str(i * 3 + 7)], nodes_dict["node" + str(i * 3 + 8)], self.cross)
            bars_dict["bar" + str(i * 6 + 15)] = pt.beam(self.material, nodes_dict["node" + str(i * 3 + 8)], nodes_dict["node" + str(i * 3 + 9)], self.cross)
            
            if i == (half - 1):
                bars_dict["bar" + str(i * 6 + 16)] = pt.beam(self.material, nodes_dict["node" + str(i * 3 + 9)], nodes_dict["node" + str(i * 3 + 11)], self.cross)
            else:
                bars_dict["bar" + str(i * 6 + 16)] = pt.beam(self.material, nodes_dict["node" + str(i * 3 + 9)], nodes_dict["node" + str(i * 3 + 12)], self.cross)
            bars_dict["bar" + str(i * 6 + 17)] = pt.beam(self.material, nodes_dict["node" + str(i * 3 + 8)], nodes_dict["node" + str(i * 3 + 10)], self.cross)
            
            if i == (half - 1):
                bars_dict["bar" + str(i * 6 + 18)] = pt.beam(self.material, nodes_dict["node" + str(i * 3 + 8)], nodes_dict["node" + str(i * 3 + 11)], self.cross)
            else:
                bars_dict["bar" + str(i * 6 + 18)] = pt.beam(self.material, nodes_dict["node" + str(i * 3 + 8)], nodes_dict["node" + str(i * 3 + 12)], self.cross)
        
        middle = 13 + (half * 6)  # middle 19
        top = (half * 3) + 7  # top = 10
        bottom = (half * 3) + 8
        
        bars_dict["bar" + str(middle)] = pt.beam(self.material, nodes_dict["node" + str(top)], nodes_dict["node" + str(bottom)], self.cross)
        
        middle += 1  # middle 20
        
        for i in range(half):
            if i == 0:
                bars_dict["bar" + str(i * 6 + middle)] = pt.beam(self.material, nodes_dict["node" + str((i * 3) + top + 2)], nodes_dict["node" + str((i * 3) + top)], self.cross)
            else:
                bars_dict["bar" + str(i * 6 + middle)] = pt.beam(self.material, nodes_dict["node" + str((i * 3) + top + 2)], nodes_dict["node" + str((i * 3) + top - 1)], self.cross)
            
            bars_dict["bar" + str(i * 6 + middle + 1)] = pt.beam(self.material, nodes_dict["node" + str((i * 3) + top + 2)], nodes_dict["node" + str((i * 3) + top + 3)], self.cross)
            bars_dict["bar" + str(i * 6 + middle + 2)] = pt.beam(self.material, nodes_dict["node" + str((i * 3) + top + 3)], nodes_dict["node" + str((i * 3) + top + 4)], self.cross)
            bars_dict["bar" + str(i * 6 + middle + 3)] = pt.beam(self.material, nodes_dict["node" + str((i * 3) + top + 4)], nodes_dict["node" + str((i * 3) + top + 1)], self.cross)
            bars_dict["bar" + str(i * 6 + middle + 4)] = pt.beam(self.material, nodes_dict["node" + str((i * 3) + top + 3)], nodes_dict["node" + str((i * 3) + top + 1)], self.cross)
            
            if i == 0:
                bars_dict["bar" + str(i * 6 + middle + 5)] = pt.beam(self.material, nodes_dict["node" + str((i * 3) + top + 3)], nodes_dict["node" + str((i * 3) + top)], self.cross)
            else:
                bars_dict["bar" + str(i * 6 + middle + 5)] = pt.beam(self.material, nodes_dict["node" + str((i * 3) + top + 3)], nodes_dict["node" + str((i * 3) + top - 1)], self.cross)
        # los 3 cuadros de colores
        self.bars_dir = bars_dict


