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


# ╔══════════════════════════════════════════════════════════════════╗
# ║                        CLASE PESTAÑA                            ║
# ╚══════════════════════════════════════════════════════════════════╝

class Pestaña:
    """
    Encapsula todo el estado y los widgets de una pestaña individual.
    Cada instancia tiene su propio area_contenido, BarraBusqueda e Historial,
    por lo que navegan de forma completamente independiente.
    """

    def __init__(self, notebook, style, buttons_frame_global, menu_savedurl, menu_historial_global):
        self.notebook              = notebook
        self.style                 = style
        self.historial             = Historial()

        # ── Frame raíz de la pestaña (va dentro del Notebook) ────────
        self.frame = tk.Frame(notebook, bg="#EDECEC")
        self.frame.columnconfigure(0, weight=0)
        self.frame.columnconfigure(1, weight=1)
        self.frame.rowconfigure(0, weight=0)   # barra de búsqueda
        self.frame.rowconfigure(1, weight=1)   # contenido
        self.frame.rowconfigure(2, weight=0)   # estado
        self.frame.rowconfigure(3, weight=0)   # progreso

        # ── Sidebar ───────────────────────────────────────────────────
        self.sidebar = tk.Frame(self.frame, bg="#EDECEC", width=150)
        self.sidebar.grid(row=1, column=0, sticky="ns", padx=(0, 10))
        self.sidebar.grid_propagate(False)
        self.sidebar.rowconfigure(0, weight=1)
        self.sidebar.rowconfigure(1, weight=0)

        style.configure("entry1.TEntry", fieldbackground="#fff", foreground="#000")
        self.entry1 = ttk.Entry(self.sidebar, style="entry1.TEntry")
        self.entry1.grid(row=1, column=0, sticky="ew", padx=5, pady=5)

        # ── Área principal ────────────────────────────────────────────
        self.main_area = tk.Frame(self.frame, bg="#FFFFFF")
        self.main_area.grid(row=1, column=1, sticky="nsew")

        self.area_contenido = tk.Text(self.main_area, state="disabled")
        self.area_contenido.pack(expand=True, fill="both", padx=20, pady=10)

        # ── Botones locales de la pestaña ─────────────────────────────
        self.boton_editar       = ttk.Button(buttons_frame_global, text="Editar Archivo",     command=self._editar_archivo)
        self.boton_guardar      = ttk.Button(buttons_frame_global, text="Guardar Cambios",    command=self._guardar_archivo)
        self.boton_guardar_como = ttk.Button(buttons_frame_global, text="Guardar Como Nuevo", command=self._guardar_como)
        for b in (self.boton_editar, self.boton_guardar, self.boton_guardar_como):
            b.config(state="disabled")

        # ── Botón Favorito ────────────────────────────────────────────
        self.fav_btn = ttk.Button(
            buttons_frame_global, text="Añadir URL Favorito",
            command=lambda: self._añadir_fav(menu_savedurl)
        )
        self.fav_btn.config(state="disabled")

        # ── Barra de búsqueda propia ──────────────────────────────────
        self.barra = BarraBusqueda(
            parent=self.frame,
            style=style,
            area_contenido=self.area_contenido,
            botones_habilitar=[self.boton_guardar, self.boton_guardar_como],
            boton_editar=self.boton_editar,
            botones_requieren_texto=[self.fav_btn],
            botones_solo_local=[self.boton_editar, self.boton_guardar, self.boton_guardar_como],
            guardar_historial=self._guardar_menuhistorial,
        )
        self.barra.on_titulo_cambio = self._actualizar_titulo_tab

        # Colocar la barra en el grid de la pestaña
        self.barra.top_frame.grid(in_=self.frame, row=0, column=0, columnspan=2, sticky="ew", padx=10, pady=5)
        self.barra.estado_label.grid(row=2, column=0, columnspan=2, sticky="ew")
        self.barra.progress.grid(row=3, column=0, columnspan=2, padx=5, pady=5, sticky="ew")

        # Callback de historial global
        self._menu_historial_global = menu_historial_global

    # ── Título de la pestaña ──────────────────────────────────────────
    def _actualizar_titulo_tab(self, titulo: str):
        try:
            self.notebook.tab(self.frame, text=titulo)
        except Exception:
            pass

    # ── Historial propio ──────────────────────────────────────────────
    def _guardar_menuhistorial(self):
        urlactual = self.barra.entrada_var.get().strip()
        if not urlactual:
            return
        self.historial.agregar_historial(urlactual)
        if self._menu_historial_global is not None:
            self._menu_historial_global()

    # ── Acciones de botones ───────────────────────────────────────────
    def _editar_archivo(self):
        respuesta = messagebox.askyesno("Editar", "¿Deseas editar este documento?")
        if respuesta:
            self.area_contenido.config(state="normal")
        else:
            self.area_contenido.config(state="disabled")

    def _guardar_archivo(self, ruta_destino=None):
        ruta = ruta_destino or self.barra.get_ruta_actual()
        if not ruta:
            messagebox.showwarning("Atención", "No hay un archivo abierto")
            return
        try:
            self.area_contenido.config(state="normal")
            contenido = self.area_contenido.get("1.0", "end-1c")
            self.area_contenido.config(state="disabled")
            with open(ruta, "w", encoding="utf-8") as archivo:
                archivo.write(contenido)
            messagebox.showinfo("Éxito", "Archivo guardado correctamente")
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo guardar:\n{e}")

    def _guardar_como(self):
        ruta = filedialog.asksaveasfilename(
            defaultextension=".*",
            filetypes=[("Todos los archivos", "*.*")]
        )
        if not ruta:
            return
        self._guardar_archivo(ruta)

    def _añadir_fav(self, menu_savedurl):
        urlactual = self.barra.entrada_var.get().strip()
        if not urlactual:
            return
        try:
            cantidad = menu_savedurl.index("end") + 1
            for i in range(cantidad):
                if menu_savedurl.entrycget(i, "label") == urlactual:
                    messagebox.showwarning("Aviso", "Esta URL ya está en favoritos")
                    return
        except Exception:
            cantidad = 0
        if cantidad < 10:
            menu_savedurl.add_command(
                label=urlactual,
                command=lambda url=urlactual: self._cargar_url_global(url)
            )
        else:
            messagebox.showerror("Error", "No puede tener más de 10 URL Favoritas")

    def _cargar_url_global(self, url):
        """Sobreescrito por VentanaPrincipal para delegar al gestor."""
        pass

    # ── Mostrar / ocultar botones propios ─────────────────────────────
    def mostrar_botones(self):
        for b in (self.boton_editar, self.boton_guardar, self.boton_guardar_como, self.fav_btn):
            b.pack(side="left", padx=3)

    def ocultar_botones(self):
        for b in (self.boton_editar, self.boton_guardar, self.boton_guardar_como, self.fav_btn):
            b.pack_forget()

    # ── Temas ─────────────────────────────────────────────────────────
    def actualizar_tema(self, oscuro: bool):
        if oscuro:
            self.frame.config(bg="#2E2E2E")
            self.sidebar.config(bg="#444444")
            self.main_area.config(bg="#3C3C3C")
            self.area_contenido.config(bg="#1E1E1E", fg="#EEEEEE")
            self.barra.actualizar_tema(
                bg_frame="#2E2E2E",
                bg_entry="#555555", fg_entry="#FFFFFF",
                bg_boton="#555555", fg_boton="#FFFFFF",
                active_bg="#666666"
            )
        else:
            self.frame.config(bg="#EDECEC")
            self.sidebar.config(bg="#EDECEC")
            self.main_area.config(bg="#FFFFFF")
            self.area_contenido.config(bg="#FFFFFF", fg="#000000")
            self.barra.actualizar_tema(
                bg_frame="#E4E2E2",
                bg_entry="#FFFFFF", fg_entry="#000000",
                bg_boton="#FFFFFF", fg_boton="#000000",
                active_bg="#E4E2E2"
            )


