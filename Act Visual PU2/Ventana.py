import os
import tkinter as tk
from tkinter import ttk
import platform
from tkinter import messagebox

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

main = tk.Tk()
main.title("GO FILE EXPLORER")
main.config(bg="#CFCFCF")

sistema = platform.system()

margen = 10
main.update_idletasks()

ancho_monitor = main.winfo_screenwidth()
alto_monitor  = main.winfo_screenheight()
ancho = ancho_monitor - 2 * margen
alto  = alto_monitor  - 2 * margen

if sistema == "Windows":
    main.state("zoomed")
else:
    main.geometry(f"{ancho}x{alto}+{margen}+{margen}")

main.minsize(600, 400)
main.resizable(True, True)

mode = False

# ===================================================
main.columnconfigure(0, weight=1)
main.rowconfigure(0, weight=0)
main.rowconfigure(1, weight=1)
main.rowconfigure(2, weight=0)

# ===================== CONTENT =====================
content_frame = tk.Frame(main, bg="#CFCFCF")
content_frame.grid(row=1, column=0, sticky="nsew")
#========================Dark Mode===================
def Modo_Oscuro():
    content_frame.config(background="#252525")
    center_frame.config(background="#252525")
    title_frame.config(background="#252525")
    ui_frame.config(background="#252525")
    label_title.config(background="#252525", foreground="#7f49b4")
    label_title2.config(background="#252525", foreground="#cfcfcf")
    top_bar.config(background="#7f49b4")
    mode = True

ModoOscuro = ttk.Button(
    content_frame,
    text="◐",
    command= Modo_Oscuro
)
ModoOscuro.pack(side="right", anchor="n", pady=5, padx=5)
# ===================== ESTILO =====================
style = ttk.Style()
style.theme_use('clam')

style.configure(
    "Custom.TEntry",
    padding=5,
    relief="flat",
)

# ===================== CONTENEDOR CENTRADO =====================
center_frame = tk.Frame(content_frame, bg="#CFCFCF")
center_frame.place(relx=0.5, rely=0.5, anchor="center")

# ===== CONTENEDOR VERTICAL (TÍTULO + BARRA) =====
ui_frame = tk.Frame(center_frame, bg="#CFCFCF")
ui_frame.pack()

# ===================== TÍTULO =====================
title_frame = tk.Frame(ui_frame, bg="#CFCFCF")
title_frame.pack()

label_title = tk.Label(
    title_frame,
    text="GO",
    bg="#CFCFCF",
    font=("Segoe UI", 50, "bold"),
    foreground="#141414"
)
label_title.pack(side="left")

label_title2 = ttk.Label(
    title_frame,
    text="FILEXPLORER",
    background="#CFCFCF",
    foreground="#7F49B4",
    font=("Segoe UI", 50, "bold")
)
label_title2.pack(side="left", padx=(5, 0))

# ===================== BARRA DE BÚSQUEDA =====================
barra = ttk.Entry(
    ui_frame,
    style="Custom.TEntry",
    font=("Segoe UI", 10),
    width=80,
)
barra.pack(pady=(10, 0))

irbtn = ttk.Button(
    ui_frame,
    text="Ir",
    width=5
)
irbtn.pack(pady=15, side="bottom")

# ===================== TOP BAR (opcional visual) =====================
top_bar = tk.Frame(main, bg="#262528", height=90)
top_bar.grid(row=0, column=0, sticky="nsew",padx=0, pady=0)
top_bar.grid_propagate(False)
#===================== Barra de busqueda secundaria ==================
BarraBusqueda2 = ttk.Entry(
    top_bar,
    style="Custom.TEntry",
    font=("Segoe UI", 10),
    width=160,
    state="disabled"
)
BarraBusqueda2.pack()
BarraBusqueda2.grid(row=0,column=0,padx=10, pady=10)

favbtn = ttk.Button(
    top_bar,
    text="★",
    width=3
)
favbtn.pack()
favbtn.grid(row=0, column=2)
# ===================== CIERRE =====================
def cerrado():
    if messagebox.askokcancel("Salir", "¿Seguro que quieres cerrar el navegador?"):
        main.destroy()

main.protocol("WM_DELETE_WINDOW", cerrado)

main.mainloop()

