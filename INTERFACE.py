"""
INTERFACE.py - BridgeSimulator GUI
Entry point for the application.
Run: python INTERFACE.py
"""

import tkinter as tk
from tkinter import ttk, messagebox
import turtle
import os
import sys
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    import BACKEND as bob
    import CORE as pt
    BACKEND_OK = True
except ImportError:
    BACKEND_OK = False


# ---------------------------------------------------------------------------
# Main application class
# ---------------------------------------------------------------------------

class BridgeSimulator:

    def __init__(self):
        self.root = tk.Tk()
        self.root.title("BridgeSimulator")
        self.root.geometry("1400x900")
        self.root.minsize(1200, 800)

        self.icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "catt.ico")
        try:
            self.root.iconbitmap(self.icon_path)
        except Exception:
            pass

        self.current_bridge = None
        self.current_forces = []
        self.pan_offset     = [0, 0]
        self.last_mouse_pos = (0, 0)

        self.root.bind('<Configure>', self.on_window_resize)

        self.setup_theme()
        self.create_layout()
        self.create_components()

    # -----------------------------------------------------------------------
    # Theme
    # -----------------------------------------------------------------------

    def setup_theme(self):
        self.colors = {
            'bg_primary':       '#0a0a0f',
            'bg_secondary':     '#1a1a2a',
            'bg_card':          '#252538',
            'accent_primary':   '#3a86ff',
            'accent_secondary': '#8338ec',
            'text_primary':     '#f8f9fa',
            'text_secondary':   '#adb5bd',
            'success':          '#38b000',
            'warning':          '#ff9e00',
            'danger':           '#ef233c',
            'border':           '#495057',
        }
        self.root.configure(bg=self.colors['bg_primary'])

    # -----------------------------------------------------------------------
    # Layout
    # -----------------------------------------------------------------------

    def create_layout(self):
        # Left panel: controls (fixed width)
        self.left_panel = tk.Frame(self.root, bg=self.colors['bg_secondary'], width=400)
        self.left_panel.pack(side='left', fill='both', padx=20, pady=20)
        self.left_panel.pack_propagate(False)

        # Right panel: visualization (70 %) + results (30 %)
        self.right_panel = tk.Frame(self.root, bg=self.colors['bg_primary'])
        self.right_panel.pack(side='right', fill='both', expand=True, padx=(0, 20), pady=20)
        self.right_panel.grid_rowconfigure(0, weight=70)
        self.right_panel.grid_rowconfigure(1, weight=30)
        self.right_panel.grid_columnconfigure(0, weight=1)

        self.viz_frame = tk.Frame(self.right_panel, bg=self.colors['bg_primary'])
        self.viz_frame.grid(row=0, column=0, sticky='nsew', pady=(0, 10))

        self.results_frame = tk.Frame(self.right_panel, bg=self.colors['bg_primary'])
        self.results_frame.grid(row=1, column=0, sticky='nsew')

    def create_components(self):
        self.create_header()
        self.create_bridge_controls()
        self.create_load_controls()
        self.create_action_buttons()
        self.create_visualization()
        self.create_results_tabs()

    # -----------------------------------------------------------------------
    # UI helpers
    # -----------------------------------------------------------------------

    def create_header(self):
        header = tk.Frame(self.left_panel, bg=self.colors['bg_secondary'], height=100)
        header.pack(fill='x', pady=(0, 20))
        header.pack_propagate(False)

        title_frame = tk.Frame(header, bg=self.colors['bg_secondary'])
        title_frame.pack(side='left', fill='y')

        for line in ('Structural Evaluation', 'of Truss Bridges'):
            tk.Label(title_frame, text=line,
                     font=('Segoe UI', 20, 'bold'),
                     bg=self.colors['bg_secondary'],
                     fg=self.colors['text_primary']).pack(anchor='w')

    def create_card(self, parent, title):
        """Reusable card widget with a title bar and content area."""
        card = tk.Frame(parent, bg=self.colors['bg_card'],
                        highlightbackground=self.colors['border'], highlightthickness=1)
        card.pack(fill='x', pady=(0, 15))
        tk.Label(card, text=title, font=('Segoe UI', 13, 'bold'),
                 bg=self.colors['bg_card'], fg=self.colors['text_primary']).pack(fill='x', padx=20, pady=15)
        tk.Frame(card, height=1, bg=self.colors['border']).pack(fill='x', padx=20, pady=(0, 15))
        content = tk.Frame(card, bg=self.colors['bg_card'])
        content.pack(fill='both', expand=True, padx=20, pady=(0, 20))
        return content

    def _label(self, parent, text, row, col, **kwargs):
        """Shortcut for a standard grid label."""
        font = kwargs.get('font', ('Segoe UI', 15))
        fg   = kwargs.get('fg', self.colors['text_secondary'])
        tk.Label(parent, text=text, font=font,
                 bg=self.colors['bg_card'], fg=fg).grid(row=row, column=col, sticky='w', padx=15, pady=5)

    def _entry(self, parent, var, row):
        """Shortcut for a standard grid entry."""
        tk.Entry(parent, textvariable=var, font=('Segoe UI', 10),
                 bg='#2d3748', fg='white', insertbackground='white',
                 relief='flat').grid(row=row, column=1, sticky='ew', padx=(0, 15), pady=5, ipady=5)

    # -----------------------------------------------------------------------
    # Control panels
    # -----------------------------------------------------------------------

    def create_bridge_controls(self):
        card = self.create_card(self.left_panel, "BRIDGE CONFIGURATION")
        for i in range(6):
            card.grid_rowconfigure(i, minsize=50)
        card.grid_columnconfigure(1, weight=1)

        # Bridge type
        self._label(card, "Bridge type:", 0, 0)
        self.bridge_type = tk.StringVar(value="Pratt")
        combo = ttk.Combobox(card, textvariable=self.bridge_type,
                             values=["Pratt", "Warren", "K-truss"],
                             state="readonly", font=('Segoe UI', 10))
        combo.grid(row=0, column=1, sticky='ew', padx=(0, 15), pady=5)
        combo.bind('<<ComboboxSelected>>', self.on_bridge_type_change)

        # Node count
        self._label(card, "Nodes:", 1, 0)
        nodes_frame = tk.Frame(card, bg=self.colors['bg_card'])
        nodes_frame.grid(row=1, column=1, sticky='w', padx=(0, 15), pady=5)
        self.nodes_var = tk.IntVar(value=8)
        for text, cmd in [('−', self.decrease_nodes), ('+', self.increase_nodes)]:
            tk.Button(nodes_frame, text=text, font=('Segoe UI', 10), width=3,
                      bg=self.colors['accent_primary'], fg='white', relief='flat',
                      command=cmd).pack(side='left')
            if text == '−':
                tk.Label(nodes_frame, textvariable=self.nodes_var,
                         font=('Segoe UI', 11), bg=self.colors['bg_card'],
                         fg=self.colors['text_primary'], width=6).pack(side='left', padx=10)

        # Numeric inputs
        self._label(card, "Length (m):", 2, 0)
        self.length_var = tk.StringVar(value="")
        self._entry(card, self.length_var, 2)

        self._label(card, "Height (m):", 3, 0)
        self.height_var = tk.StringVar(value="")
        self._entry(card, self.height_var, 3)

        self._label(card, "Material:", 4, 0)
        self.material_var = tk.StringVar(value="A36")
        ttk.Combobox(card, textvariable=self.material_var,
                     values=["A36", "S275", "S355", "A572", "A588", "S460"],
                     state="readonly", font=('Segoe UI', 10)).grid(
                         row=4, column=1, sticky='ew', padx=(0, 15), pady=5)

        self._label(card, "Section area (cm²):", 5, 0)
        self.area_var = tk.StringVar(value="")
        self._entry(card, self.area_var, 5)

    def create_load_controls(self):
        card = self.create_card(self.left_panel, "LOAD ANALYSIS")
        for i in range(3):
            card.grid_rowconfigure(i, minsize=55)
        card.grid_columnconfigure(1, weight=1)

        self._label(card, "Target node:", 0, 0, fg=self.colors['text_primary'])
        self.node_var   = tk.StringVar()
        self.node_combo = ttk.Combobox(card, textvariable=self.node_var,
                                       state="readonly", font=('Segoe UI', 11))
        self.node_combo.grid(row=0, column=1, sticky='ew', padx=(0, 15), pady=8)

        self._label(card, "Load (kN):", 1, 0, fg=self.colors['text_primary'])
        self.load_var = tk.StringVar(value="")
        tk.Entry(card, textvariable=self.load_var, font=('Segoe UI', 11),
                 bg='#2d3748', fg='white', insertbackground='white',
                 relief='flat').grid(row=1, column=1, sticky='ew', padx=(0, 15), pady=8, ipady=6)

        self._label(card, "Angle (°):", 2, 0, fg=self.colors['text_primary'])
        self.angle_var = tk.StringVar(value="")
        tk.Entry(card, textvariable=self.angle_var, font=('Segoe UI', 11),
                 bg='#2d3748', fg='white', insertbackground='white',
                 relief='flat').grid(row=2, column=1, sticky='ew', padx=(0, 15), pady=8, ipady=6)

    def create_action_buttons(self):
        btn_card = tk.Frame(self.left_panel, bg=self.colors['bg_secondary'])
        btn_card.pack(fill='x', pady=(20, 0))

        self.generate_btn = tk.Button(
            btn_card, text='GENERATE BRIDGE', font=('Segoe UI', 18, 'bold'),
            bg=self.colors['accent_primary'], fg='white', relief='flat',
            padx=30, pady=14, cursor='hand2', command=self.generate_bridge)
        self.generate_btn.pack(fill='x', pady=(0, 10))

        self.analyze_btn = tk.Button(
            btn_card, text='ANALYZE LOADS', font=('Segoe UI', 18, 'bold'),
            bg=self.colors['accent_secondary'], fg='white', relief='flat',
            padx=30, pady=14, cursor='hand2', command=self.analyze_loads)
        self.analyze_btn.pack(fill='x')

    # -----------------------------------------------------------------------
    # Visualization canvas
    # -----------------------------------------------------------------------

    def create_visualization(self):
        title_frame = tk.Frame(self.viz_frame, bg=self.colors['bg_primary'])
        title_frame.pack(fill='x', pady=(0, 10))
        tk.Label(title_frame, text='BRIDGE VISUALIZATION',
                 font=('Segoe UI', 14, 'bold'),
                 bg=self.colors['bg_primary'],
                 fg=self.colors['text_primary']).pack(side='left')

        canvas_container = tk.Frame(self.viz_frame, bg=self.colors['bg_primary'])
        canvas_container.pack(fill='both', expand=True)

        self.viz_canvas = tk.Canvas(canvas_container,
                                    bg=self.colors['bg_secondary'],
                                    highlightbackground=self.colors['border'],
                                    highlightthickness=2)
        self.viz_canvas.pack(fill='both', expand=True, padx=20, pady=10)
        self.viz_canvas.bind('<Button-1>', self.start_pan)
        self.viz_canvas.bind('<B1-Motion>', self.do_pan)
        self.viz_canvas.bind('<Configure>', lambda e: self.on_canvas_resize())

        self.screen     = turtle.TurtleScreen(self.viz_canvas)
        self.turtle_pen = turtle.RawTurtle(self.screen)
        self.turtle_pen.hideturtle()
        self.screen.tracer(0)

    # -----------------------------------------------------------------------
    # Results tabs
    # -----------------------------------------------------------------------

    def create_results_tabs(self):
        style = ttk.Style()
        style.theme_use('clam')
        style.configure('Custom.TNotebook',
                        background=self.colors['bg_primary'], borderwidth=0)
        style.configure('Custom.TNotebook.Tab',
                        background=self.colors['bg_card'],
                        foreground=self.colors['text_primary'],
                        padding=[15, 5], font=('Segoe UI', 10, 'bold'),
                        borderwidth=1, relief='flat')
        style.map('Custom.TNotebook.Tab',
                  background=[('selected', self.colors['accent_primary'])],
                  foreground=[('selected', 'white')])

        self.notebook = ttk.Notebook(self.results_frame, style='Custom.TNotebook')
        self.notebook.pack(fill='both', expand=True)

        # --- Results table tab ---
        self.results_tab = tk.Frame(self.notebook, bg=self.colors['bg_secondary'])
        self.notebook.add(self.results_tab, text='Results')

        style.configure('Treeview',
                        background=self.colors['bg_secondary'],
                        foreground=self.colors['text_primary'],
                        fieldbackground=self.colors['bg_secondary'],
                        font=('Segoe UI', 10), rowheight=25, borderwidth=0)
        style.configure('Treeview.Heading',
                        background=self.colors['bg_card'],
                        foreground=self.colors['text_primary'],
                        font=('Segoe UI', 10, 'bold'), borderwidth=1, relief='flat')

        columns = ('Bar', 'Force (kN)', 'Stress', 'Status')
        self.results_tree = ttk.Treeview(self.results_tab, columns=columns, show='headings')
        for col in columns:
            self.results_tree.heading(col, text=col)
            self.results_tree.column(col, anchor='center')

        scrollbar = ttk.Scrollbar(self.results_tab, orient='vertical',
                                   command=self.results_tree.yview)
        self.results_tree.configure(yscrollcommand=scrollbar.set)

        self.results_tab.grid_columnconfigure(0, weight=1)
        self.results_tab.grid_rowconfigure(0, weight=1)
        self.results_tree.grid(row=0, column=0, sticky='nsew', padx=10, pady=10)
        scrollbar.grid(row=0, column=1, sticky='ns', pady=10)

        # --- Chart tab ---
        self.graph_tab = tk.Frame(self.notebook, bg=self.colors['bg_primary'])
        self.notebook.add(self.graph_tab, text='Chart')
        self.graph_frame = tk.Frame(self.graph_tab, bg=self.colors['bg_primary'])
        self.graph_frame.pack(fill='both', expand=True, padx=10, pady=10)
        self.create_empty_chart()

    def create_empty_chart(self):
        fig, ax = plt.subplots(figsize=(6, 4), facecolor=self.colors['bg_primary'])
        ax.set_facecolor(self.colors['bg_primary'])
        ax.text(0.5, 0.5, 'Run analysis to see stress distribution',
                ha='center', va='center', transform=ax.transAxes,
                color=self.colors['text_secondary'], fontsize=12)
        ax.set_xticks([])
        ax.set_yticks([])
        for spine in ax.spines.values():
            spine.set_visible(False)
        self.chart_canvas = FigureCanvasTkAgg(fig, self.graph_frame)
        self.chart_canvas.draw()
        self.chart_canvas.get_tk_widget().pack(fill='both', expand=True)

    # -----------------------------------------------------------------------
    # Event handlers
    # -----------------------------------------------------------------------

    def on_window_resize(self, event):
        if self.current_bridge and event.widget == self.root:
            self.root.after(50, self.force_redraw)

    def on_canvas_resize(self):
        if self.current_bridge:
            self.draw_bridge()

    def force_redraw(self):
        if self.current_bridge:
            self.viz_canvas.update_idletasks()
            self.draw_bridge()

    def on_bridge_type_change(self, event=None):
        self.nodes_var.set(14 if self.bridge_type.get() == "K-truss" else 8)

    def increase_nodes(self):
        step = 6 if self.bridge_type.get() == "K-truss" else 4
        self.nodes_var.set(self.nodes_var.get() + step)

    def decrease_nodes(self):
        step    = 6 if self.bridge_type.get() == "K-truss" else 4
        current = self.nodes_var.get()
        if current - step >= 8:
            self.nodes_var.set(current - step)

    # -----------------------------------------------------------------------
    # Pan support
    # -----------------------------------------------------------------------

    def start_pan(self, event):
        self.last_mouse_pos = (event.x, event.y)

    def do_pan(self, event):
        if not self.current_bridge:
            return
        dx = event.x - self.last_mouse_pos[0]
        dy = event.y - self.last_mouse_pos[1]
        self.pan_offset[0] += dx
        self.pan_offset[1] += dy
        self.last_mouse_pos = (event.x, event.y)
        self.draw_bridge()

    # -----------------------------------------------------------------------
    # Drawing
    # -----------------------------------------------------------------------

    def draw_bridge(self):
        self.turtle_pen.clear()
        if not self.current_bridge or not hasattr(self.current_bridge, 'bars_dir'):
            self.screen.update()
            return

        self.viz_canvas.update_idletasks()
        canvas_w = self.viz_canvas.winfo_width()
        canvas_h = self.viz_canvas.winfo_height()
        if canvas_w <= 10 or canvas_h <= 10:
            return

        # Bounding box and scale
        nodes_x = [n.x for n in self.current_bridge.nodes_dir.values()]
        nodes_y = [n.y for n in self.current_bridge.nodes_dir.values()]
        if not nodes_x:
            return

        min_x, max_x = min(nodes_x), max(nodes_x)
        min_y, max_y = min(nodes_y), max(nodes_y)
        bridge_w = max(max_x - min_x, 1)
        bridge_h = max(max_y - min_y, 1)

        margin = 0.8
        scale  = min((canvas_w * margin) / bridge_w, (canvas_h * margin) / bridge_h)

        # FIX: center both horizontally and vertically
        center_x_model = (min_x + max_x) / 2
        center_y_model = (min_y + max_y) / 2
        offset_x = -center_x_model * scale + self.pan_offset[0]
        offset_y = -center_y_model * scale + self.pan_offset[1]

        self.turtle_pen.speed(0)
        self.turtle_pen.width(3)

        # Draw bars (coloured by stress if analysis has been run)
        n_bars    = len(self.current_bridge.bars_dir)
        max_force = (max(abs(f) for f in self.current_forces[:n_bars])
                     if self.current_forces and n_bars > 0 else 1)

        for idx, bar in enumerate(self.current_bridge.bars_dir.values()):
            if idx < len(self.current_forces):
                ratio = abs(self.current_forces[idx]) / max_force if max_force > 0 else 0
                self.turtle_pen.color(self.stress_to_color(ratio))
            else:
                self.turtle_pen.color(self.colors['accent_primary'])

            try:
                n1, n2 = bar.nodes
                x1, y1 = n1.x * scale + offset_x, n1.y * scale + offset_y
                x2, y2 = n2.x * scale + offset_x, n2.y * scale + offset_y
                self.turtle_pen.penup()
                self.turtle_pen.goto(x1, y1)
                self.turtle_pen.pendown()
                self.turtle_pen.goto(x2, y2)
            except Exception:
                pass

        # Draw nodes
        self.turtle_pen.penup()
        self.turtle_pen.color(self.colors['text_primary'])
        for node in self.current_bridge.nodes_dir.values():
            try:
                x = node.x * scale + offset_x
                y = node.y * scale + offset_y
                self.turtle_pen.goto(x, y)
                self.turtle_pen.dot(10)
            except Exception:
                pass

        self.screen.update()

    def stress_to_color(self, ratio):
        """Map a [0, 1] stress ratio to a traffic-light colour."""
        ratio = max(0.0, min(1.0, ratio))
        if ratio < 0.3:
            return self.colors['success']
        elif ratio < 0.7:
            return self.colors['warning']
        return self.colors['danger']

    # -----------------------------------------------------------------------
    # Business logic
    # -----------------------------------------------------------------------

    def generate_bridge(self):
        if not BACKEND_OK:
            messagebox.showerror('Error', 'Backend modules not available')
            return

        for var, name in [(self.length_var, "Length"),
                          (self.height_var,  "Height"),
                          (self.area_var,    "Section area")]:
            if not var.get().strip():
                messagebox.showerror('Error', f'Please enter: {name}')
                return

        try:
            self.generate_btn.config(state='disabled', text='GENERATING...')
            self.root.update()

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

            self.pan_offset = [0, 0]
            self.viz_canvas.update_idletasks()
            self.draw_bridge()

        except Exception as e:
            messagebox.showerror('Error', f'Generation failed:\n{e}')
        finally:
            self.generate_btn.config(state='normal', text='GENERATE BRIDGE')

    def update_node_list(self):
        """Refresh the node selection combobox after a new bridge is built."""
        self.node_combo.set('')
        if self.current_bridge and hasattr(self.current_bridge, 'nodes_dir'):
            nodes = sorted(
                self.current_bridge.nodes_dir.keys(),
                key=lambda x: int(x.replace('node', ''))
            )
            self.node_combo['values'] = nodes
            if nodes:
                self.node_combo.current(0)

    def analyze_loads(self):
        if not self.current_bridge:
            messagebox.showwarning('Warning', 'Generate a bridge first')
            return
        if not self.node_var.get():
            messagebox.showwarning('Warning', 'Select a target node')
            return
        for var, name in [(self.load_var, "Load"), (self.angle_var, "Angle")]:
            if not var.get().strip():
                messagebox.showerror('Error', f'Please enter: {name}')
                return

        try:
            self.analyze_btn.config(state='disabled', text='ANALYZING...')
            self.root.update()

            node_num  = int(self.node_var.get().replace('node', ''))
            load_val  = float(self.load_var.get())
            angle_val = float(self.angle_var.get())
            area_val  = float(self.area_var.get()) if self.area_var.get() else 5.0

            self.current_bridge.set_load(load_val, angle_val, node_num)
            forces = self.current_bridge.do_calc()

            self.current_forces = forces.tolist() if hasattr(forces, 'tolist') else list(forces)

            self.check_bridge_viability(area_val)
            self.update_results_table(area_val)
            self.update_stress_chart(area_val)
            self.draw_bridge()

        except Exception as e:
            messagebox.showerror('Error', f'Analysis failed:\n{e}')
        finally:
            self.analyze_btn.config(state='normal', text='ANALYZE LOADS')

    # -----------------------------------------------------------------------
    # Results display
    # -----------------------------------------------------------------------

    # Stress thresholds (kN/cm²)
    _STRESS_SAFE    = 15
    _STRESS_WARNING = 25

    def _classify_stress(self, stress_val):
        if stress_val < self._STRESS_SAFE:
            return "Safe"
        elif stress_val < self._STRESS_WARNING:
            return "Warning"
        return "Danger"

    def check_bridge_viability(self, area=5.0):
        """Show a pop-up summarising the overall bridge safety."""
        if not self.current_forces:
            return

        n_bars = (len(self.current_bridge.bars_dir)
                  if hasattr(self.current_bridge, 'bars_dir')
                  else len(self.current_forces))

        safe_bars, warning_bars, danger_bars = 0, 0, 0
        for i in range(min(n_bars, len(self.current_forces))):
            try:
                stress = abs(float(self.current_forces[i])) / area if area > 0 else 0
                status = self._classify_stress(stress)
                if status == "Safe":
                    safe_bars += 1
                elif status == "Warning":
                    warning_bars += 1
                else:
                    danger_bars += 1
            except Exception:
                pass

        if danger_bars == 0 and warning_bars == 0:
            result_text = "BRIDGE VIABLE"
            color = self.colors['success']
        elif danger_bars == 0:
            result_text = "BRIDGE ACCEPTABLE"
            color = self.colors['warning']
        else:
            result_text = "BRIDGE NOT VIABLE"
            color = self.colors['danger']

        # Result window
        win = tk.Toplevel(self.root)
        win.title("Analysis Result")
        win.geometry("450x350")
        win.configure(bg='#1a1a2a')
        win.resizable(False, False)
        win.transient(self.root)
        try:
            win.iconbitmap(self.icon_path)
        except Exception:
            pass

        tk.Frame(win, bg=color, height=5).pack(fill='x', pady=(0, 10))
        tk.Label(win, text="ANALYSIS COMPLETE",
                 font=('Segoe UI', 18, 'bold'),
                 bg='#1a1a2a', fg='#ffffff').pack(pady=15)
        tk.Label(win, text=result_text,
                 font=('Segoe UI', 22, 'bold'),
                 bg='#1a1a2a', fg=color).pack(pady=10)

        stats = tk.Frame(win, bg='#1a1a2a')
        stats.pack(pady=20)

        for col, (count, label, c) in enumerate([
            (safe_bars,    "SAFE",    self.colors['success']),
            (warning_bars, "WARNING", self.colors['warning']),
            (danger_bars,  "DANGER",  self.colors['danger']),
        ]):
            f = tk.Frame(stats, bg=c, width=110, height=90,
                         highlightbackground='#ffffff', highlightthickness=2)
            f.grid(row=0, column=col, padx=5)
            f.pack_propagate(False)
            tk.Label(f, text=str(count), font=('Segoe UI', 32, 'bold'),
                     bg=c, fg='#ffffff').pack(expand=True)
            tk.Label(f, text=label, font=('Segoe UI', 12, 'bold'),
                     bg=c, fg='#ffffff').pack()

        tk.Button(win, text="OK", font=('Segoe UI', 13, 'bold'),
                  bg=self.colors['accent_primary'], fg='white', relief='flat',
                  padx=35, pady=8, cursor='hand2',
                  command=win.destroy).pack(pady=15)

    def update_results_table(self, area=5.0):
        """Refresh the results Treeview with force and stress values."""
        for item in self.results_tree.get_children():
            self.results_tree.delete(item)
        if not self.current_forces:
            return

        n_bars = (len(self.current_bridge.bars_dir)
                  if hasattr(self.current_bridge, 'bars_dir')
                  else len(self.current_forces))

        for i in range(min(n_bars, len(self.current_forces))):
            try:
                force  = float(self.current_forces[i])
                stress = abs(force) / area if area > 0 else 0
                status = self._classify_stress(stress)
                ftype  = "C" if force < 0 else "T"   # compression / tension

                self.results_tree.insert('', 'end', values=(
                    f'Bar {i+1}',
                    f'{abs(force):.2f} {ftype}',
                    f'{stress:.2f} kN/cm²',
                    status
                ))
            except Exception as e:
                print(f"[results_table] bar {i+1}: {e}")

    def update_stress_chart(self, area=5.0):
        """Redraw the Matplotlib bar chart with current stress values."""
        if not self.current_forces:
            self.create_empty_chart()
            return

        for widget in self.graph_frame.winfo_children():
            widget.destroy()

        n_bars   = len(self.current_bridge.bars_dir)
        forces   = self.current_forces[:n_bars]
        stresses = [abs(f) / area for f in forces]
        bar_names = [f'Bar {i+1}' for i in range(len(forces))]
        colors    = [
            (self.colors['success']  if s < self._STRESS_SAFE else
             self.colors['warning']  if s < self._STRESS_WARNING else
             self.colors['danger'])
            for s in stresses
        ]

        fig, ax = plt.subplots(figsize=(6, 4), facecolor=self.colors['bg_primary'])
        ax.set_facecolor(self.colors['bg_primary'])
        ax.bar(bar_names, stresses, color=colors)
        ax.set_ylabel('Stress (kN/cm²)', color=self.colors['text_secondary'])
        ax.set_title('Stress Distribution per Bar', color=self.colors['text_primary'])
        ax.tick_params(axis='x', colors=self.colors['text_secondary'], rotation=45, labelsize=8)
        ax.tick_params(axis='y', colors=self.colors['text_secondary'])
        for spine in ax.spines.values():
            spine.set_edgecolor(self.colors['border'])

        self.chart_canvas = FigureCanvasTkAgg(fig, self.graph_frame)
        self.chart_canvas.draw()
        self.chart_canvas.get_tk_widget().pack(fill='both', expand=True)

    def clear_results(self):
        """Clear the table and reset the chart."""
        for item in self.results_tree.get_children():
            self.results_tree.delete(item)
        for widget in self.graph_frame.winfo_children():
            widget.destroy()
        self.create_empty_chart()

    # -----------------------------------------------------------------------
    # Entry point
    # -----------------------------------------------------------------------

    def run(self):
        self.root.mainloop()


if __name__ == '__main__':
    if not BACKEND_OK:
        print("WARNING: BACKEND.py or CORE.py not found — simulation will not work.")
    app = BridgeSimulator()
    app.run()
