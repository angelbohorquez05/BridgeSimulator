import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import turtle
import os
import sys #interprete de Python y el entorno de ejecución
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    import BACKEND as bob
    import CORE as pt
    BACKEND_OK = True
except ImportError:
    BACKEND_OK = False

class BridgeSimulator:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("MINOU - Simulatore Ponti")
        self.root.geometry("1400x900")
        self.root.minsize(1200, 800)
        self.icon_path = "PUENTE/catt.ico"
        self.root.iconbitmap(self.icon_path)
        self.current_bridge = None
        self.current_forces = []
        
        # Variables de Paneo 
        self.pan_offset = [0, 0]        
        self.last_mouse_pos = (0, 0)    
        
        self.root.bind('<Configure>', self.on_window_resize)
        
        self.setup_theme()
        self.create_layout()
        self.create_components()
        
    # MÉTODOS DE CONFIGURACIÓN DE UI/LAYOUT
    
    def setup_theme(self):
        self.colors = {
            'bg_primary': '#0a0a0f', 'bg_secondary': '#1a1a2a', 'bg_card': '#252538',
            'accent_primary': '#3a86ff', 'accent_secondary': '#8338ec',
            'text_primary': '#f8f9fa', 'text_secondary': '#adb5bd',
            'success': '#38b000', 'warning': '#ff9e00', 'danger': '#ef233c',
            'border': '#495057'
        }
        self.root.configure(bg=self.colors['bg_primary'])
        
    def create_layout(self):
        # Estructura principal: panel izquierdo (controles) y panel derecho (viz/resultados)
        self.left_panel = tk.Frame(self.root, bg=self.colors['bg_secondary'], width=400)
        self.left_panel.pack(side='left', fill='both', padx=20, pady=20)
        self.left_panel.pack_propagate(False)
        
        self.right_panel = tk.Frame(self.root, bg=self.colors['bg_primary'])
        self.right_panel.pack(side='right', fill='both', expand=True, padx=(0, 20), pady=20)
        
        # División vertical del panel derecho: 70% visualización, 30% resultados
        self.right_panel.grid_rowconfigure(0, weight=70)
        self.right_panel.grid_rowconfigure(1, weight=30)
        self.right_panel.grid_columnconfigure(0, weight=1)
        
        self.viz_frame = tk.Frame(self.right_panel, bg=self.colors['bg_primary'])
        self.viz_frame.grid(row=0, column=0, sticky='nsew', pady=(0, 10))
        
        self.results_frame = tk.Frame(self.right_panel, bg=self.colors['bg_primary'])
        self.results_frame.grid(row=1, column=0, sticky='nsew')
        
    def create_components(self):
        # Inicializa todos los grupos de control y visualización
        self.create_header()
        self.create_bridge_controls()
        self.create_load_controls()
        self.create_action_buttons()
        self.create_visualization()
        self.create_results_tabs()
        
    def create_header(self):
        header = tk.Frame(self.left_panel, bg=self.colors['bg_secondary'], height=100)
        header.pack(fill='x', pady=(0, 20))
        header.pack_propagate(False)
        
        title_frame = tk.Frame(header, bg=self.colors['bg_secondary'])
        title_frame.pack(side='left', fill='y')
        
        tk.Label(title_frame, text='Valutazione Strutturale', 
                 font=('Segoe UI', 20, 'bold'),
                 bg=self.colors['bg_secondary'], 
                 fg=self.colors['text_primary']).pack(anchor='w')
        tk.Label(title_frame, text='dei Ponti a Travatura', 
                 font=('Segoe UI', 20, 'bold'),
                 bg=self.colors['bg_secondary'], 
                 fg=self.colors['text_primary']).pack(anchor='w')
        
    def create_card(self, parent, title):
        card = tk.Frame(parent, bg=self.colors['bg_card'], highlightbackground=self.colors['border'], highlightthickness=1)
        card.pack(fill='x', pady=(0, 15))
        tk.Label(card, text=title, font=('Segoe UI', 13, 'bold'), bg=self.colors['bg_card'], 
                 fg=self.colors['text_primary']).pack(fill='x', padx=20, pady=15)
        tk.Frame(card, height=1, bg=self.colors['border']).pack(fill='x', padx=20, pady=(0, 15))
        content = tk.Frame(card, bg=self.colors['bg_card'])
        content.pack(fill='both', expand=True, padx=20, pady=(0, 20))
        return content

    def create_bridge_controls(self):
        # Controles para definir la geometría y material del puente
        bridge_card = self.create_card(self.left_panel, "CONFIGURAZIONE PONTE")
        
        for i in range(6):
            bridge_card.grid_rowconfigure(i, minsize=50)
        bridge_card.grid_columnconfigure(1, weight=1)
        
        # Tipo de puente 
        tk.Label(bridge_card, text="Tipo ponte:", font=('Segoe UI', 15),
                 bg=self.colors['bg_card'], fg=self.colors['text_secondary']).grid(row=0, column=0, sticky='w', padx=15, pady=5)
        self.bridge_type = tk.StringVar(value="Pratt")
        type_combo = ttk.Combobox(bridge_card, textvariable=self.bridge_type,
                                  values=["Pratt", "Warren", "K-truss"], state="readonly", font=('Segoe UI', 10))
        type_combo.grid(row=0, column=1, sticky='ew', padx=(0, 15), pady=5)
        type_combo.bind('<<ComboboxSelected>>', self.on_bridge_type_change)
        
        # Nodos 
        tk.Label(bridge_card, text="Nodi:", font=('Segoe UI', 15),
                 bg=self.colors['bg_card'], fg=self.colors['text_secondary']).grid(row=1, column=0, sticky='w', padx=15, pady=5)
        nodes_frame = tk.Frame(bridge_card, bg=self.colors['bg_card'])
        nodes_frame.grid(row=1, column=1, sticky='w', padx=(0, 15), pady=5)
        self.nodes_var = tk.IntVar(value=8)
        tk.Button(nodes_frame, text='−', font=('Segoe UI', 10), width=3, bg=self.colors['accent_primary'], fg='white', relief='flat',
                  command=self.decrease_nodes).pack(side='left')
        tk.Label(nodes_frame, textvariable=self.nodes_var, font=('Segoe UI', 11),
                 bg=self.colors['bg_card'], fg=self.colors['text_primary'], width=6).pack(side='left', padx=10)
        tk.Button(nodes_frame, text='+', font=('Segoe UI', 10), width=3, bg=self.colors['accent_primary'], fg='white', relief='flat',
                  command=self.increase_nodes).pack(side='left')
        
        # Longitud, Altura, Material y Área de la sección
        tk.Label(bridge_card, text="Lunghezza (m):", font=('Segoe UI', 15),
                 bg=self.colors['bg_card'], fg=self.colors['text_secondary']).grid(row=2, column=0, sticky='w', padx=15, pady=5)
        self.length_var = tk.StringVar(value=" ")
        tk.Entry(bridge_card, textvariable=self.length_var, font=('Segoe UI', 10),
                 bg='#2d3748', fg='white', insertbackground='white', relief='flat').grid(row=2, column=1, sticky='ew', padx=(0, 15), pady=5, ipady=5)
        
        tk.Label(bridge_card, text="Altezza (m):", font=('Segoe UI', 15),
                 bg=self.colors['bg_card'], fg=self.colors['text_secondary']).grid(row=3, column=0, sticky='w', padx=15, pady=5)
        self.height_var = tk.StringVar(value=" ")
        tk.Entry(bridge_card, textvariable=self.height_var, font=('Segoe UI', 10),
                 bg='#2d3748', fg='white', insertbackground='white', relief='flat').grid(row=3, column=1, sticky='ew', padx=(0, 15), pady=5, ipady=5)
        
        tk.Label(bridge_card, text="Materiale:", font=('Segoe UI', 15),
                 bg=self.colors['bg_card'], fg=self.colors['text_secondary']).grid(row=4, column=0, sticky='w', padx=15, pady=5)
        self.material_var = tk.StringVar(value="A36")
        material_combo = ttk.Combobox(bridge_card, textvariable=self.material_var,
                                      values=["A36", "S275", "S355", "A572", "A588", "S460"], state="readonly", font=('Segoe UI', 10))
        material_combo.grid(row=4, column=1, sticky='ew', padx=(0, 15), pady=5)
        
        tk.Label(bridge_card, text="Area (cm²):", font=('Segoe UI', 15),
                 bg=self.colors['bg_card'], fg=self.colors['text_secondary']).grid(row=5, column=0, sticky='w', padx=15, pady=5)
        self.area_var = tk.StringVar(value="")
        tk.Entry(bridge_card, textvariable=self.area_var, font=('Segoe UI', 10),
                 bg='#2d3748', fg='white', insertbackground='white', relief='flat').grid(row=5, column=1, sticky='ew', padx=(0, 15), pady=5, ipady=5)
    
    def create_load_controls(self):
        # Controles para especificar el punto y magnitud del carho
        load_card = self.create_card(self.left_panel, "ANALISI CARICHI")
        
        for i in range(4):
            load_card.grid_rowconfigure(i, minsize=55)
        load_card.grid_columnconfigure(1, weight=1)
        
        tk.Label(load_card, text="Nodo destinazione:", font=('Segoe UI', 15),
                 bg=self.colors['bg_card'], fg=self.colors['text_primary']).grid(row=0, column=0, sticky='w', padx=15, pady=8)
        self.node_var = tk.StringVar()
        self.node_combo = ttk.Combobox(load_card, textvariable=self.node_var, state="readonly", font=('Segoe UI', 11))
        self.node_combo.grid(row=0, column=1, sticky='ew', padx=(0, 15), pady=8)
        
        tk.Label(load_card, text="Carico (kN):", font=('Segoe UI', 15),
                 bg=self.colors['bg_card'], fg=self.colors['text_primary']).grid(row=1, column=0, sticky='w', padx=15, pady=8)
        self.load_var = tk.StringVar(value="")
        tk.Entry(load_card, textvariable=self.load_var, font=('Segoe UI', 11),
                 bg='#2d3748', fg='white', insertbackground='white', relief='flat').grid(row=1, column=1, sticky='ew', padx=(0, 15), pady=8, ipady=6)
        
        tk.Label(load_card, text="Angolo (°):", font=('Segoe UI', 15),
                 bg=self.colors['bg_card'], fg=self.colors['text_primary']).grid(row=2, column=0, sticky='w', padx=15, pady=8)
        self.angle_var = tk.StringVar(value="")
        tk.Entry(load_card, textvariable=self.angle_var, font=('Segoe UI', 11),
                 bg='#2d3748', fg='white', insertbackground='white', relief='flat').grid(row=2, column=1, sticky='ew', padx=(0, 15), pady=8, ipady=6)
    
    def create_action_buttons(self):
        # Botones Generar y Analizar
        btn_card = tk.Frame(self.left_panel, bg=self.colors['bg_secondary'])
        btn_card.pack(fill='x', pady=(20, 0))
        
        self.generate_btn = tk.Button(btn_card, text='GENERA PONTE', font=('Segoe UI', 18, 'bold'),
                                      bg=self.colors['accent_primary'], fg='white', relief='flat',
                                      padx=30, pady=14, cursor='hand2', command=self.generate_bridge)
        self.generate_btn.pack(fill='x', pady=(0, 10))
        
        self.analyze_btn = tk.Button(btn_card, text='ANALIZZA CARICHI', font=('Segoe UI', 18, 'bold'),
                                     bg=self.colors['accent_secondary'], fg='white', relief='flat',
                                     padx=30, pady=14, cursor='hand2', command=self.analyze_loads)
        self.analyze_btn.pack(fill='x')
    
    def create_visualization(self):
        # Configuración del lienzo de Turtle para la visualización del puente
        title_frame = tk.Frame(self.viz_frame, bg=self.colors['bg_primary'])
        title_frame.pack(fill='x', pady=(0, 10))
        tk.Label(title_frame, text='VISUALIZZAZIONE PONTE', font=('Segoe UI', 14, 'bold'),
                 bg=self.colors['bg_primary'], fg=self.colors['text_primary']).pack(side='left')
        
        canvas_container = tk.Frame(self.viz_frame, bg=self.colors['bg_primary'])
        canvas_container.pack(fill='both', expand=True)
        
        self.viz_canvas = tk.Canvas(canvas_container, bg=self.colors['bg_secondary'], 
                                   highlightbackground=self.colors['border'], 
                                   highlightthickness=2)
        self.viz_canvas.pack(fill='both', expand=True, padx=20, pady=10)
        self.viz_canvas.bind('<Button-1>', self.start_pan)   
        self.viz_canvas.bind('<B1-Motion>', self.do_pan)     
        self.screen = turtle.TurtleScreen(self.viz_canvas)
        self.turtle_pen = turtle.RawTurtle(self.screen)
        self.turtle_pen.hideturtle()
        self.screen.tracer(0)
        self.viz_canvas.bind('<Configure>', lambda e: self.on_canvas_resize())
    
    def create_results_tabs(self):
        style = ttk.Style()
        style.theme_use('clam')
        # Estilos del Notebook/Tabs
        style.configure('Custom.TNotebook', background=self.colors['bg_primary'], borderwidth=0)
        style.configure('Custom.TNotebook.Tab', background=self.colors['bg_card'], 
                        foreground=self.colors['text_primary'], padding=[15, 5], 
                        font=('Segoe UI', 10, 'bold'), borderwidth=1, relief='flat')
        style.map('Custom.TNotebook.Tab', background=[('selected', self.colors['accent_primary'])],
                  foreground=[('selected', 'white')])
        
        self.notebook = ttk.Notebook(self.results_frame, style='Custom.TNotebook')
        self.notebook.pack(fill='both', expand=True)
        self.results_tab = tk.Frame(self.notebook, bg=self.colors['bg_secondary'])
        self.notebook.add(self.results_tab, text='Risultati')
        
        # Estilos del Treeview (Tabla)
        style.configure('Treeview', background=self.colors['bg_secondary'], foreground=self.colors['text_primary'],
                        fieldbackground=self.colors['bg_secondary'], font=('Segoe UI', 10), rowheight=25, borderwidth=0)
        style.configure('Treeview.Heading', background=self.colors['bg_card'], foreground=self.colors['text_primary'],
                        font=('Segoe UI', 10, 'bold'), borderwidth=1, relief='flat')
        
        columns = ('Barra', 'Forza (kN)', 'Tensione', 'Stato')
        self.results_tree = ttk.Treeview(self.results_tab, columns=columns, show='headings') 
        for col in columns:
            self.results_tree.heading(col, text=col)
            self.results_tree.column(col, anchor='center')
        scrollbar = ttk.Scrollbar(self.results_tab, orient='vertical', command=self.results_tree.yview)
        self.results_tree.configure(yscrollcommand=scrollbar.set)
        
        # Usar Grid para expansión total (nsew) del Treeview dentro de su pestaña
        self.results_tab.grid_columnconfigure(0, weight=1)
        self.results_tab.grid_rowconfigure(0, weight=1)
        
        self.results_tree.grid(row=0, column=0, sticky='nsew', padx=10, pady=10)
        scrollbar.grid(row=0, column=1, sticky='ns', pady=10)
        
        # Tab de gráfico
        self.graph_tab = tk.Frame(self.notebook, bg=self.colors['bg_primary'])
        self.notebook.add(self.graph_tab, text='Grafico')
        self.graph_frame = tk.Frame(self.graph_tab, bg=self.colors['bg_primary'])
        self.graph_frame.pack(fill='both', expand=True, padx=10, pady=10)
        self.create_empty_chart()
    
    def create_empty_chart(self):
        fig, ax = plt.subplots(figsize=(6, 4), facecolor='#0a0a0f')
        ax.set_facecolor('#0a0a0f')
        ax.text(0.5, 0.5, 'Esegui analisi per visualizzare distribuzione', ha='center', va='center',
                transform=ax.transAxes, color='#adb5bd', fontsize=12)
        ax.set_xticks([])
        ax.set_yticks([])
        for spine in ax.spines.values():
            spine.set_visible(False)
        
        self.chart_canvas = FigureCanvasTkAgg(fig, self.graph_frame)
        self.chart_canvas.draw()
        self.chart_canvas.get_tk_widget().pack(fill='both', expand=True)

    # MÉTODOS DE MANEJO DE EVENTOS
        
    def on_window_resize(self, event):
        # Redibuja el puente al cambiar el tamaño de la ventana
        if self.current_bridge and event.widget == self.root:
            self.root.after(50, self.force_redraw)
    
    def on_canvas_resize(self):
        # Redibuja el puente al cambiar el tamaño del lienzo
        if self.current_bridge:
            self.draw_bridge()
    
    def force_redraw(self):
        # Fuerza un redibujo del puente
        if self.current_bridge:
            self.viz_canvas.update_idletasks()
            self.draw_bridge()
    
    def on_bridge_type_change(self, event=None):
        # Ajusta el número mínimo de nodos al cambiar el tipo de puente
        self.nodes_var.set(14 if self.bridge_type.get() == "K-truss" else 8)
    
    def increase_nodes(self):
        step = 6 if self.bridge_type.get() == "K-truss" else 4
        self.nodes_var.set(self.nodes_var.get() + step)
    
    def decrease_nodes(self):
        step = 6 if self.bridge_type.get() == "K-truss" else 4
        current = self.nodes_var.get()
        if current - step >= 8:
            self.nodes_var.set(current - step)
    
    # MÉTODOS DE DIBUJO Y PANEO
    
    def start_pan(self, event):
        # Inicia el registro de posición para el paneo
        self.last_mouse_pos = (event.x, event.y)

    def do_pan(self, event):
        # Aplica el desplazamiento al offset de paneo y redibuja
        if not self.current_bridge: return
        dx = event.x - self.last_mouse_pos[0]
        dy = event.y - self.last_mouse_pos[1]
        self.pan_offset[0] += dx
        self.pan_offset[1] += dy
        self.last_mouse_pos = (event.x, event.y)
        self.draw_bridge()
        
    def draw_bridge(self):
        self.turtle_pen.clear()
        if not self.current_bridge or not hasattr(self.current_bridge, 'bars_dir'):
            self.screen.update()
            return
        
        self.viz_canvas.update_idletasks()
        canvas_width = self.viz_canvas.winfo_width()
        canvas_height = self.viz_canvas.winfo_height()
        if canvas_width <= 10 or canvas_height <= 10: return

        # 1. Calcular Bounding Box y Escala
        nodes_x = [node.x for node in self.current_bridge.nodes_dir.values()]
        nodes_y = [node.y for node in self.current_bridge.nodes_dir.values()]
        if not nodes_x or not nodes_y: return
        max_x, min_x = max(nodes_x), min(nodes_x)
        max_y, min_y = max(nodes_y), min(nodes_y) 
        
        bridge_width = max_x - min_x
        bridge_height = max_y - min_y
        if bridge_width <= 0: bridge_width = 1
        if bridge_height <= 0: bridge_height = 1

        margin_factor = 0.8 
        scale_x = (canvas_width * margin_factor) / bridge_width
        scale_y = (canvas_height * margin_factor) / bridge_height
        scale = min(scale_x, scale_y)
        
        # 2. Calcular Offset = diferenza di posizione
        center_x_model = (min_x + max_x) / 2
        offset_x_centering = (canvas_width / 2) - center_x_model * scale
        y_bottom_target = -canvas_height / 2 + 50 
        offset_y_centering = y_bottom_target - (min_y * scale)
        
        offset_x = offset_x_centering + self.pan_offset[0]
        offset_y = offset_y_centering + self.pan_offset[1]
        
        self.turtle_pen.speed(0)
        self.turtle_pen.width(3)
        
        # 3. Coloración y Dibujo de Barras
        real_bar_count = len(self.current_bridge.bars_dir)
        max_force = max(abs(f) for f in self.current_forces[:real_bar_count]) if self.current_forces and real_bar_count > 0 else 1

        bar_index = 0
        for bar_name, bar in self.current_bridge.bars_dir.items():
            if bar_index < len(self.current_forces):
                stress_ratio = abs(self.current_forces[bar_index]) / max_force if max_force > 0 else 0
                self.turtle_pen.color(self.stress_to_color(stress_ratio))
            else:
                self.turtle_pen.color('#3a86ff')
            
            try:
                node1, node2 = bar.nodes
                #Traslación
                x1 = node1.x * scale + offset_x
                y1 = node1.y * scale + offset_y 
                x2 = node2.x * scale + offset_x
                y2 = node2.y * scale + offset_y
                
                self.turtle_pen.penup()
                self.turtle_pen.goto(x1, y1)
                self.turtle_pen.pendown()
                self.turtle_pen.goto(x2, y2)
            except:
                pass
            bar_index += 1
        
        # 4. Dibujo de Nodos
        if hasattr(self.current_bridge, 'nodes_dir'):
            self.turtle_pen.penup()
            self.turtle_pen.color('#f8f9fa')
            for node_name, node in self.current_bridge.nodes_dir.items():
                try:
                    x = node.x * scale + offset_x
                    y = node.y * scale + offset_y
                    self.turtle_pen.goto(x, y)
                    self.turtle_pen.dot(10)
                except:
                    pass
        
        self.screen.update()
    
    def stress_to_color(self, ratio):
        # Mapea la relación de tensión a un color (verde=bajo, rojo=alto)
        ratio = max(0, min(1, ratio))
        if ratio < 0.3:
            return '#38b000' # Success
        elif ratio < 0.7:
            return '#ff9e00' # Warning
        else:
            return '#ef233c' # Danger
    
    # MÉTODOS DE LÓGICA DE NEGOCIO Y CÁLCULO 
    
    def generate_bridge(self):
        if not BACKEND_OK:
            messagebox.showerror('Errore', 'Backend non disponibile')
            return
        
        # Validación de campos
        for var, name in [(self.length_var, "Lunghezza"), (self.height_var, "Altezza"), (self.area_var, "Area sezione")]:
            if not var.get().strip():
                messagebox.showerror('Errore', f'Inserire {name}')
                return
        
        try:
            self.generate_btn.config(state='disabled', text='GENERAZIONE...')
            self.root.update()
            
            # Creación y configuración del modelo de puente usando el backend
            bridge_type = self.bridge_type.get()
            if bridge_type == "Pratt":
                self.current_bridge = bob.pratt()
            elif bridge_type == "Warren":
                self.current_bridge = bob.warren()
            else:
                self.current_bridge = bob.k_type()
            
            self.current_bridge.nodes = self.nodes_var.get()
            self.current_bridge.set_length(float(self.length_var.get()))
            self.current_bridge.set_height(float(self.height_var.get()))
            self.current_bridge.set_material(self.material_var.get())
            self.current_bridge.set_cross(float(self.area_var.get()))
            
            self.current_bridge.build_nodes_bars()
            self.current_bridge.create_struct()
            
            self.current_forces = []
            self.clear_results()
            self.update_node_list()
            
            # Resetear paneo y dibujar el nuevo puente
            self.pan_offset = [0, 0]
            self.viz_canvas.update_idletasks()
            self.draw_bridge()
            
        except Exception as e:
            messagebox.showerror('Errore', f'Errore nella generazione:\n{str(e)}')
        finally:
            self.generate_btn.config(state='normal', text='GENERA PONTE')
    
    def update_node_list(self):
        # Actualiza el Combobox de selección de nodo para la aplicación de carga
        self.node_combo.set('')
        if self.current_bridge and hasattr(self.current_bridge, 'nodes_dir'):
            nodes = list(self.current_bridge.nodes_dir.keys())
            try:
                # Ordenamiento numérico de los nodos
                nodes.sort(key=lambda x: int(x.replace('node', '')))
            except:
                pass
            self.node_combo['values'] = nodes
            if nodes:
                self.node_combo.current(0)
    
    def analyze_loads(self):
        if not self.current_bridge:
            messagebox.showwarning('Attenzione', 'Genera un ponte prima')
            return
        
        # Validación de campos de carga
        if not self.node_var.get():
            messagebox.showwarning('Attenzione', 'Seleziona un nodo')
            return
        
        for var, name in [(self.load_var, "Carico"), (self.angle_var, "Angolo")]:
            if not var.get().strip():
                messagebox.showerror('Errore', f'Inserire {name}')
                return
        
        try:
            self.analyze_btn.config(state='disabled', text='ANALISI...')
            self.root.update()
            
            # Preparar y ejecutar el cálculo estructural
            node_num = int(self.node_var.get().replace('node', ''))
            load_val = float(self.load_var.get())
            angle_val = float(self.angle_var.get())
            area_val = float(self.area_var.get()) if self.area_var.get() else 5.0
            
            self.current_bridge.set_load(load_val, angle_val, node_num)
            forces = self.current_bridge.do_calc() # Llamada al backend
            
            self.current_forces = forces.tolist() if hasattr(forces, 'tolist') else list(forces)
            
            self.check_bridge_viability(area_val)
            self.update_results_table(area_val)
            self.update_stress_chart(area_val)
            self.draw_bridge() # Redibuja con la nueva coloración de fuerzas
            
        except Exception as e:
            messagebox.showerror('Errore', f'Errore nell\'analisi:\n{str(e)}')
        finally:
            self.analyze_btn.config(state='normal', text='ANALIZZA CARICHI')
    
    def check_bridge_viability(self, area=5.0):
        # Muestra un resumen de la viabilidad del puente 
        if not self.current_forces:
            return
        
        real_bar_count = len(self.current_bridge.bars_dir) if hasattr(self.current_bridge, 'bars_dir') else len(self.current_forces)
        safe_bars = 0
        warning_bars = 0
        danger_bars = 0
        
        # Clasificación simplificada basada en tensión (valores de umbral fijos kN/cm²)
        yield_safe = 15 
        yield_warning = 25 
        
        for i in range(min(real_bar_count, len(self.current_forces))):
            try:
                stress_val = abs(float(self.current_forces[i])) / area if area > 0 else 0
                
                if stress_val < yield_safe:
                    safe_bars += 1
                elif stress_val < yield_warning:
                    warning_bars += 1
                else:
                    danger_bars += 1
            except:
                pass
        
        # Creación de la ventana de resultados
        result_win = tk.Toplevel(self.root)
        result_win.title("Risultato Analisi")
        result_win.geometry("450x350")
        result_win.configure(bg='#1a1a2a')
        result_win.resizable(False, False)
        result_win.transient(self.root)
        try:
            # Aplicar el ícono a la ventana de resultados
            result_win.iconbitmap(self.icon_path)
        except:
            pass
        
        # Determinar resultado final
        if danger_bars == 0 and warning_bars == 0:
            result_text = "PONTE VIABILE"
            color = self.colors['success']
        elif danger_bars == 0:
            result_text = "PONTE ACCETTABILE"
            color = self.colors['warning']
        else:
            result_text = "PONTE NON VIABILE"
            color = self.colors['danger']
        
        title_frame = tk.Frame(result_win, bg=color, height=5)
        title_frame.pack(fill='x', pady=(0, 10))
        
        tk.Label(result_win, text="ANALISI COMPLETATA", font=('Segoe UI', 18, 'bold'),
                 bg='#1a1a2a', fg='#ffffff').pack(pady=15)
        tk.Label(result_win, text=result_text, font=('Segoe UI', 22, 'bold'),
                 bg='#1a1a2a', fg=color).pack(pady=10)
        
        stats_frame = tk.Frame(result_win, bg='#1a1a2a')
        stats_frame.pack(pady=20)
        # Controles visuales de Safe, Warning, Danger

        frame1 = tk.Frame(stats_frame, bg=self.colors['success'], width=110, height=90, highlightbackground='#ffffff', highlightthickness=2)
        frame1.grid(row=0, column=0, padx=5); frame1.pack_propagate(False)
        tk.Label(frame1, text=str(safe_bars), font=('Segoe UI', 32, 'bold'), bg=self.colors['success'], fg='#ffffff').pack(expand=True)
        tk.Label(frame1, text="SICURE", font=('Segoe UI', 12, 'bold'), bg=self.colors['success'], fg='#ffffff').pack()
        
        frame2 = tk.Frame(stats_frame, bg=self.colors['warning'], width=110, height=90, highlightbackground='#ffffff', highlightthickness=2)
        frame2.grid(row=0, column=1, padx=5); frame2.pack_propagate(False)
        tk.Label(frame2, text=str(warning_bars), font=('Segoe UI', 32, 'bold'), bg=self.colors['warning'], fg='#ffffff').pack(expand=True)
        tk.Label(frame2, text="ATTENZIONE", font=('Segoe UI', 12, 'bold'), bg=self.colors['warning'], fg='#ffffff').pack()
        
        frame3 = tk.Frame(stats_frame, bg=self.colors['danger'], width=110, height=90, highlightbackground='#ffffff', highlightthickness=2)
        frame3.grid(row=0, column=2, padx=5); frame3.pack_propagate(False)
        tk.Label(frame3, text=str(danger_bars), font=('Segoe UI', 32, 'bold'), bg=self.colors['danger'], fg='#ffffff').pack(expand=True)
        tk.Label(frame3, text="PERICOLO", font=('Segoe UI', 12, 'bold'), bg=self.colors['danger'], fg='#ffffff').pack()
        
        btn_frame = tk.Frame(result_win, bg='#1a1a2a')
        btn_frame.pack(pady=15)
        tk.Button(btn_frame, text="OK", font=('Segoe UI', 13, 'bold'), bg='#3a86ff',
                  fg='white', relief='flat', padx=35, pady=8, cursor='hand2',
                  command=result_win.destroy).pack()
    
    def update_results_table(self, area=5.0):
        """Actualiza la tabla con los resultados (Fuerza y Tensión)."""
        for item in self.results_tree.get_children():
            self.results_tree.delete(item)
        
        if not self.current_forces:
            return
        real_bar_count = len(self.current_bridge.bars_dir) if hasattr(self.current_bridge, 'bars_dir') else len(self.current_forces)
        for i in range(min(real_bar_count, len(self.current_forces))):
            bar_name = f'Barra {i+1}'
            try:
                force_val = float(self.current_forces[i])
                stress_val = abs(force_val) / area if area > 0 else 0 # Tensión = |Fuerza| / Área
                
                if stress_val < 15:
                    status = "Sicuro"
                elif stress_val < 25:
                    status = "Attenzione"
                else:
                    status = "Pericolo"
                
                force_type = "C" if force_val < 0 else "T"
                
                self.results_tree.insert('', 'end', values=(
                    bar_name,
                    f'{abs(force_val):.2f}{force_type}', 
                    f'{stress_val:.2f} kN/cm²',
                    status
                ))
            except Exception as e:
                print(f"Error inserting result for bar {bar_name}: {e}")
                
    def update_stress_chart(self, area=5.0):
        """Genera y actualiza el gráfico de distribución de tensiones."""
        if not self.current_forces:
            self.create_empty_chart()
            return

        # Limpiar
        for widget in self.graph_frame.winfo_children():
            widget.destroy()
        forces = self.current_forces[:len(self.current_bridge.bars_dir)]
        bar_names = [f'Barra {i+1}' for i in range(len(forces))]
        stresses = [abs(f) / area for f in forces]
        colors = []
        for s in stresses:
            if s < 15:
                colors.append(self.colors['success'])
            elif s < 25:
                colors.append(self.colors['warning'])
            else:
                colors.append(self.colors['danger'])

        # Creación de la figura Matplotlib
        fig, ax = plt.subplots(figsize=(6, 4), facecolor=self.colors['bg_primary'])
        ax.set_facecolor(self.colors['bg_primary'])
        bars = ax.bar(bar_names, stresses, color=colors)
        
        #Tema oscuro
        ax.set_ylabel('Tensione (kN/cm²)', color=self.colors['text_secondary'])
        ax.set_title('Distribuzione Tensione per Barra', color=self.colors['text_primary'])
        ax.tick_params(axis='x', colors=self.colors['text_secondary'], rotation=45, labelsize=8)
        ax.tick_params(axis='y', colors=self.colors['text_secondary'])
        for spine in ax.spines.values():
            spine.set_edgecolor(self.colors['border'])
        # Mostrar el gráfico
        self.chart_canvas = FigureCanvasTkAgg(fig, self.graph_frame)
        self.chart_canvas.draw()
        self.chart_canvas.get_tk_widget().pack(fill='both', expand=True)

    def clear_results(self):
        """Limpia la tabla de resultados y el gráfico."""
        for item in self.results_tree.get_children():
            self.results_tree.delete(item)
        
        for widget in self.graph_frame.winfo_children():
            widget.destroy()
        self.create_empty_chart()
        
    def run(self):
        self.root.mainloop()
if __name__ == '__main__':
    if not BACKEND_OK:
        print("ATTENZIONE: I moduli BACKEND.py o CORE.py non sono stati trovati. La simulazione non funzionerà.")
    
    app = BridgeSimulator()
    app.run()