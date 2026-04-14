import os
import tkinter as tk
from tkinter import ttk
import platform
from tkinter import messagebox
import subprocess
from parser import RenderizadorParser
from html.parser import HTMLParser

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

main = tk.Tk()
main.title("GO FILE EXPLORER")
main.config(bg="#E4E2E2")

sistema = platform.system()

margen = 10  
main.update_idletasks()  

ancho_monitor = main.winfo_screenwidth()
alto_monitor = main.winfo_screenheight()

ancho = ancho_monitor - 2 * margen
alto = alto_monitor - 2 * margen

if sistema == "Windows":
    main.state("zoomed")  
else:
    
    main.geometry(f"{ancho}x{alto}+{margen}+{margen}")

main.minsize(600, 400)
main.resizable(True, True)

# ----------------- Style -----------------
style = ttk.Style(main)
style.theme_use("clam")

# ===================== MENU =====================
menu = tk.Menu(main)
main.config(menu=menu)

menu_0 = tk.Menu(menu, tearoff=0)
menu.add_cascade(label="Ventana Principal", menu=menu_0)

menu_1 = tk.Menu(menu, tearoff=0)
menu.add_cascade(label="Pestaña 2", menu=menu_1)

menu_2 = tk.Menu(menu, tearoff=0)
menu.add_cascade(label="Pestaña 3", menu=menu_2)

menu_3 = tk.Menu(menu, tearoff=0)
menu.add_cascade(label="+", menu=menu_3)

# ===================== GRID PRINCIPAL =====================
main.columnconfigure(0, weight=1)
main.rowconfigure(1, weight=1)

# ===================== TOP BAR =====================
entrada_var = tk.StringVar()
top_frame = tk.Frame(main, bg="#E4E2E2")
top_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=5)

top_frame.columnconfigure(0, weight=1)  
top_frame.columnconfigure(1, weight=0)  

style.configure("entry.TEntry", fieldbackground="#FFFFFF", foreground="#000")
frame_buscador = ttk.Entry(top_frame, style="entry.TEntry", textvariable=entrada_var)
frame_buscador.grid(row=0, column=0, sticky="ew", padx=(0, 5))

style.configure("button.TButton", background="#FFFFFF", foreground="#000")
style.map("button.TButton",
          background=[("active", "#E4E2E2")],
          foreground=[("active", "#000")])
#-----------------------------------------------------------------------------------
def cerrado():
    if messagebox.askokcancel("salir", "seguro que quieres que quieres cerrar el navegador"):
        main.destroy()
# =====================Barra de Estado =====================
barra_progreso=tk.StringVar()
barra_progreso.set("Barra de estado:En espera")
estado=tk.Label(main,textvariable=barra_progreso,bd=3,relief=tk.SUNKEN,anchor="w")
estado.grid(row=3, column=0, sticky="ew")

#-----------------------------------------------------------------------------------
def verificar_existencia():
            texto = entrada_var.get().strip() 
            if sistema == "Windows":
                if os.path.exists(texto): #Verificacion de existencia de archivos
                    barra_progreso.set("Barra de estado:Cargando...")
                    try:
                         parser = RenderizadorParser()
                         resultado = parser.renderizar(texto)
                         area_contenido.delete("1.0", "end")
                         area_contenido.insert("end", str(resultado))
                         estado.config(bg="green",fg="black")
                         barra_progreso.set("Barra de estado:Completado")
                    except Exception as e:
                         messagebox.showerror("Error", "El archivo no existe")
                         estado.config(bg="red",fg="lightgray")
                         barra_progreso.set("Barra de estado:ERROR")
            elif sistema == "Darwin":  # macOS
                if os.path.exist(texto): #Verificacion de existencia de archivos
                    barra_progreso.set("Barra de estado:Cargando...")
                    try:
                         parser = RenderizadorParser()
                         resultado = parser.renderizar(texto)
                         area_contenido.delete("1.0", "end")
                         area_contenido.insert("end", str(resultado))
                         estado.config(bg="green",fg="black")
                         barra_progreso.set("Barra de estado:Completado")
                    except Exception as e:
                         messagebox.showerror("Error", "El archivo no existe")
                         estado.config(bg="red",fg="lightgray")
                         barra_progreso.set("Barra de estado:ERROR")
            else:  # Linux 
                if os.path.exists(texto): #Verificaon de existencia de archivos
                    barra_progreso.set("Barra de estado:Cargando...")
                    try:
                         parser = RenderizadorParser()
                         resultado = parser.renderizar(texto)
                         area_contenido.delete("1.0", "end")
                         area_contenido.insert("end", str(resultado))
                         estado.config(bg="green",fg="black")
                         barra_progreso.set("Barra de estado:Completado")
                    except Exception as e:
                         messagebox.showerror("Error", "El archivo no existe")
                         estado.config(bg="red",fg="lightgray")
                         barra_progreso.set("Barra de estado:ERROR")
