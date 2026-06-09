import os
import json
import tkinter as tk
from tkinter import SUNKEN, ttk
import platform
from tkinter import messagebox
from tkinter import filedialog
from Renderizador import RenderizadorParser
from BarraBusqueda import BarraBusqueda
from Historial import Historial
from Pestaña import Pestaña, GestorPestañas

BASE_DIR      = os.path.dirname(os.path.abspath(__file__))
FAVS_FILE     = os.path.join(BASE_DIR, "favoritos.json")
HISTORIAL_FILE    = os.path.join(BASE_DIR, "historial.json")
MAX_FAVORITOS = 10

# ─────────────────────────────────────────────
#  PALETAS
# ─────────────────────────────────────────────
DARK = {
    "bg":       "#0F0E0D",
    "surface":  "#1A1916",
    "border":   "#2E2C29",
    "accent":   "#D4A843",
    "accent2":  "#8C6A1F",
    "text":     "#E8E4DC",
    "text_dim": "#6B6760",
    "topbar":   "#141310",
}

LIGHT = {
    "bg":       "#F5F2EC",
    "surface":  "#FFFFFF",
    "border":   "#D6D0C4",
    "accent":   "#A0742A",
    "accent2":  "#7A5520",
    "text":     "#1A1714",
    "text_dim": "#9A9186",
    "topbar":   "#E8E2D8",
}

FONT_TITLE = ("Courier New", 38, "bold")
FONT_SMALL = ("Courier New",  9)
FONT_ENTRY = ("Courier New", 11)
FONT_ICON  = ("Segoe UI Symbol", 14)


