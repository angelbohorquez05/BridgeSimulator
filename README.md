# BridgeSimulator

Academic simulator for the structural analysis of 2D truss bridges based on **statics** and **structural equilibrium** principles.

---

## Academic context

BridgeSimulator was developed as an **academic project** for educational purposes, focused on understanding the internal behavior of truss bridge structures.

The main goal is to apply concepts from:

* Structural statics
* Classical mechanics
* Linear algebra
* Structural modeling
* Object-oriented programming

---

## Features

* Parametric generation of **Pratt**, **Warren**, and **K-Truss** bridges
* Definition of number of nodes, span length, height, and material
* Application of concentrated loads on selected nodes
* Computation of internal axial forces in each bar
* Stress evaluation and safety classification
* Interactive graphical visualization of the structure
* Results table and stress distribution chart

---

## Model limitations

* **Static analysis only** (no dynamic effects)
* **Linear elastic** behavior
* **2D structures**
* Buckling, fatigue, and nonlinear effects are not considered
* Intended exclusively for educational use

---

## Technologies used

* **Python 3**
* **Tkinter** — Graphical user interface
* **Turtle** — Structural visualization
* **Matplotlib** — Stress distribution plots

---

## How to run

From the project root directory:

```bash
python INTERFACE.py
```

Make sure the files `BACKEND.py` and `CORE.py` are located in the same directory.

---

## Project structure

* `INTERFACE.py` — Graphical interface and application controller
* `BACKEND.py` — Bridge generation and structural calculations
* `CORE.py` — Node, bar, and matrix operation definitions

---
