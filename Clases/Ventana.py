import os
import json
import tkinter as tk
from tkinter import ttk
import platform
from tkinter import messagebox
from tkinter import filedialog
from RenderAvanzado import RenderizadorParserAvanzado
from Historial import Historial
from Pestaña import Pestaña, GestorPestañas
from VentanaBusqueda import VentanaBusqueda

BASE_DIR      = os.path.dirname(os.path.abspath(__file__))
FAVS_FILE     = os.path.join(BASE_DIR, "favoritos.json")
HISTORIAL_FILE = os.path.join(BASE_DIR, "historial.json")
MAX_FAVORITOS = 10

# ─────────────────────────────────────────────
#  ASISTENTE DE IA — configurar aquí la api_key de Gemini
#  (déjala vacía "" si todavía no tienes una; el botón Asistente IA mostrará
#  un aviso en vez de fallar silenciosamente)
# ─────────────────────────────────────────────
API_KEY_GEMINI = "" #!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!

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

FONT_TITLE = ("Arial", 38, "bold")
FONT_SMALL = ("Arial",  9)
FONT_ENTRY = ("Arial", 11)
FONT_ICON  = ("Segoe UI Symbol", 14)


class Ventana:
    def __init__(self):
        self.sistema  = platform.system()
        self.is_dark  = True
        self.theme    = DARK

        self.favoritos: list[str] = self._cargar_favoritos()

        self.historial_global = Historial(limitante=10)
        for url in reversed(self._cargar_historial()):
            self.historial_global.agregar_historial(url)

        self._panel_visible = False
        self._modo_online   = True   # True = online, False = offline

        self._build_window()
        self._build_topbar()
        self._build_content()   # crea gestor + primera pestaña
        self._build_panel()
        self._build_statusbar()

        # ── Conectar controles de Ventana al GestorPestañas ──────────
        # Esto DEBE hacerse DESPUÉS de _build_topbar y _build_statusbar
        self.gestor.set_controles_ventana(
            btn_atras    = self.btn_atras,
            btn_adelante = self.btn_adelante,
            status_var   = self.status_var,
        )
        # Re-crear la primera pestaña AHORA que los controles están listos
        # (La pestaña creada en _build_content no tenía los controles aún)
        self._reconectar_primera_pestana()

        self._apply_theme()
        self._bind_events()
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

        self.root.columnconfigure(0, weight=1)
        self.root.columnconfigure(1, weight=0)
        self.root.rowconfigure(0, weight=0)
        self.root.rowconfigure(1, weight=1)
        self.root.rowconfigure(2, weight=0)

    # ─────────────────────────────────────────
    #  TOP BAR
    # ─────────────────────────────────────────

    def _build_topbar(self):
        self.top_bar = tk.Frame(self.root, height=52)
        self.top_bar.grid(row=0, column=0, columnspan=2, sticky="ew")
        self.top_bar.grid_propagate(False)
        self.top_bar.columnconfigure(4, weight=1)

        self.accent_line = tk.Frame(self.top_bar, height=2)
        self.accent_line.place(relx=0, rely=1.0, relwidth=1.0, anchor="sw")

        self.logo_top = tk.Label(
            self.top_bar, text="GO/",
            font=("Courier New", 16, "bold"), padx=10, cursor="hand2",
        )
        self.logo_top.grid(row=0, column=0, pady=10, sticky="w")
        self.logo_top.bind("<Button-1>", lambda e: self._volver_splash())

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

        self.btn_ir_top = tk.Button(
            self.top_bar, text=" IR ",
            font=("Courier New", 9, "bold"),
            relief="flat", cursor="hand2", bd=0, padx=10,
            command=self._url_bar_navegar,
        )
        self.btn_ir_top.grid(row=0, column=5, pady=10, padx=(0, 4))

        self.favbtn = tk.Button(
            self.top_bar, text="★", font=FONT_ICON,
            relief="flat", cursor="hand2", bd=0, padx=8,
            command=self._toggle_favorito,
        )
        self.favbtn.grid(row=0, column=6, pady=10, padx=(0, 2))

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

        # ── Motor de Búsqueda (Requerimiento 4) ───────────────────────
        self.btn_motor_busqueda = tk.Button(
            self.top_bar, text="🔍", font=FONT_ICON,
            relief="flat", cursor="hand2", bd=0, padx=8,
            command=self._abrir_motor_busqueda,
        )
        self.btn_motor_busqueda.grid(row=0, column=9, pady=10, padx=(0, 4))

        # ── Switch ONLINE / OFFLINE ───────────────────────────────────

        self.switch_frame = tk.Frame(self.top_bar)
        self.switch_frame.grid(row=0, column=10, pady=10, padx=(4, 6))

        self.lbl_modo = tk.Label(
            self.switch_frame, text="ONLINE",
            font=("Courier New", 8, "bold"), width=7,
        )
        self.lbl_modo.pack(side="left", padx=(0, 4))

        # Canvas que actúa como switch visual (38×20 px)
        self.switch_canvas = tk.Canvas(
            self.switch_frame, width=38, height=20,
            bd=0, highlightthickness=0, cursor="hand2",
        )
        self.switch_canvas.pack(side="left")
        self.switch_canvas.bind("<Button-1>", lambda e: self._toggle_online())
        self._dibujar_switch()

        self.mode_btn = tk.Button(
            self.top_bar, text="◑", font=FONT_ICON,
            relief="flat", cursor="hand2", bd=0, padx=8,
            command=self._toggle_modo,
        )
        self.mode_btn.grid(row=0, column=11, pady=10)

        self.panel_btn = tk.Button(
            self.top_bar, text="☰", font=FONT_ICON,
            relief="flat", cursor="hand2", bd=0, padx=8,
            command=self._toggle_panel,
        )
        self.panel_btn.grid(row=0, column=12, pady=10, padx=(0, 8))

    # ─────────────────────────────────────────
    #  CONTENT (splash + notebook)
    # ─────────────────────────────────────────
    def _build_content(self):
        self.style_ttk = ttk.Style()
        self._navegador_activo = False

        self.content_frame = tk.Frame(self.root)
        self.content_frame.grid(row=1, column=0, sticky="nsew")
        self.content_frame.columnconfigure(0, weight=1)
        self.content_frame.rowconfigure(0, weight=1)

        # ── Splash ────────────────────────────────────────────────────
        self.splash_frame = tk.Frame(self.content_frame)
        self.splash_frame.grid(row=0, column=0, sticky="nsew")
        self.splash_frame.columnconfigure(0, weight=1)
        self.splash_frame.rowconfigure(0, weight=1)

        self.center_frame = tk.Frame(self.splash_frame)
        self.center_frame.place(relx=0.5, rely=0.46, anchor="center")

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

        self.search_outer = tk.Frame(self.center_frame, padx=2, pady=2)
        self.search_outer.pack(fill="x")
        self.search_inner = tk.Frame(self.search_outer)
        self.search_inner.pack(fill="x")
        self.search_inner.columnconfigure(1, weight=1)

        self.lbl_prompt = tk.Label(
            self.search_inner, text=" ›_ ", font=("Courier New", 13, "bold"),
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

        self.hints_row = tk.Frame(self.center_frame)
        self.hints_row.pack(pady=(14, 0))
        self.hint_btns = []

        # ── Browser / Notebook ────────────────────────────────────────
        self.browser_frame = tk.Frame(self.content_frame)
        self.browser_frame.columnconfigure(0, weight=1)
        self.browser_frame.rowconfigure(0, weight=1)

        self.buttons_frame = tk.Frame(self.browser_frame, height=0)

        self.notebook = ttk.Notebook(self.browser_frame)
        self.notebook.grid(row=0, column=0, sticky="nsew", padx=4, pady=2)

        self.menu_savedurl = tk.Menu(self.root, tearoff=0)

        # StringVar de status (antes de crear gestor para poder pasarla)
        # Se crea aquí temporalmente; _build_statusbar la sobreescribirá
        # apuntando al mismo objeto, ya que GestorPestañas guarda la referencia.
        self.status_var = tk.StringVar(value="listo")

        self.gestor = GestorPestañas(
            notebook      = self.notebook,
            style         = self.style_ttk,
            buttons_frame = self.buttons_frame,
            menu_savedurl = self.menu_savedurl,
            api_key_ia    = API_KEY_GEMINI,
        )
        self.gestor.set_menu_historial_callback(self._on_historial_navegacion)

        # Primera pestaña (sin controles aún; se reconecta en __init__)
        self.gestor.nueva_pestaña("Nueva pestaña")

        self.notebook.bind("<<NotebookTabChanged>>", self._on_tab_changed_ventana)

    def _reconectar_primera_pestana(self):
        """
        La primera pestaña se creó antes de que _build_topbar terminara,
        así que no tenía btn_atras/btn_adelante/status_var.
        Los inyectamos ahora directamente.
        """
        for p in self.gestor.pestañas:
            p.barra.btn_atras    = self.btn_atras
            p.barra.btn_adelante = self.btn_adelante
            p.barra.status_var   = self.status_var
            p.barra.gestor_pestañas = self.gestor

    # ─────────────────────────────────────────
    #  STATUS BAR
    # ─────────────────────────────────────────
    def _build_statusbar(self):
        self.status_bar = tk.Frame(self.root, height=24)
        self.status_bar.grid(row=2, column=0, sticky="ew")
        self.status_bar.grid_propagate(False)

        self.status_accent = tk.Frame(self.status_bar, width=4)
        self.status_accent.pack(side="left", fill="y")

        # Reutilizamos la misma StringVar creada en _build_content
        self.lbl_status = tk.Label(
            self.status_bar, textvariable=self.status_var,
            font=FONT_SMALL, padx=10,
        )
        self.lbl_status.pack(side="left", fill="y")

        self.lbl_sistema = tk.Label(
            self.status_bar, text=f"  {self.sistema}  ", font=FONT_SMALL
        )
        self.lbl_sistema.pack(side="right", fill="y")

    # ─────────────────────────────────────────
    #  PANEL LATERAL
    # ─────────────────────────────────────────
    def _build_panel(self):
        PANEL_W = 260

        self.panel_frame = tk.Frame(self.root, width=PANEL_W)

        self.panel_sep = tk.Frame(self.panel_frame, width=2)
        self.panel_sep.pack(side="left", fill="y")

        inner = tk.Frame(self.panel_frame)
        inner.pack(side="left", fill="both", expand=True, padx=(6, 6), pady=6)
        inner.columnconfigure(0, weight=1)

        lbl_hist = tk.Label(inner, text="Historial",
                            font=("Courier New", 9, "bold"), anchor="w")
        lbl_hist.grid(row=0, column=0, sticky="ew", pady=(4, 2))

        frame_hist = tk.Frame(inner)
        frame_hist.grid(row=1, column=0, sticky="nsew")
        frame_hist.columnconfigure(0, weight=1)
        inner.rowconfigure(1, weight=1)

        scroll_hist = ttk.Scrollbar(frame_hist, orient="vertical")
        scroll_hist.pack(side="right", fill="y")

        self.lb_historial = tk.Listbox(
            frame_hist, yscrollcommand=scroll_hist.set,
            selectmode="browse", activestyle="none",
            font=FONT_SMALL, bd=0, highlightthickness=0,
            relief="flat", cursor="hand2",
        )
        self.lb_historial.pack(side="left", fill="both", expand=True)
        scroll_hist.config(command=self.lb_historial.yview)

        btn_limpiar_hist = tk.Button(
            inner, text="Limpiar historial", font=FONT_SMALL,
            relief="flat", cursor="hand2", bd=0, pady=2,
            command=self._limpiar_historial,
        )
        btn_limpiar_hist.grid(row=2, column=0, sticky="ew", pady=(2, 6))
        self._btn_limpiar_hist = btn_limpiar_hist

        sep = tk.Frame(inner, height=1)
        sep.grid(row=3, column=0, sticky="ew", pady=(0, 6))
        self._panel_sep_inner = sep

        lbl_fav = tk.Label(inner, text="Favoritos",
                           font=("Courier New", 9, "bold"), anchor="w")
        lbl_fav.grid(row=4, column=0, sticky="ew", pady=(0, 2))

        frame_fav = tk.Frame(inner)
        frame_fav.grid(row=5, column=0, sticky="nsew")
        frame_fav.columnconfigure(0, weight=1)
        inner.rowconfigure(5, weight=1)

        scroll_fav = ttk.Scrollbar(frame_fav, orient="vertical")
        scroll_fav.pack(side="right", fill="y")

        self.lb_favoritos = tk.Listbox(
            frame_fav, yscrollcommand=scroll_fav.set,
            selectmode="browse", activestyle="none",
            font=FONT_SMALL, bd=0, highlightthickness=0,
            relief="flat", cursor="hand2",
        )
        self.lb_favoritos.pack(side="left", fill="both", expand=True)
        scroll_fav.config(command=self.lb_favoritos.yview)

        fav_btns = tk.Frame(inner)
        fav_btns.grid(row=6, column=0, sticky="ew", pady=(2, 4))
        fav_btns.columnconfigure(0, weight=1)
        fav_btns.columnconfigure(1, weight=1)

        self._btn_ir_fav = tk.Button(
            fav_btns, text="Ir a URL", font=FONT_SMALL,
            relief="flat", cursor="hand2", bd=0, pady=2,
            command=self._ir_a_favorito,
        )
        self._btn_ir_fav.grid(row=0, column=0, sticky="ew", padx=(0, 2))

        self._btn_quitar_fav = tk.Button(
            fav_btns, text="Quitar", font=FONT_SMALL,
            relief="flat", cursor="hand2", bd=0, pady=2,
            command=self._quitar_favorito,
        )
        self._btn_quitar_fav.grid(row=0, column=1, sticky="ew", padx=(2, 0))

        self._panel_labels = [lbl_hist, lbl_fav]
        self._panel_inner  = inner

        self._refrescar_listbox_favoritos()

        self.lb_historial.bind("<Double-Button-1>", lambda e: self._navegar_desde_historial())
        self.lb_favoritos.bind("<Double-Button-1>", lambda e: self._ir_a_favorito())

    def _toggle_panel(self):
        self._panel_visible = not self._panel_visible
        if self._panel_visible:
            self.panel_frame.grid(row=1, column=1, sticky="nsew")
        else:
            self.panel_frame.grid_forget()

    # ─────────────────────────────────────────
    #  FAVORITOS
    # ─────────────────────────────────────────
    def _cargar_favoritos(self) -> list:
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
        try:
            with open(FAVS_FILE, "w", encoding="utf-8") as f:
                json.dump(self.favoritos, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    def _refrescar_listbox_favoritos(self):
        self.lb_favoritos.delete(0, "end")
        for url in self.favoritos:
            self.lb_favoritos.insert("end", url)

    def añadir_favorito(self, url: str):
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
        sel = self.lb_favoritos.curselection()
        if not sel:
            return
        url = self.favoritos[sel[0]]
        self._navegar_url(url)

    def _toggle_favorito(self):
        url = self.barra2_var.get().strip()
        if url:
            self.añadir_favorito(url)
        else:
            messagebox.showinfo("Aviso", "No hay una URL activa para añadir a favoritos")

    # ─────────────────────────────────────────
    #  HISTORIAL
    # ─────────────────────────────────────────
    def _cargar_historial(self) -> list:
        if os.path.isfile(HISTORIAL_FILE):
            try:
                with open(HISTORIAL_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                if isinstance(data, list):
                    return [str(u) for u in data[:MAX_FAVORITOS]]
            except Exception:
                pass
        return []

    def _guardar_historial(self):
        try:
            with open(HISTORIAL_FILE, "w", encoding="utf-8") as f:
                json.dump(self.historial_global.historial, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    def registrar_en_historial(self, url: str):
        url = url.strip()
        if not url:
            return
        self.historial_global.agregar_historial(url)
        self._refrescar_listbox_historial()
        self._guardar_historial()

    def _refrescar_listbox_historial(self):
        self.lb_historial.delete(0, "end")
        for i in range(self.historial_global.limite):
            entry = self.historial_global.obtener_url(i)
            if entry is None:
                break
            self.lb_historial.insert("end", entry)

    def _limpiar_historial(self):
        if messagebox.askyesno("Confirmar", "¿Limpiar todo el historial?"):
            self.historial_global.historial.clear()
            self.lb_historial.delete(0, "end")
            self._guardar_historial()

    def _navegar_desde_historial(self):
        sel = self.lb_historial.curselection()
        if not sel:
            return
        url = self.lb_historial.get(sel[0])
        self._navegar_url(url)

    # ─────────────────────────────────────────
    #  NAVEGACIÓN CENTRAL
    # ─────────────────────────────────────────
    def _navegar_url(self, url: str):
        """Punto de entrada para navegar desde el panel, historial o favoritos."""
        self._activar_navegador()
        self.barra2_var.set(url)
        self.gestor.cargar_url_en_activa(url)

    def _ir_splash(self):
        url = self.barra.get().strip()
        if not url:
            return
        self._activar_navegador()
        self.barra2_var.set(url)
        self.gestor.cargar_url_en_activa(url)

    def _activar_navegador(self):
        if self._navegador_activo:
            return
        self._navegador_activo = True
        self.splash_frame.grid_forget()
        self.browser_frame.grid(row=0, column=0, sticky="nsew")

    # ─────────────────────────────────────────
    #  BARRA URL (topbar)
    # ─────────────────────────────────────────
    def _url_bar_navegar(self, event=None):
        url = self.barra2_var.get().strip()
        if url:
            self._activar_navegador()
            self.gestor.cargar_url_en_activa(url)

    def _url_bar_select_all(self, event=None):
        self.barra2.select_range(0, "end")
        self.barra2.icursor("end")

    def _url_bar_sync(self, event=None):
        p = self.gestor.pestaña_activa()
        if p:
            self.barra2_var.set(p.barra.entrada_var.get().strip())

    def sincronizar_barra_url(self, url: str = ""):
        if not url:
            p = self.gestor.pestaña_activa()
            if p:
                url = p.barra.entrada_var.get().strip()
        self.barra2_var.set(url)

    # ─────────────────────────────────────────
    #  MOTOR DE BÚSQUEDA SIMULADO (Requerimiento 4)
    # ─────────────────────────────────────────
    def _abrir_motor_busqueda(self):
        """Abre el popup modal del Motor de Búsqueda."""
        VentanaBusqueda(
            root=self.root,
            theme=self.theme,
            on_buscar=self._cargar_resultado_busqueda,
        )

    def _cargar_resultado_busqueda(self, ruta_html: str):
        """
        Callback invocado por VentanaBusqueda cuando hay un resultado válido.
        Carga el HTML de resultados en la pestaña actualmente activa
        (modo local/offline, ya que es un archivo en disco).
        """
        self._activar_navegador()
        p = self.gestor.pestaña_activa()
        if p is None:
            return
        # Forzamos navegación local para este archivo, independientemente
        # del modo online/offline activo, ya que es contenido simulado en disco.
        p.barra.Status = False
        p.barra.entrada_var.set(ruta_html)
        p.barra.iniciar_busqueda()
        self.sincronizar_barra_url(ruta_html)
        self._actualizar_botones_nav(p)
        # Restauramos el modo de navegación visible en la UI
        p.barra.Status = self._modo_online

    # ─────────────────────────────────────────
    #  BOTONES ADELANTE / ATRÁS / RECARGAR
    # ─────────────────────────────────────────
    def _navegar_atras(self):
        p = self.gestor.pestaña_activa()
        if not p:
            return
        url = p.navegacion.atras()
        if url:
            p.barra._navegacion_interna = True
            p.barra.entrada_var.set(url)
            p.barra.iniciar_busqueda()
            p.barra._navegacion_interna = False
            self.sincronizar_barra_url(url)
            self._actualizar_botones_nav(p)

    def _navegar_adelante(self):
        p = self.gestor.pestaña_activa()
        if not p:
            return
        url = p.navegacion.adelante()
        if url:
            p.barra._navegacion_interna = True
            p.barra.entrada_var.set(url)
            p.barra.iniciar_busqueda()
            p.barra._navegacion_interna = False
            self.sincronizar_barra_url(url)
            self._actualizar_botones_nav(p)

    def _recargar(self):
        p = self.gestor.pestaña_activa()
        if p and p.barra.entrada_var.get().strip():
            p.barra.iniciar_busqueda()

    def _actualizar_botones_nav(self, p: Pestaña = None):
        if p is None:
            p = self.gestor.pestaña_activa()
        if not p:
            self.btn_atras.config(state="disabled")
            self.btn_adelante.config(state="disabled")
            return
        self.btn_atras.config(
            state="normal" if p.navegacion.puede_atras()    else "disabled"
        )
        self.btn_adelante.config(
            state="normal" if p.navegacion.puede_adelante() else "disabled"
        )

    # ─────────────────────────────────────────
    #  PESTAÑAS
    # ─────────────────────────────────────────
    def _nueva_pestaña(self):
        self._activar_navegador()
        self.gestor.nueva_pestaña("Nueva pestaña")
        self.sincronizar_barra_url("")
        self.btn_atras.config(state="disabled")
        self.btn_adelante.config(state="disabled")

    def _cerrar_pestaña(self):
        self.gestor.cerrar_pestaña_activa()
        self.sincronizar_barra_url()
        self._actualizar_botones_nav()

    def _on_tab_changed_ventana(self, event=None):
        self.sincronizar_barra_url()
        self._actualizar_botones_nav()

    def _on_historial_navegacion(self):
        """Callback tras cada navegación exitosa: actualiza historial y barra."""
        p = self.gestor.pestaña_activa()
        if p:
            url = p.barra.entrada_var.get().strip()
            self.registrar_en_historial(url)
            self.barra2_var.set(url)
        self._actualizar_botones_nav(p)

    # ─────────────────────────────────────────
    #  TEMA
    # ─────────────────────────────────────────
    def _apply_theme(self):
        T = self.theme
        self.root.config(bg=T["bg"])

        self.top_bar.config(bg=T["topbar"])
        self.accent_line.config(bg=T["accent"])
        self.logo_top.config(bg=T["topbar"], fg=T["accent"])
        self.favbtn.config(bg=T["topbar"], fg=T["text_dim"],
                           activebackground=T["topbar"], activeforeground=T["accent"])
        self.btn_motor_busqueda.config(bg=T["topbar"], fg=T["text_dim"],
                           activebackground=T["topbar"], activeforeground=T["accent"])
        self.mode_btn.config(bg=T["topbar"], fg=T["accent"],
                             activebackground=T["topbar"], activeforeground=T["text"])
        self.panel_btn.config(bg=T["topbar"], fg=T["text_dim"],
                              activebackground=T["topbar"], activeforeground=T["accent"])
        for btn in (self.btn_atras, self.btn_adelante, self.btn_recargar):
            btn.config(bg=T["topbar"], fg=T["text_dim"],
                       activebackground=T["topbar"], activeforeground=T["accent"],
                       disabledforeground=T["border"])
        self.frame_url.config(bg=T["surface"],
                              highlightbackground=T["border"], highlightcolor=T["accent"])
        self.barra2.config(bg=T["surface"], fg=T["text"], insertbackground=T["accent"])
        self.btn_ir_top.config(bg=T["accent"], fg=T["bg"],
                               activebackground=T["accent2"], activeforeground=T["text"])
        for btn in (self.btn_nueva_tab, self.btn_cerrar_tab):
            btn.config(bg=T["topbar"], fg=T["text_dim"],
                       activebackground=T["topbar"], activeforeground=T["accent"])

        # switch online/offline
        self.switch_frame.config(bg=T["topbar"])
        self.lbl_modo.config(
            bg=T["topbar"],
            fg=T["accent"] if self._modo_online else T["text_dim"],
        )
        self.switch_canvas.config(bg=T["topbar"])
        self._dibujar_switch()

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
        self.irbtn.config(bg=T["accent"], fg=T["bg"],
                          activebackground=T["accent2"], activeforeground=T["text"])
        self.hints_row.config(bg=T["bg"])
        for btn in self.hint_btns:
            btn.config(bg=T["bg"], fg=T["text_dim"],
                       activebackground=T["surface"], activeforeground=T["accent"])
        self.browser_frame.config(bg=T["bg"])

        self.status_bar.config(bg=T["topbar"])
        self.status_accent.config(bg=T["accent"])
        self.lbl_status.config(bg=T["topbar"], fg=T["text_dim"])
        self.lbl_sistema.config(bg=T["topbar"], fg=T["text_dim"])

        self.panel_frame.config(bg=T["surface"])
        self.panel_sep.config(bg=T["border"])
        self._panel_inner.config(bg=T["surface"])
        self._panel_sep_inner.config(bg=T["border"])
        for lbl in self._panel_labels:
            lbl.config(bg=T["surface"], fg=T["text"])
        for lb in (self.lb_historial, self.lb_favoritos):
            lb.config(bg=T["surface"], fg=T["text"],
                      selectbackground=T["accent"], selectforeground=T["bg"])
        for btn in (self._btn_limpiar_hist, self._btn_ir_fav, self._btn_quitar_fav):
            btn.config(bg=T["surface"], fg=T["text_dim"],
                       activebackground=T["bg"], activeforeground=T["accent"])

        self.gestor.actualizar_tema_todas(self.is_dark)

    def _toggle_online(self):
        """Alterna entre modo ONLINE y OFFLINE y propaga el cambio a todas las pestañas."""
        self._modo_online = not self._modo_online
        self.gestor.set_modo_online(self._modo_online)
        self._dibujar_switch()
        modo_texto = "ONLINE" if self._modo_online else "OFFLINE"
        self.lbl_modo.config(text=modo_texto)
        self.status_var.set(f"Modo {modo_texto} activado")

    def _dibujar_switch(self):
        """Redibuja el canvas del switch según el estado actual."""
        c = self.switch_canvas
        c.delete("all")
        T = self.theme
        if self._modo_online:
            pista_color  = T["accent"]    # dorado/verde = online
            circulo_x    = 28             # círculo a la derecha
        else:
            pista_color  = T["border"]    # gris = offline
            circulo_x    = 10            # círculo a la izquierda
        # Pista redondeada
        c.create_oval(0, 2, 18, 18,  fill=pista_color, outline="")
        c.create_oval(20, 2, 38, 18, fill=pista_color, outline="")
        c.create_rectangle(9, 2, 29, 18, fill=pista_color, outline="")
        # Círculo deslizante
        c.create_oval(circulo_x - 8, 2, circulo_x + 8, 18,
                      fill=T["surface"], outline=T["border"])

    def _toggle_modo(self):
        self.is_dark = not self.is_dark
        self.theme   = DARK if self.is_dark else LIGHT
        self.mode_btn.config(text="◑" if self.is_dark else "◐")
        self._apply_theme()

    # ─────────────────────────────────────────
    #  EVENTOS
    # ─────────────────────────────────────────
    def _bind_events(self):
        def _hover(btn, key="accent"):
            btn.bind("<Enter>", lambda e: btn.config(fg=self.theme[key]))
            btn.bind("<Leave>", lambda e: btn.config(fg=self.theme["text_dim"]))

        _hover(self.favbtn)
        _hover(self.btn_motor_busqueda)
        _hover(self.panel_btn)
        _hover(self.btn_nueva_tab)
        _hover(self.btn_cerrar_tab)
        _hover(self.btn_recargar)
        _hover(self.btn_atras)
        _hover(self.btn_adelante)

    def _volver_splash(self):
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


if __name__ == "__main__":
    Ventana()