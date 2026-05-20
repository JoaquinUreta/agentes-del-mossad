import os
import tkinter as tk
from tkinter import SUNKEN, ttk
import platform
from tkinter import messagebox
from tkinter import filedialog
from Renderizador import RenderizadorParser
from BarraBusqueda import BarraBusqueda
from Historial import Historial
from Pestaña import Pestaña, GestorPestañas

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

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

if __name__ == "__main__":
    VentanaPrincipal()