#------------------------------------------------------------------------------------
button_ir = ttk.Button(top_frame, text="Ir", style="button.TButton", state="disabled", command=verificar_existencia)
button_ir.grid(row=0, column=1)
#-----------------------------------------------------
def verificar_barra(*args):
    texto = entrada_var.get().strip()
    if texto == "":
        button_ir.config(state="disabled")
    else:
        button_ir.config(state="normal")

entrada_var.trace_add("write", verificar_barra)
#----------------------------------------------------

# ===================== CONTENT =====================
content_frame = tk.Frame(main, bg="#EDECEC")
content_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=5)

content_frame.columnconfigure(0, weight=0)  
content_frame.columnconfigure(1, weight=1)  
content_frame.rowconfigure(0, weight=1)

# ===================== SIDEBAR =====================
sidebar = tk.Frame(content_frame, bg="#EDECEC", width=150)
sidebar.grid(row=0, column=0, sticky="ns", padx=(0, 10))
sidebar.grid_propagate(False)

sidebar.rowconfigure(0, weight=1)
sidebar.rowconfigure(1, weight=0)

style.configure("entry1.TEntry", fieldbackground="#fff", foreground="#000")

entry1 = ttk.Entry(sidebar, style="entry1.TEntry")
entry1.grid(row=1, column=0, sticky="ew", padx=5, pady=5)

# ===================== MAIN AREA =====================
main_area = tk.Frame(content_frame, bg="#FFFFFF")
main_area.grid(row=0, column=1, sticky="nsew")
#---------------------------
area_contenido = tk.Text(main_area)
area_contenido.pack(expand=True, fill="both", padx=20, pady=10)

#======================BOTTOM BAR========================
bottom_bar = tk.Frame(main_area)
bottom_bar.pack(side="bottom", anchor="e", padx=10, pady=10)

#---------------------------FUNCIONES BOTTOM BAR-----------------------------
def Modo_Oscuro():
    # Colores principales
    color_fondo_ventana = "#2E2E2E"
    color_fondo_frame = "#3C3C3C"
    color_fondo_sidebar = "#444444"
    color_fondo_text = "#1E1E1E"
    color_fondo_entry = "#555555"
    color_fondo_boton = "#555555"
    color_fg_text = "#EEEEEE"
    color_fg_entry = "#FFFFFF"
    color_fg_boton = "#FFFFFF"
    color_menu_bg = "#3C3C3C"
    color_menu_fg = "#FFFFFF"

    # -------------------- Ventana principal --------------------
    try:
        main.config(bg=color_fondo_ventana)
    except Exception:
        pass

    # -------------------- Top Frame ----------------------------
    try:
        top_frame.config(bg=color_fondo_frame)
    except Exception:
        pass
    try:
        style.configure("entry.TEntry", fieldbackground=color_fondo_entry, foreground=color_fg_entry)
    except Exception:
        pass
    try:
        style.configure("button.TButton", background=color_fondo_boton, foreground=color_fg_boton)
        style.map("button.TButton",
                  background=[("active", "#666666")],
                  foreground=[("active", color_fg_boton)])
    except Exception:
        pass

    # -------------------- Content Frame ------------------------
    try:
        content_frame.config(bg=color_fondo_frame)
    except Exception:
        pass
    try:
        sidebar.config(bg=color_fondo_sidebar)
    except Exception:
        pass
    try:
        entry1.config(bg=color_fondo_entry, fg=color_fg_entry)
    except Exception:
        pass
    try:
        main_area.config(bg=color_fondo_frame)
    except Exception:
        pass
    try:
        area_contenido.config(bg=color_fondo_text, fg=color_fg_text)
    except Exception:
        pass

    # -------------------- Bottom Bar ---------------------------
    try:
        bottom_bar.config(bg=color_fondo_frame)
    except Exception:
        pass

    # -------------------- Botones bottom bar -------------------
    #for boton in [boton_editar_archivo, boton_guardar_archivo, boton_guardar_comonuevo]:
        #try:
            #boton.config(style="button.TButton")
        #except Exception:
            #pass

    # -------------------- Menus -------------------------------
    for w in [menu, menu_btn]:
        try:
            w.config(bg=color_menu_bg, fg=color_menu_fg)
        except Exception:
            pass

