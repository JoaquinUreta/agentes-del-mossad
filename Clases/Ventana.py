import os
import tkinter as tk
from tkinter import SUNKEN, ttk
import platform
from tkinter import messagebox
from tkinter import filedialog
from Renderizador import RenderizadorParser
from BarraBusqueda import BarraBusqueda
from Historial import Historial

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

main = tk.Tk()
main.title("GO FILE EXPLORER")
main.config(bg="#E4E2E2")

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
historial=Historial()

# ===================== Style =====================
style = ttk.Style(main)
style.theme_use("clam")

# ===================== GRID PRINCIPAL =====================
main.columnconfigure(0, weight=1)
main.rowconfigure(0, weight=0)   # barra de búsqueda + botones
main.rowconfigure(1, weight=1)   # contenido
main.rowconfigure(2, weight=0)   # estado / progreso

# ===================== TOP BAR (búsqueda + botones) =====================
top_bar = tk.Frame(main, bg="#E4E2E2")
top_bar.grid(row=0, column=0, sticky="ew", padx=10, pady=5)
top_bar.columnconfigure(0, weight=1)

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

area_contenido = tk.Text(main_area, state="disabled")
area_contenido.pack(expand=True, fill="both", padx=20, pady=10)

# ===================== FRAME DE BOTONES =====================
buttons_frame = tk.Frame(top_bar, bg="#E4E2E2")
buttons_frame.grid(row=1, column=0, sticky="e", pady=(3, 0))

# ===================== Boton Editar Archivo =====================
def Editar_Archivo():
    respuesta = messagebox.askyesno("Editar", "¿Deseas editar este documento?")
    if respuesta:
        area_contenido.config(state="normal")
    else:
        area_contenido.config(state="disabled")

boton_editar_archivo = ttk.Button(buttons_frame, text="Editar Archivo", command=Editar_Archivo)
boton_editar_archivo.config(state="disabled")
boton_editar_archivo.pack(side="left", padx=3)

# ===================== Boton Guardar Cambios =====================
def guardar_archivo(ruta_destino=None):
    ruta = ruta_destino or barra.get_ruta_actual()
    if not ruta:
        messagebox.showwarning("Atención", "No hay un archivo abierto")
        return
    try:
        area_contenido.config(state="normal")
        contenido = area_contenido.get("1.0", "end-1c")
        area_contenido.config(state="disabled")
        with open(ruta, "w", encoding="utf-8") as archivo:
            archivo.write(contenido)
        messagebox.showinfo("Éxito", "Archivo guardado correctamente")
    except Exception as e:
        messagebox.showerror("Error", f"No se pudo guardar:\n{e}")

boton_guardar_archivo = ttk.Button(buttons_frame, text="Guardar Cambios", command=guardar_archivo)
boton_guardar_archivo.config(state="disabled")
boton_guardar_archivo.pack(side="left", padx=3)

# ===================== Guardar Como Nuevo =====================
def guardar_como():
    ruta = filedialog.asksaveasfilename(
        defaultextension=".*",
        filetypes=[("Todos los archivos", "*.*")]
    )
    if not ruta:
        return
    guardar_archivo(ruta)

boton_guardar_comonuevo = ttk.Button(buttons_frame, text="Guardar Como Nuevo", command=guardar_como)
boton_guardar_comonuevo.config(state="disabled")
boton_guardar_comonuevo.pack(side="left", padx=3)

# ===================== AJUSTES =====================
menu_btn = ttk.Menubutton(buttons_frame, text="Ajustes", style="Custom.TMenubutton")
menu_btn.pack(side="left", padx=3)

menu_contextual = tk.Menu(menu_btn, tearoff=0)
menu_btn["menu"] = menu_contextual

# ===================== MODOS OSCURO / CLARO =====================
def Modo_Oscuro():
    main.config(bg="#2E2E2E")
    top_bar.config(bg="#2E2E2E")
    buttons_frame.config(bg="#2E2E2E")
    content_frame.config(bg="#3C3C3C")
    sidebar.config(bg="#444444")
    main_area.config(bg="#3C3C3C")
    area_contenido.config(bg="#1E1E1E", fg="#EEEEEE")
    barra.actualizar_tema(
        bg_frame="#2E2E2E",
        bg_entry="#555555", fg_entry="#FFFFFF",
        bg_boton="#555555", fg_boton="#FFFFFF",
        active_bg="#666666"
    )
    for w in [menu_contextual, menu_btn]:
        try:
            w.config(bg="#3C3C3C", fg="#FFFFFF")
        except Exception:
            pass