# ╔══════════════════════════════════════════════════════════════════╗
# ║                     CLASE GESTORPESTAÑAS                        ║
# ╚══════════════════════════════════════════════════════════════════╝

class GestorPestañas:
    """
    Administra la colección de pestañas dentro del ttk.Notebook.
    """

    def __init__(self, notebook, style, buttons_frame, menu_savedurl):
        self.notebook       = notebook
        self.style          = style
        self.buttons_frame  = buttons_frame
        self.menu_savedurl  = menu_savedurl
        self.pestañas: list[Pestaña] = []
        self._tema_oscuro   = False

        self._menu_historial_ref = None

        self.notebook.bind("<<NotebookTabChanged>>", self._on_tab_changed)

    def set_menu_historial_callback(self, cb):
        self._menu_historial_ref = cb

    def _actualizar_historial_global(self):
        pestaña = self.pestaña_activa()
        if not pestaña:
            return
        url = pestaña.barra.entrada_var.get().strip()
        if url:
            self._historial_global.agregar_historial(url)
        if self._menu_historial_ref:
            self._menu_historial_ref()

    def nueva_pestaña(self, titulo="Nueva pestaña"):
        p = Pestaña(
            notebook=self.notebook,
            style=self.style,
            buttons_frame_global=self.buttons_frame,
            menu_savedurl=self.menu_savedurl,
            menu_historial_global=self._menu_historial_ref,
        )
        p.actualizar_tema(self._tema_oscuro)
        self.pestañas.append(p)
        self.notebook.add(p.frame, text=titulo)
        self.notebook.select(p.frame)

    def cerrar_pestaña_activa(self):
        if len(self.pestañas) <= 1:
            messagebox.showinfo("Aviso", "Debe quedar al menos una pestaña abierta")
            return
        p = self.pestaña_activa()
        if p is None:
            return
        p.ocultar_botones()
        # Oculta botones de la pestaña
        p.ocultar_botones()

        # Detener posibles animaciones/progreso
        try:
            p.barra.progress.stop()
        except:
            pass

        # Limpiar contenido del área de texto
        try:
            p.area_contenido.config(state="normal")
            p.area_contenido.delete("1.0", "end")
            p.area_contenido.config(state="disabled")
        except:
            pass

        # Eliminar widgets visuales
        p.frame.destroy()

        # Limpiar referencias importantes
        p.historial = None
        p.barra = None
        p.area_contenido = None

        # Sacar de la lista interna
        self.pestañas.remove(p)

    def pestaña_activa(self):
        try:
            frame_id = self.notebook.select()
            return next((p for p in self.pestañas if str(p.frame) == frame_id), None)
        except Exception:
            return None

    def _on_tab_changed(self, event=None):
        for p in self.pestañas:
            p.ocultar_botones()
        activa = self.pestaña_activa()
        if activa:
            activa.mostrar_botones()
        if self._menu_historial_ref:
            self._menu_historial_ref()

    def cargar_url_en_activa(self, url: str):
        p = self.pestaña_activa()
        if p is None:
            return
        p.barra.entrada_var.set(url)
        p.barra.iniciar_busqueda()

    def actualizar_tema_todas(self, oscuro: bool):
        self._tema_oscuro = oscuro
        for p in self.pestañas:
            p.actualizar_tema(oscuro)