# ─────────────────────────────────────────────
#  CLASE VENTANA
# ─────────────────────────────────────────────
class Ventana:
    def __init__(self):
        self.sistema      = platform.system()
        self.is_dark      = True
        self.theme        = LIGHT

        # ── Estado de favoritos (persistente en JSON) ─────────────────
        self.favoritos: list[str] = self._cargar_favoritos()
        
        # ── Historial global (Inicializado con los datos persistidos) ──
        self.historial_global = Historial(limitante=10)
        historial_cargado = self._cargar_historial()
        
        # Poblamos el objeto Historial respetando el orden correcto
        for url in reversed(historial_cargado):
            self.historial_global.agregar_historial(url)

        # ── Visibilidad del panel lateral ─────────────────────────────
        self._panel_visible = False

        self._build_window()
        self._build_topbar()
        self._build_content()
        self._build_panel()
        self._build_statusbar()
        self._apply_theme()
        self._bind_events()

        # Volcar el historial inicial en el Listbox visual
        self._refrescar_listbox_historial()

        self.root.protocol("WM_DELETE_WINDOW", self._cerrado)
        self.root.mainloop()

    # ─────────────────────────────────────────
    #  VENTANA RAÍZ
    # ─────────────────────────────────────────
    def _build_window(self):
        self.root = tk.Tk()
        self.root.title("GOFILEXPLORER")

        margen = 10
        self.root.update_idletasks()
        ancho = self.root.winfo_screenwidth()  - 2 * margen
        alto  = self.root.winfo_screenheight() - 2 * margen

        if self.sistema == "Windows":
            self.root.state("zoomed")
        else:
            self.root.geometry(f"{ancho}x{alto}+{margen}+{margen}")

        self.root.minsize(640, 420)
        self.root.resizable(True, True)

        # columna 0 = contenido principal  |  columna 1 = panel lateral (peso 0 = ancho fijo)
        self.root.columnconfigure(0, weight=1)
        self.root.columnconfigure(1, weight=0)
        self.root.rowconfigure(0, weight=0)   # top bar
        self.root.rowconfigure(1, weight=1)   # contenido + panel
        self.root.rowconfigure(2, weight=0)   # status bar

    # ─────────────────────────────────────────
    #  TOP BAR
    # ─────────────────────────────────────────
    def _build_topbar(self):
        """
        Barra superior completamente funcional:
          logo | ◀ ▶ ⟳ | [barra URL] | IR | ★ | ＋ ✕ | ◑ | ☰
        """
        self.top_bar = tk.Frame(self.root, height=52)
        self.top_bar.grid(row=0, column=0, columnspan=2, sticky="ew")
        self.top_bar.grid_propagate(False)
        self.top_bar.columnconfigure(4, weight=1)   # col 4 = barra URL, se expande

        self.accent_line = tk.Frame(self.top_bar, height=2)
        self.accent_line.place(relx=0, rely=1.0, relwidth=1.0, anchor="sw")

        # ── Logo ─────────────────────────────────────────────────────
        self.logo_top = tk.Label(
            self.top_bar, text="GO/",
            font=("Courier New", 16, "bold"), padx=10,
            cursor="hand2",
        )
        self.logo_top.grid(row=0, column=0, pady=10, sticky="w")
        self.logo_top.bind("<Button-1>", lambda e: self._volver_splash())

        # ── Botones de navegación ─────────────────────────────────────
        NAV_FONT = ("Segoe UI Symbol", 13)

        self.btn_atras = tk.Button(
            self.top_bar, text="◀", font=NAV_FONT,
            relief="flat", cursor="hand2", bd=0, padx=6,
            state="disabled", command=self._navegar_atras,
        )
        self.btn_atras.grid(row=0, column=1, pady=10)

        self.btn_adelante = tk.Button(
            self.top_bar, text="▶", font=NAV_FONT,
            relief="flat", cursor="hand2", bd=0, padx=6,
            state="disabled", command=self._navegar_adelante,
        )
        self.btn_adelante.grid(row=0, column=2, pady=10)

        self.btn_recargar = tk.Button(
            self.top_bar, text="⟳", font=NAV_FONT,
            relief="flat", cursor="hand2", bd=0, padx=6,
            command=self._recargar,
        )
        self.btn_recargar.grid(row=0, column=3, pady=10, padx=(0, 6))

        # ── Barra URL ─────────────────────────────────────────────────
        self.frame_url = tk.Frame(self.top_bar, highlightthickness=1)
        self.frame_url.grid(row=0, column=4, sticky="ew", pady=10, padx=(0, 6))
        self.frame_url.columnconfigure(0, weight=1)

        self.barra2_var = tk.StringVar()
        self.barra2 = tk.Entry(
            self.frame_url, textvariable=self.barra2_var,
            relief="flat", font=FONT_ENTRY, bd=0, highlightthickness=0,
        )
        self.barra2.grid(row=0, column=0, ipady=5, ipadx=8, sticky="ew")
        self.barra2.bind("<Return>",   self._url_bar_navegar)
        self.barra2.bind("<FocusIn>",  self._url_bar_select_all)
        self.barra2.bind("<FocusOut>", self._url_bar_sync)

        # ── Botón IR ──────────────────────────────────────────────────
        self.btn_ir_top = tk.Button(
            self.top_bar, text=" IR ",
            font=("Courier New", 9, "bold"),
            relief="flat", cursor="hand2", bd=0, padx=10,
            command=self._url_bar_navegar,
        )
        self.btn_ir_top.grid(row=0, column=5, pady=10, padx=(0, 4))

        # ── Favorito ──────────────────────────────────────────────────
        self.favbtn = tk.Button(
            self.top_bar, text="★", font=FONT_ICON,
            relief="flat", cursor="hand2", bd=0, padx=8,
            command=self._toggle_favorito,
        )
        self.favbtn.grid(row=0, column=6, pady=10, padx=(0, 2))

        # ── Pestañas nueva / cerrar ───────────────────────────────────
        self.btn_nueva_tab = tk.Button(
            self.top_bar, text="＋", font=("Courier New", 12, "bold"),
            relief="flat", cursor="hand2", bd=0, padx=6,
            command=self._nueva_pestaña,
        )
        self.btn_nueva_tab.grid(row=0, column=7, pady=10)

        self.btn_cerrar_tab = tk.Button(
            self.top_bar, text="✕", font=("Courier New", 10),
            relief="flat", cursor="hand2", bd=0, padx=6,
            command=self._cerrar_pestaña,
        )
        self.btn_cerrar_tab.grid(row=0, column=8, pady=10, padx=(0, 8))

        # ── Tema / Panel ──────────────────────────────────────────────
        self.mode_btn = tk.Button(
            self.top_bar, text="◑", font=FONT_ICON,
            relief="flat", cursor="hand2", bd=0, padx=8,
            command=self._toggle_modo,
        )
        self.mode_btn.grid(row=0, column=9, pady=10)

        self.panel_btn = tk.Button(
            self.top_bar, text="☰", font=FONT_ICON,
            relief="flat", cursor="hand2", bd=0, padx=8,
            command=self._toggle_panel,
        )
        self.panel_btn.grid(row=0, column=10, pady=10, padx=(0, 8))

    def _build_content(self):
        """
        Construye la zona central con dos capas superpuestas dentro de content_frame:
          - splash_frame : pantalla de inicio con título y barra de búsqueda central
          - browser_frame: franja de botones + ttk.Notebook (oculto hasta navegar)
        La transición splash → browser se hace en _activar_navegador().
        """
        self.style_ttk = ttk.Style()
        self._navegador_activo = False

        self.content_frame = tk.Frame(self.root)
        self.content_frame.grid(row=1, column=0, sticky="nsew")
        self.content_frame.columnconfigure(0, weight=1)
        self.content_frame.rowconfigure(0, weight=1)

        # ══════════════════════════════════════════
        #  SPLASH (pantalla de inicio)
        # ══════════════════════════════════════════
        self.splash_frame = tk.Frame(self.content_frame)
        self.splash_frame.grid(row=0, column=0, sticky="nsew")
        self.splash_frame.columnconfigure(0, weight=1)
        self.splash_frame.rowconfigure(0, weight=1)

        self.center_frame = tk.Frame(self.splash_frame)
        self.center_frame.place(relx=0.5, rely=0.46, anchor="center")

        # Título
        self.title_row = tk.Frame(self.center_frame)
        self.title_row.pack()
        self.lbl_go = tk.Label(self.title_row, text="GO",      font=FONT_TITLE)
        self.lbl_go.pack(side="left")
        self.lbl_fi = tk.Label(self.title_row, text="FILE",    font=FONT_TITLE)
        self.lbl_fi.pack(side="left")
        self.lbl_xl = tk.Label(self.title_row, text="XPLORER", font=FONT_TITLE)
        self.lbl_xl.pack(side="left")

        self.sep_line = tk.Frame(self.center_frame, height=2, width=420)
        self.sep_line.pack(pady=(4, 18))

        self.lbl_sub = tk.Label(
            self.center_frame,
            text="w e b   ·   l o c a l   ·   e v e r y w h e r e",
            font=("Courier New", 10),
        )
        self.lbl_sub.pack(pady=(0, 28))

        # Barra de búsqueda central de la splash
        self.search_outer = tk.Frame(self.center_frame, padx=2, pady=2)
        self.search_outer.pack(fill="x")
        self.search_inner = tk.Frame(self.search_outer)
        self.search_inner.pack(fill="x")
        self.search_inner.columnconfigure(1, weight=1)

        self.lbl_prompt = tk.Label(
            self.search_inner, text=" ›_ ",
            font=("Courier New", 13, "bold"),
        )
        self.lbl_prompt.grid(row=0, column=0, sticky="w", padx=(8, 0))

        self.barra = tk.Entry(
            self.search_inner, relief="flat",
            font=("Courier New", 13), bd=0, highlightthickness=0,
        )
        self.barra.grid(row=0, column=1, sticky="ew", ipady=10)
        self.barra.bind("<Return>", lambda e: self._ir_splash())

        self.irbtn = tk.Button(
            self.search_inner, text=" IR ",
            relief="flat", font=("Courier New", 10, "bold"),
            cursor="hand2", bd=0, padx=12, pady=10,
            command=self._ir_splash,
        )
        self.irbtn.grid(row=0, column=2)

        # Atajos rápidos (se rellenan desde fuera si se quiere)
        self.hints_row = tk.Frame(self.center_frame)
        self.hints_row.pack(pady=(14, 0))
        self.hint_btns = []

        # ══════════════════════════════════════════
        #  BROWSER (notebook + botones de acción)
        # ══════════════════════════════════════════
        self.browser_frame = tk.Frame(self.content_frame)
        # No se pone en grid todavía; lo hace _activar_navegador()
        self.browser_frame.columnconfigure(0, weight=1)
        self.browser_frame.rowconfigure(0, weight=0)
        self.browser_frame.rowconfigure(1, weight=1)

        # Franja de botones de acción
        self.buttons_frame = tk.Frame(self.browser_frame, height=32)
        self.buttons_frame.grid(row=0, column=0, sticky="ew", padx=6, pady=(4, 0))
        self.buttons_frame.grid_propagate(False)

        # Notebook
        self.notebook = ttk.Notebook(self.browser_frame)
        self.notebook.grid(row=1, column=0, sticky="nsew", padx=4, pady=(2, 0))

        # Menú de URLs guardadas (compatibilidad con Pestaña)
        self.menu_savedurl = tk.Menu(self.root, tearoff=0)

        # GestorPestañas
        self.gestor = GestorPestañas(
            notebook=self.notebook,
            style=self.style_ttk,
            buttons_frame=self.buttons_frame,
            menu_savedurl=self.menu_savedurl,
        )
        self.gestor.set_menu_historial_callback(self._on_historial_navegacion)

        # Conectar favoritos de Pestaña con el panel de Ventana
        Pestaña._cargar_url_global = lambda p, url: self.gestor.cargar_url_en_activa(url)

        # Primera pestaña (creada en background, aún oculta)
        self.gestor.nueva_pestaña("Nueva pestaña")

        # Sincronizar barra URL al cambiar pestaña
        self.notebook.bind("<<NotebookTabChanged>>", self._on_tab_changed_ventana)

    def _ir_splash(self):
        """
        Acción del botón IR de la pantalla splash.
        Transfiere el texto a la barra URL de la topbar,
        activa el modo navegador y lanza la búsqueda.
        """
        url = self.barra.get().strip()
        if not url:
            return
        self._activar_navegador()
        self.barra2_var.set(url)
        self._url_bar_navegar()

    def _activar_navegador(self):
        """
        Transición splash → navegador.
        Oculta la pantalla de inicio y muestra el Notebook.
        Se llama una sola vez; llamadas posteriores son inocuas.
        """
        if self._navegador_activo:
            return
        self._navegador_activo = True
        self.splash_frame.grid_forget()
        self.browser_frame.grid(row=0, column=0, sticky="nsew")
        
    # ─────────────────────────────────────────
    #  PANEL LATERAL (historial + favoritos)
    # ─────────────────────────────────────────
    def _build_panel(self):
        """
        Construye el panel lateral colapsable (columna 1, fila 1).
        Contiene dos secciones:
            - Historial: Listbox con las últimas visitas (todas las pestañas).
            - Favoritos: Listbox con las URLs guardadas manualmente.
        El panel arranca oculto; se muestra/oculta con _toggle_panel().
        """
        PANEL_W = 260

        # ── Frame raíz del panel ──────────────────────────────────────
        self.panel_frame = tk.Frame(self.root, width=PANEL_W)
        # No se añade al grid todavía — lo hace _toggle_panel()

        # ── Separador visual izquierdo ────────────────────────────────
        self.panel_sep = tk.Frame(self.panel_frame, width=2)
        self.panel_sep.pack(side="left", fill="y")

        # ── Contenedor interior ───────────────────────────────────────
        inner = tk.Frame(self.panel_frame)
        inner.pack(side="left", fill="both", expand=True, padx=(6, 6), pady=6)
        inner.columnconfigure(0, weight=1)

        # ── Sección HISTORIAL ─────────────────────────────────────────
        lbl_hist = tk.Label(inner, text="Historial", font=("Courier New", 9, "bold"), anchor="w")
        lbl_hist.grid(row=0, column=0, sticky="ew", pady=(4, 2))

        frame_hist = tk.Frame(inner)
        frame_hist.grid(row=1, column=0, sticky="nsew")
        frame_hist.columnconfigure(0, weight=1)
        inner.rowconfigure(1, weight=1)

        scroll_hist = ttk.Scrollbar(frame_hist, orient="vertical")
        scroll_hist.pack(side="right", fill="y")

        self.lb_historial = tk.Listbox(
            frame_hist,
            yscrollcommand=scroll_hist.set,
            selectmode="browse",
            activestyle="none",
            font=FONT_SMALL,
            bd=0,
            highlightthickness=0,
            relief="flat",
            cursor="hand2",
        )
        self.lb_historial.pack(side="left", fill="both", expand=True)
        scroll_hist.config(command=self.lb_historial.yview)

        # Botón limpiar historial
        btn_limpiar_hist = tk.Button(
            inner,
            text="Limpiar historial",
            font=FONT_SMALL,
            relief="flat",
            cursor="hand2",
            bd=0,
            pady=2,
            command=self._limpiar_historial,
        )
        btn_limpiar_hist.grid(row=2, column=0, sticky="ew", pady=(2, 6))
        self._btn_limpiar_hist = btn_limpiar_hist

        # ── Separador entre secciones ─────────────────────────────────
        sep = tk.Frame(inner, height=1)
        sep.grid(row=3, column=0, sticky="ew", pady=(0, 6))
        self._panel_sep_inner = sep

        # ── Sección FAVORITOS ─────────────────────────────────────────
        lbl_fav = tk.Label(inner, text="Favoritos", font=("Courier New", 9, "bold"), anchor="w")
        lbl_fav.grid(row=4, column=0, sticky="ew", pady=(0, 2))

        frame_fav = tk.Frame(inner)
        frame_fav.grid(row=5, column=0, sticky="nsew")
        frame_fav.columnconfigure(0, weight=1)
        inner.rowconfigure(5, weight=1)

        scroll_fav = ttk.Scrollbar(frame_fav, orient="vertical")
        scroll_fav.pack(side="right", fill="y")

        self.lb_favoritos = tk.Listbox(
            frame_fav,
            yscrollcommand=scroll_fav.set,
            selectmode="browse",
            activestyle="none",
            font=FONT_SMALL,
            bd=0,
            highlightthickness=0,
            relief="flat",
            cursor="hand2",
        )
        self.lb_favoritos.pack(side="left", fill="both", expand=True)
        scroll_fav.config(command=self.lb_favoritos.yview)

        # Botones de favoritos
        fav_btns = tk.Frame(inner)
        fav_btns.grid(row=6, column=0, sticky="ew", pady=(2, 4))
        fav_btns.columnconfigure(0, weight=1)
        fav_btns.columnconfigure(1, weight=1)

        self._btn_ir_fav = tk.Button(
            fav_btns,
            text="Ir a URL",
            font=FONT_SMALL,
            relief="flat",
            cursor="hand2",
            bd=0,
            pady=2,
            command=self._ir_a_favorito,
        )
        self._btn_ir_fav.grid(row=0, column=0, sticky="ew", padx=(0, 2))

        self._btn_quitar_fav = tk.Button(
            fav_btns,
            text="Quitar",
            font=FONT_SMALL,
            relief="flat",
            cursor="hand2",
            bd=0,
            pady=2,
            command=self._quitar_favorito,
        )
        self._btn_quitar_fav.grid(row=0, column=1, sticky="ew", padx=(2, 0))

        # Guardar referencias a labels para el tema
        self._panel_labels = [lbl_hist, lbl_fav]
        self._panel_inner   = inner

        # Poblar el listbox de favoritos con lo cargado del JSON
        self._refrescar_listbox_favoritos()

        # Doble-clic para navegar
        self.lb_historial.bind("<Double-Button-1>", lambda e: self._navegar_desde_historial())
        self.lb_favoritos.bind("<Double-Button-1>", lambda e: self._ir_a_favorito())

    # ── Visibilidad del panel ────────────────────────────────────────

    def _toggle_panel(self):
        """Muestra u oculta el panel lateral."""
        self._panel_visible = not self._panel_visible
        if self._panel_visible:
            self.panel_frame.grid(row=1, column=1, sticky="nsew", padx=(0, 0))
        else:
            self.panel_frame.grid_forget()

    # ── Persistencia de favoritos ────────────────────────────────────

    def _cargar_favoritos(self) -> list:
        """Lee favoritos.json; si no existe devuelve lista vacía."""
        if os.path.isfile(FAVS_FILE):
            try:
                with open(FAVS_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                if isinstance(data, list):
                    return [str(u) for u in data[:MAX_FAVORITOS]]
            except Exception:
                pass
        return []
    
    def _guardar_favoritos(self):
        """Escribe self.favoritos en favoritos.json."""
        try:
            with open(FAVS_FILE, "w", encoding="utf-8") as f:
                json.dump(self.favoritos, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    # ── Operaciones sobre favoritos ──────────────────────────────────

    def _refrescar_listbox_favoritos(self):
        """Sincroniza el Listbox de favoritos con self.favoritos."""
        self.lb_favoritos.delete(0, "end")
        for url in self.favoritos:
            self.lb_favoritos.insert("end", url)

    def añadir_favorito(self, url: str):
        """
        Añade una URL a la lista de favoritos si no está duplicada y
        no supera el límite de MAX_FAVORITOS. Persiste en disco.
        Se puede llamar desde fuera (ej.: botón en Pestaña).
        """
        url = url.strip()
        if not url:
            return
        if url in self.favoritos:
            messagebox.showwarning("Aviso", "Esta URL ya está en favoritos")
            return
        if len(self.favoritos) >= MAX_FAVORITOS:
            messagebox.showerror("Error", f"No puede tener más de {MAX_FAVORITOS} favoritos")
            return
        self.favoritos.append(url)
        self._guardar_favoritos()
        self._refrescar_listbox_favoritos()

    def _quitar_favorito(self):
        """Elimina el favorito seleccionado en el Listbox."""
        sel = self.lb_favoritos.curselection()
        if not sel:
            return
        idx = sel[0]
        url = self.favoritos[idx]
        if messagebox.askyesno("Confirmar", f"¿Quitar '{url}' de favoritos?"):
            self.favoritos.pop(idx)
            self._guardar_favoritos()
            self._refrescar_listbox_favoritos()

    def _ir_a_favorito(self):
        """Carga la URL del favorito seleccionado en la pestaña activa."""
        sel = self.lb_favoritos.curselection()
        if not sel:
            return
        url = self.favoritos[sel[0]]
        self._navegar_url(url)
    
    #----- Persistencia sobre historial ---------------------------------
    def _guardar_historial(self):
        try:
            with open(HISTORIAL_FILE, "w", encoding="utf-8") as f:
                # Guardamos el array interno de URLs gestionado por Historial
                json.dump(self.historial_global.historial, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    def _cargar_historial(self) -> list:
        "Lee historial.json; si no existe devuelve lista vacía."
        if os.path.isfile(HISTORIAL_FILE):
            try:
                with open(HISTORIAL_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                if isinstance(data, list):
                    return [str(u) for u in data[:MAX_FAVORITOS]]
            except Exception:
                pass
        return []
        
    # ── Operaciones sobre historial ──────────────────────────────────

    def registrar_en_historial(self, url: str):
        """
        Añade una URL al historial global y refresca el Listbox.
        Debe ser llamado por GestorPestañas / BarraBusqueda al navegar.
        """
        url = url.strip()
        if not url:
            return
        self.historial_global.agregar_historial(url)
        self._refrescar_listbox_historial()
        self._guardar_historial()

    def _refrescar_listbox_historial(self):
        """Vuelca el historial global en el Listbox (más reciente arriba)."""
        self.lb_historial.delete(0, "end")
        for i in range(self.historial_global.limite):
            entry = self.historial_global.obtener_url(i)
            if entry is None:
                break
            self.lb_historial.insert("end", entry)

    def _limpiar_historial(self):
        """Vacía el historial global previa confirmación."""
        if messagebox.askyesno("Confirmar", "¿Limpiar todo el historial?"):
            self.historial_global.historial.clear()
            self.lb_historial.delete(0, "end")
            self._guardar_historial()

    def _navegar_desde_historial(self):
        """Carga la URL del historial seleccionada en la pestaña activa."""
        sel = self.lb_historial.curselection()
        if not sel:
            return
        url = self.lb_historial.get(sel[0])
        self._navegar_url(url)

    # ── Navegación desde el panel ────────────────────────────────────

    def _navegar_url(self, url: str):
        """
        Punto de entrada para navegar a una URL desde el panel o historial.
        Activa el navegador si todavía se muestra la splash.
        """
        self._activar_navegador()
        if hasattr(self, "gestor") and self.gestor is not None:
            self.gestor.cargar_url_en_activa(url)
        else:
            self.lbl_status.config(text=f"navegando: {url}")

    # ─────────────────────────────────────────
    #  STATUS BAR
    # ─────────────────────────────────────────
    def _build_statusbar(self):
        self.status_bar = tk.Frame(self.root, height=24)
        self.status_bar.grid(row=2, column=0, sticky="ew")
        self.status_bar.grid_propagate(False)

        self.status_accent = tk.Frame(self.status_bar, width=4)
        self.status_accent.pack(side="left", fill="y")

        self.lbl_status = tk.Label(
            self.status_bar, text="listo", font=FONT_SMALL, padx=10
        )
        self.lbl_status.pack(side="left", fill="y")

        self.lbl_sistema = tk.Label(
            self.status_bar, text=f"  {self.sistema}  ", font=FONT_SMALL
        )
        self.lbl_sistema.pack(side="right", fill="y")

    # ─────────────────────────────────────────
    #  TEMA
    # ─────────────────────────────────────────
    def _apply_theme(self):
        T = self.theme
        self.root.config(bg=T["bg"])

        # top bar
        self.top_bar.config(bg=T["topbar"])
        self.accent_line.config(bg=T["accent"])
        self.logo_top.config(bg=T["topbar"], fg=T["accent"])
        self.favbtn.config(
            bg=T["topbar"], fg=T["text_dim"],
            activebackground=T["topbar"], activeforeground=T["accent"],
        )
        self.mode_btn.config(
            bg=T["topbar"], fg=T["accent"],
            activebackground=T["topbar"], activeforeground=T["text"],
        )
        self.panel_btn.config(
            bg=T["topbar"], fg=T["text_dim"],
            activebackground=T["topbar"], activeforeground=T["accent"],
        )
        for btn in (self.btn_atras, self.btn_adelante, self.btn_recargar):
            btn.config(
                bg=T["topbar"], fg=T["text_dim"],
                activebackground=T["topbar"], activeforeground=T["accent"],
                disabledforeground=T["border"],
            )
        self.frame_url.config(
            bg=T["surface"],
            highlightbackground=T["border"], highlightcolor=T["accent"],
        )
        self.barra2.config(
            bg=T["surface"], fg=T["text"],
            insertbackground=T["accent"],
        )
        self.btn_ir_top.config(
            bg=T["accent"], fg=T["bg"],
            activebackground=T["accent2"], activeforeground=T["text"],
        )
        for btn in (self.btn_nueva_tab, self.btn_cerrar_tab):
            btn.config(
                bg=T["topbar"], fg=T["text_dim"],
                activebackground=T["topbar"], activeforeground=T["accent"],
            )

        # contenido — splash
        self.content_frame.config(bg=T["bg"])
        self.splash_frame.config(bg=T["bg"])
        self.center_frame.config(bg=T["bg"])
        self.title_row.config(bg=T["bg"])
        self.lbl_go.config(bg=T["bg"], fg=T["text"])
        self.lbl_fi.config(bg=T["bg"], fg=T["accent"])
        self.lbl_xl.config(bg=T["bg"], fg=T["text"])
        self.sep_line.config(bg=T["accent"])
        self.lbl_sub.config(bg=T["bg"], fg=T["text_dim"])
        self.search_outer.config(bg=T["accent"])
        self.search_inner.config(bg=T["surface"])
        self.lbl_prompt.config(bg=T["surface"], fg=T["accent"])
        self.barra.config(bg=T["surface"], fg=T["text"], insertbackground=T["accent"])
        self.irbtn.config(
            bg=T["accent"], fg=T["bg"],
            activebackground=T["accent2"], activeforeground=T["text"],
        )
        self.hints_row.config(bg=T["bg"])
        for btn in self.hint_btns:
            btn.config(bg=T["bg"], fg=T["text_dim"],
                       activebackground=T["surface"], activeforeground=T["accent"])
        # contenido — browser
        self.browser_frame.config(bg=T["bg"])
        self.buttons_frame.config(bg=T["surface"])

        # status bar
        self.status_bar.config(bg=T["topbar"])
        self.status_accent.config(bg=T["accent"])
        self.lbl_status.config(bg=T["topbar"], fg=T["text_dim"])
        self.lbl_sistema.config(bg=T["topbar"], fg=T["text_dim"])

        # panel lateral
        self.panel_frame.config(bg=T["surface"])
        self.panel_sep.config(bg=T["border"])
        self._panel_inner.config(bg=T["surface"])
        self._panel_sep_inner.config(bg=T["border"])
        for lbl in self._panel_labels:
            lbl.config(bg=T["surface"], fg=T["text"])
        for lb in (self.lb_historial, self.lb_favoritos):
            lb.config(
                bg=T["surface"], fg=T["text"],
                selectbackground=T["accent"], selectforeground=T["bg"],
            )
        for btn in (self._btn_limpiar_hist, self._btn_ir_fav, self._btn_quitar_fav):
            btn.config(
                bg=T["surface"], fg=T["text_dim"],
                activebackground=T["bg"], activeforeground=T["accent"],
            )

    def _toggle_modo(self):
        self.is_dark = not self.is_dark
        self.theme   = DARK if self.is_dark else LIGHT
        self.mode_btn.config(text="◑" if self.is_dark else "◐")
        self._apply_theme()

    # ─────────────────────────────────────────
    #  ACCIONES — BARRA URL
    # ─────────────────────────────────────────
    def _url_bar_navegar(self, event=None):
        """Toma el texto de barra2 y navega en la pestaña activa."""
        url = self.barra2_var.get().strip()
        if url:
            self._navegar_url(url)

    def _url_bar_select_all(self, event=None):
        """Al enfocar la barra URL, selecciona todo para facilitar reescritura."""
        self.barra2.select_range(0, "end")
        self.barra2.icursor("end")

    def _url_bar_sync(self, event=None):
        """Al perder el foco, restaura la URL real de la pestaña activa."""
        p = self.gestor.pestaña_activa() if hasattr(self, "gestor") else None
        if p:
            self.barra2_var.set(p.barra.entrada_var.get().strip())

    def sincronizar_barra_url(self, url: str = ""):
        """
        Actualiza la barra URL con la URL provista o con la de la pestaña activa.
        Llamar tras cada navegación exitosa.
        """
        if not url and hasattr(self, "gestor"):
            p = self.gestor.pestaña_activa()
            if p:
                url = p.barra.entrada_var.get().strip()
        self.barra2_var.set(url)

    # ─────────────────────────────────────────
    #  ACCIONES — NAVEGACIÓN
    # ─────────────────────────────────────────
    def _navegar_atras(self):
        """Navega atrás en el historial de la pestaña activa."""
        p = self.gestor.pestaña_activa() if hasattr(self, "gestor") else None
        if not p:
            return
        # Busca la URL anterior en el historial de la pestaña
        actual = p.barra.entrada_var.get().strip()
        hist   = p.historial.historial
        if not hist:
            return
        try:
            idx = hist.index(actual)
        except ValueError:
            idx = len(hist)
        if idx > 0:
            p.barra.entrada_var.set(hist[idx - 1])
            p.barra.iniciar_busqueda()

    def _navegar_adelante(self):
        """Navega adelante en el historial de la pestaña activa."""
        p = self.gestor.pestaña_activa() if hasattr(self, "gestor") else None
        if not p:
            return
        actual = p.barra.entrada_var.get().strip()
        hist   = p.historial.historial
        if not hist:
            return
        try:
            idx = hist.index(actual)
        except ValueError:
            idx = -1
        if idx != -1 and idx < len(hist) - 1:
            p.barra.entrada_var.set(hist[idx + 1])
            p.barra.iniciar_busqueda()

    def _recargar(self):
        """Recarga la página actual de la pestaña activa."""
        p = self.gestor.pestaña_activa() if hasattr(self, "gestor") else None
        if p and p.barra.entrada_var.get().strip():
            p.barra.iniciar_busqueda()

    def _actualizar_botones_nav(self):
        """
        Habilita/deshabilita ◀ y ▶ según el historial de la pestaña activa.
        Llamar tras cada navegación.
        """
        p = self.gestor.pestaña_activa() if hasattr(self, "gestor") else None
        if not p or not p.historial:
            self.btn_atras.config(state="disabled")
            self.btn_adelante.config(state="disabled")
            return
        hist   = p.historial.historial
        actual = p.barra.entrada_var.get().strip()
        try:
            idx = hist.index(actual)
        except ValueError:
            idx = len(hist) - 1
        self.btn_atras.config(   state="normal"   if idx > 0                else "disabled")
        self.btn_adelante.config(state="normal"   if idx < len(hist) - 1   else "disabled")

    # ─────────────────────────────────────────
    #  ACCIONES — PESTAÑAS
    # ─────────────────────────────────────────
    def _nueva_pestaña(self):
        """Crea una nueva pestaña y la selecciona."""
        if hasattr(self, "gestor"):
            self.gestor.nueva_pestaña("Nueva pestaña")
            self.sincronizar_barra_url("")

    def _cerrar_pestaña(self):
        """Cierra la pestaña activa."""
        if hasattr(self, "gestor"):
            self.gestor.cerrar_pestaña_activa()
            self.sincronizar_barra_url()
            self._actualizar_botones_nav()

    def _on_tab_changed_ventana(self, event=None):
        """Al cambiar de pestaña, sincroniza la barra URL y los botones de nav."""
        self.sincronizar_barra_url()
        self._actualizar_botones_nav()

    def _on_historial_navegacion(self):
        """
        Callback para GestorPestañas: se invoca tras cada navegación exitosa.
        Actualiza barra URL, botones nav y panel de historial.
        """
        p = self.gestor.pestaña_activa() if hasattr(self, "gestor") else None
        if p:
            url = p.barra.entrada_var.get().strip()
            self.registrar_en_historial(url)
        self.sincronizar_barra_url()
        self._actualizar_botones_nav()

    # ─────────────────────────────────────────
    #  ACCIONES — FAVORITOS
    # ─────────────────────────────────────────
    def _toggle_favorito(self):
        """Añade la URL activa al panel de favoritos."""
        url = self.barra2_var.get().strip()
        if url:
            self.añadir_favorito(url)
        else:
            messagebox.showinfo("Aviso", "No hay una URL activa para añadir a favoritos")

    # ─────────────────────────────────────────
    #  EVENTOS
    # ─────────────────────────────────────────
    def _bind_events(self):
        # Hover suave en botones de la topbar
        def _hover(btn, key="accent"):
            btn.bind("<Enter>", lambda e: btn.config(fg=self.theme[key]))
            btn.bind("<Leave>", lambda e: btn.config(fg=self.theme["text_dim"]))

        _hover(self.favbtn)
        _hover(self.panel_btn)
        _hover(self.btn_nueva_tab)
        _hover(self.btn_cerrar_tab)
        _hover(self.btn_recargar)
        _hover(self.btn_atras)
        _hover(self.btn_adelante)

    def _volver_splash(self):
        """
        Vuelve a la pantalla de inicio: oculta el navegador,
        muestra la splash, limpia la barra URL y resetea botones nav.
        """
        if not self._navegador_activo:
            return
        self._navegador_activo = False
        self.browser_frame.grid_forget()
        self.splash_frame.grid(row=0, column=0, sticky="nsew")
        self.barra2_var.set("")
        self.barra.delete(0, "end")
        self.barra.focus()
        self.btn_atras.config(state="disabled")
        self.btn_adelante.config(state="disabled")

    def _cerrado(self):
        if messagebox.askokcancel("Salir", "¿Seguro que quieres cerrar el navegador?"):
            self.root.destroy()


# ─────────────────────────────────────────────
#  ENTRY POINT
# ─────────────────────────────────────────────
if __name__ == "__main__":
    Ventana()