def Modo_Claro():
    main.config(bg="#E4E2E2")
    top_bar.config(bg="#E4E2E2")
    buttons_frame.config(bg="#E4E2E2")
    content_frame.config(bg="#E4E2E2")
    sidebar.config(bg="#EDECEC")
    main_area.config(bg="#E4E2E2")
    area_contenido.config(bg="#FFFFFF", fg="#000000")
    barra.actualizar_tema(
        bg_frame="#E4E2E2",
        bg_entry="#FFFFFF", fg_entry="#000000",
        bg_boton="#FFFFFF", fg_boton="#000000",
        active_bg="#E4E2E2"
    )
    for w in [menu_contextual, menu_btn]:
        try:
            w.config(bg="#E4E2E2", fg="#000000")
        except Exception:
            pass

menu_contextual.add_command(label="Modo Oscuro", command=Modo_Oscuro)
menu_contextual.add_command(label="Modo Claro",  command=Modo_Claro)

# ===================== MARCAR FAV =====================
def cargar_url(url):
    barra.entrada_var.set(url)
    barra.iniciar_busqueda()
    guardar_menuhistorial()

def AñadirFav():
    urlactual = barra.entrada_var.get().strip()
    if not urlactual:
        return

    # Revisar duplicados
    try:
        cantidad = menu_savedurl.index("end") + 1
        for i in range(cantidad):
            if menu_savedurl.entrycget(i, "label") == urlactual:
                messagebox.showwarning("Aviso", "Esta URL ya está en favoritos")
                return
    except:
        cantidad = 0

    if cantidad < 10:
        menu_savedurl.add_command(label=urlactual,
                                  command=lambda url=urlactual: cargar_url(url))
    else:
        messagebox.showerror("Error", "No puede tener más de 10 URL Favoritas")

fav_btn = ttk.Button(buttons_frame, text="Añadir URL Favorito", command=AñadirFav)
fav_btn.config(state="disabled")
fav_btn.pack(side="left", padx=3)

# ===================== URL GUARDADAS =====================
savedurl_btn = ttk.Menubutton(buttons_frame, text="URL Guardadas", style="Custom.TMenubutton")
savedurl_btn.pack(side="left", padx=3)

menu_savedurl = tk.Menu(savedurl_btn, tearoff=0)
savedurl_btn["menu"] = menu_savedurl

#====== Historial Guardado =========================
def guardar_menuhistorial():#Guardar url usando clase Historal
    urlactual = barra.entrada_var.get().strip()
    if not urlactual:
        return
    historial.agregar_historial(urlactual)
    actualizar_historial()

def actualizar_historial():#Actualiza menu del boton Historial
 menu_historial.delete(0,"end")
 indice=0
 while True:
     url=historial.obtener_url(indice)
     if url is None:
         break
     menu_historial.add_command(label=url,command=lambda u=url:cargar_url(u))
     indice+=1

#=========== Boton Historial =================================
boton_historial= ttk.Menubutton(buttons_frame, text="Historial", style="Custom.TMenubutton")
boton_historial.pack(side="left", padx=4)
menu_historial=tk.Menu(boton_historial,tearoff=0)
boton_historial["menu"] = menu_historial

# ===================== BARRA DE BÚSQUEDA =====================
barra = BarraBusqueda(
    parent=main,
    style=style,
    area_contenido=area_contenido,
    botones_habilitar=[boton_guardar_archivo, boton_guardar_comonuevo],
    boton_editar=boton_editar_archivo,
    botones_requieren_texto=[fav_btn],
    botones_solo_local=[boton_editar_archivo, boton_guardar_archivo, boton_guardar_comonuevo],
    guardar_historial=guardar_menuhistorial
)
barra.top_frame.grid(in_=top_bar, row=0, column=0, sticky="ew")

# Completar referencias en la barra de búsqueda
barra.botones_habilitar = [boton_guardar_archivo, boton_guardar_comonuevo]
barra.boton_editar = boton_editar_archivo

# ===================== ESTADO / PROGRESO (fila 2) =====================
barra.estado_label.grid(row=2, column=0, sticky="ew")
barra.progress.grid(row=3, column=0, padx=5, pady=5, sticky="ew")

# ===================== CIERRE =====================
def cerrado():
    if messagebox.askokcancel("Salir", "¿Seguro que quieres cerrar el navegador?"):
        main.destroy()

main.protocol("WM_DELETE_WINDOW", cerrado)
main.mainloop()