# ╔══════════════════════════════════════════════════════════════════╗
# ║                      CLASE VENTANA PRINCIPAL                    ║
# ╚══════════════════════════════════════════════════════════════════╝

class VentanaPrincipal:
    def __init__(self):
        self.main = tk.Tk()
        self._configurar_ventana()
        self._configurar_estilos()
        self._construir_layout()
        self._construir_menu_savedurl()
        self._construir_gestor()
        self._construir_historial()
        self._construir_botones_pestañas()
        self._construir_ajustes()
        self._cargar_urls_default()
        self._abrir_primera_pestaña()
        self._configurar_cierre()
        self.main.mainloop()

    # ── Configuración de ventana ──────────────────────────────────────
    def _configurar_ventana(self):
        self.main.title("GO FILE EXPLORER")
        self.main.config(bg="#E4E2E2")
        self.main.minsize(600, 400)
        self.main.resizable(True, True)

        sistema = platform.system()
        margen  = 10
        self.main.update_idletasks()

        ancho_monitor = self.main.winfo_screenwidth()
        alto_monitor  = self.main.winfo_screenheight()
        ancho = ancho_monitor - 2 * margen
        alto  = alto_monitor  - 2 * margen

        if sistema == "Windows":
            self.main.state("zoomed")
        else:
            self.main.geometry(f"{ancho}x{alto}+{margen}+{margen}")

    def _configurar_estilos(self):
        self.style = ttk.Style(self.main)
        self.style.theme_use("clam")

    # ── Layout ────────────────────────────────────────────────────────
    def _construir_layout(self):
        self.main.columnconfigure(0, weight=1)
        self.main.rowconfigure(0, weight=0)   # top bar
        self.main.rowconfigure(1, weight=1)   # notebook

        self.top_bar = tk.Frame(self.main, bg="#E4E2E2")
        self.top_bar.grid(row=0, column=0, sticky="ew", padx=10, pady=5)
        self.top_bar.columnconfigure(0, weight=1)

        self.buttons_frame = tk.Frame(self.top_bar, bg="#E4E2E2")
        self.buttons_frame.grid(row=0, column=0, sticky="e", pady=(3, 0))

        self.notebook = ttk.Notebook(self.main)
        self.notebook.grid(row=1, column=0, sticky="nsew", padx=10, pady=5)

    # ── Menú URL Guardadas ────────────────────────────────────────────
    def _construir_menu_savedurl(self):
        self.savedurl_btn  = ttk.Menubutton(self.buttons_frame, text="URL Guardadas", style="Custom.TMenubutton")
        self.menu_savedurl = tk.Menu(self.savedurl_btn, tearoff=0)
        self.savedurl_btn["menu"] = self.menu_savedurl
        self.savedurl_btn.pack(side="left", padx=3)

    # ── Gestor de pestañas ────────────────────────────────────────────
    def _construir_gestor(self):
        self.gestor = GestorPestañas(
            self.notebook, self.style, self.buttons_frame, self.menu_savedurl
        )
        # Conectar favoritos de cada Pestaña al gestor
        Pestaña._cargar_url_global = lambda p, url: self.gestor.cargar_url_en_activa(url)

    # ── Historial global ──────────────────────────────────────────────
    def _construir_historial(self):
        self.boton_historial = ttk.Menubutton(self.buttons_frame, text="Historial", style="Custom.TMenubutton")
        self.menu_historial  = tk.Menu(self.boton_historial, tearoff=0)
        self.boton_historial["menu"] = self.menu_historial
        self.boton_historial.pack(side="left", padx=4)

        self.gestor.set_menu_historial_callback(self._actualizar_menu_historial)

    def _actualizar_menu_historial(self):
        self.menu_historial.delete(0, "end")
        pestaña=self.gestor.pestaña_activa()
        indice = 0
        while True:
            url = pestaña.historial.obtener_url(indice) 
            if url is None:
                break
            self.menu_historial.add_command(
                label=url,
                command=lambda u=url: self.gestor.cargar_url_en_activa(u)
            )
            indice += 1

    # ── Botones Nueva / Cerrar pestaña ────────────────────────────────
    def _construir_botones_pestañas(self):
        self.btn_nueva_tab  = ttk.Button(self.buttons_frame, text="＋ Nueva pestaña", command=self.gestor.nueva_pestaña)
        self.btn_cerrar_tab = ttk.Button(self.buttons_frame, text="✕ Cerrar pestaña", command=self.gestor.cerrar_pestaña_activa)
        self.btn_nueva_tab.pack(side="left", padx=3)
        self.btn_cerrar_tab.pack(side="left", padx=3)

    # ── Ajustes ───────────────────────────────────────────────────────
    def _construir_ajustes(self):
        self.menu_btn        = ttk.Menubutton(self.buttons_frame, text="Ajustes", style="Custom.TMenubutton")
        self.menu_contextual = tk.Menu(self.menu_btn, tearoff=0)
        self.menu_btn["menu"] = self.menu_contextual
        self.menu_btn.pack(side="left", padx=3)

        self.menu_contextual.add_command(label="Modo Oscuro", command=self._modo_oscuro)
        self.menu_contextual.add_command(label="Modo Claro",  command=self._modo_claro)

    def _modo_oscuro(self):
        self.main.config(bg="#2E2E2E")
        self.top_bar.config(bg="#2E2E2E")
        self.buttons_frame.config(bg="#2E2E2E")
        self.gestor.actualizar_tema_todas(oscuro=True)
        for w in (self.menu_contextual, self.menu_btn):
            try:
                w.config(bg="#3C3C3C", fg="#FFFFFF")
            except Exception:
                pass

    def _modo_claro(self):
        self.main.config(bg="#E4E2E2")
        self.top_bar.config(bg="#E4E2E2")
        self.buttons_frame.config(bg="#E4E2E2")
        self.gestor.actualizar_tema_todas(oscuro=False)
        for w in (self.menu_contextual, self.menu_btn):
            try:
                w.config(bg="#E4E2E2", fg="#000000")
            except Exception:
                pass

    # ── URLs por defecto ──────────────────────────────────────────────
    def _cargar_urls_default(self):
        urls_default = [
            "https://example.com",
            "https://example.org",
            "https://example.net",
            "https://httpbin.org/get",
            "https://www.iana.org/domains/reserved",
            "https://info.cern.ch",
            "https://text.npr.org",
            "https://www.utalca.cl",
        ]
        for url in urls_default:
            try:
                cantidad = self.menu_savedurl.index("end") + 1
            except Exception:
                cantidad = 0
            ya_existe = False
            for i in range(cantidad):
                if self.menu_savedurl.entrycget(i, "label") == url:
                    ya_existe = True
                    break
            if not ya_existe and cantidad < 10:
                self.menu_savedurl.add_command(
                    label=url,
                    command=lambda u=url: self.gestor.cargar_url_en_activa(u)
                )

    # ── Primera pestaña ───────────────────────────────────────────────
    def _abrir_primera_pestaña(self):
        self.gestor.nueva_pestaña("Nueva pestaña")

    # ── Cierre ────────────────────────────────────────────────────────
    def _configurar_cierre(self):
        self.main.protocol("WM_DELETE_WINDOW", self._cerrar)

    def _cerrar(self):
        if messagebox.askokcancel("Salir", "¿Seguro que quieres cerrar el navegador?"):
            self.main.destroy()


# ╔══════════════════════════════════════════════════════════════════╗
# ║                       PUNTO DE ENTRADA                          ║
# ╚══════════════════════════════════════════════════════════════════╝

if __name__ == "__main__":
    VentanaPrincipal()