def Modo_Claro():
    # Colores originales
    color_fondo_ventana = "#E4E2E2"
    color_fondo_frame = "#E4E2E2"
    color_fondo_sidebar = "#EDECEC"
    color_fondo_text = "#FFFFFF"
    color_fondo_entry = "#FFFFFF"
    color_fondo_boton = "#FFFFFF"
    color_fg_text = "#000000"
    color_fg_entry = "#000000"
    color_fg_boton = "#000000"
    color_menu_bg = "#E4E2E2"
    color_menu_fg = "#000000"

    # -------------------- Ventana principal --------------------
    try:
        main.config(bg=color_fondo_ventana)
    except Exception:
        pass

    # -------------------- Top Frame ----------------------------
    try:
        top_frame.config(bg=color_fondo_frame)
    except Exception:
        pass
    try:
        style.configure("entry.TEntry", fieldbackground=color_fondo_entry, foreground=color_fg_entry)
    except Exception:
        pass
    try:
        style.configure("button.TButton", background=color_fondo_boton, foreground=color_fg_boton)
        style.map("button.TButton",
                  background=[("active", "#E4E2E2")],
                  foreground=[("active", color_fg_boton)])
    except Exception:
        pass

    # -------------------- Content Frame ------------------------
    try:
        content_frame.config(bg=color_fondo_frame)
    except Exception:
        pass
    try:
        sidebar.config(bg=color_fondo_sidebar)
    except Exception:
        pass
    try:
        entry1.config(bg=color_fondo_entry, fg=color_fg_entry)
    except Exception:
        pass
    try:
        main_area.config(bg=color_fondo_frame)
    except Exception:
        pass
    try:
        area_contenido.config(bg=color_fondo_text, fg=color_fg_text)
    except Exception:
        pass

    # -------------------- Bottom Bar ---------------------------
    try:
        bottom_bar.config(bg=color_fondo_frame)
    except Exception:
        pass

    # -------------------- Botones bottom bar -------------------
    #for boton in [boton_editar_archivo, boton_guardar_archivo, boton_guardar_comonuevo]:
        #try:
            #boton.config(style="button.TButton")
        #except Exception:
            #pass

    # -------------------- Menus -------------------------------
    for w in [menu, menu_btn]:
        try:
            w.config(bg=color_menu_bg, fg=color_menu_fg)
        except Exception:
            pass


menu_btn = ttk.Menubutton(bottom_bar, text="Ajustes", style="Custom.TMenubutton")
menu_btn.pack(side="right", padx=5)

menu = tk.Menu(menu_btn, tearoff=0)
menu.add_command(label="Modo Oscuro", command=Modo_Oscuro)
menu.add_command(label="Modo Claro", command=Modo_Claro)

menu_btn["menu"] = menu
main.protocol("WM_DELETE_WINDOW", cerrado)
main.mainloop()