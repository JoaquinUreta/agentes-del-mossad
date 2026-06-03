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
        self.sistema  = platform.system()
        self.is_dark  = True
        self.theme    = LIGHT

        self._build_window()
        self._build_topbar()
        self._build_content()
        self._build_statusbar()
        self._apply_theme()
        self._bind_events()

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
        self.root.rowconfigure(0, weight=0)   # top bar
        self.root.rowconfigure(1, weight=1)   # contenido
        self.root.rowconfigure(2, weight=0)   # status bar

    # ─────────────────────────────────────────
    #  TOP BAR
    # ─────────────────────────────────────────
    def _build_topbar(self):
        self.top_bar = tk.Frame(self.root, height=52)
        self.top_bar.grid(row=0, column=0, sticky="ew")
        self.top_bar.grid_propagate(False)
        self.top_bar.columnconfigure(1, weight=1)

        self.accent_line = tk.Frame(self.top_bar, height=2)
        self.accent_line.place(relx=0, rely=1.0, relwidth=1.0, anchor="sw")

        self.logo_top = tk.Label(
            self.top_bar,
            text="GO/",
            font=("Courier New", 16, "bold"),
            padx=14,
        )
        self.logo_top.grid(row=0, column=0, pady=10, sticky="w")

        self.frame_search_top = tk.Frame(self.top_bar)
        self.frame_search_top.grid(row=0, column=1, pady=10, padx=(0, 10), sticky="ew")
        self.frame_search_top.columnconfigure(0, weight=1)

        self.barra2_var = tk.StringVar()
        self.barra2 = tk.Entry(
            self.frame_search_top,
            textvariable=self.barra2_var,
            relief="flat",
            font=FONT_ENTRY,
            bd=0,
            highlightthickness=1,
            state="disabled",
        )
        self.barra2.grid(row=0, column=0, ipady=6, ipadx=8, sticky="ew")

        self.favbtn = tk.Button(
            self.top_bar,
            text="★",
            relief="flat",
            font=FONT_ICON,
            cursor="hand2",
            bd=0,
            padx=10,
            command=self._toggle_favorito,
        )
        self.favbtn.grid(row=0, column=2, padx=(0, 6))

        self.mode_btn = tk.Button(
            self.top_bar,
            text="◑",
            relief="flat",
            font=FONT_ICON,
            cursor="hand2",
            bd=0,
            padx=8,
            command=self._toggle_modo,
        )
        self.mode_btn.grid(row=0, column=3, padx=(0, 10))

    # ─────────────────────────────────────────
    #  CONTENIDO CENTRAL
    # ─────────────────────────────────────────
    def _build_content(self):
        self.content_frame = tk.Frame(self.root)
        self.content_frame.grid(row=1, column=0, sticky="nsew")
        self.content_frame.columnconfigure(0, weight=1)
        self.content_frame.rowconfigure(0, weight=1)

        self.center_frame = tk.Frame(self.content_frame)
        self.center_frame.place(relx=0.5, rely=0.46, anchor="center")

        # Título
        self.title_row = tk.Frame(self.center_frame)
        self.title_row.pack()

        self.lbl_go = tk.Label(self.title_row, text="GO",       font=FONT_TITLE)
        self.lbl_go.pack(side="left")
        self.lbl_fi = tk.Label(self.title_row, text="FILE",     font=FONT_TITLE)
        self.lbl_fi.pack(side="left")
        self.lbl_xl = tk.Label(self.title_row, text="XPLORER",  font=FONT_TITLE)
        self.lbl_xl.pack(side="left")

        self.sep_line = tk.Frame(self.center_frame, height=2, width=420)
        self.sep_line.pack(pady=(4, 18))

        self.lbl_sub = tk.Label(
            self.center_frame,
            text="w e b   ·   l o c a l   ·   e v e r y w h e r e",
            font=("Courier New", 10),
        )
        self.lbl_sub.pack(pady=(0, 28))

        # Barra de búsqueda principal
        self.search_outer = tk.Frame(self.center_frame, padx=2, pady=2)
        self.search_outer.pack(fill="x")

        self.search_inner = tk.Frame(self.search_outer)
        self.search_inner.pack(fill="x")
        self.search_inner.columnconfigure(1, weight=1)

        self.lbl_prompt = tk.Label(
            self.search_inner,
            text=" ›_ ",
            font=("Courier New", 13, "bold"),
        )
        self.lbl_prompt.grid(row=0, column=0, sticky="w", padx=(8, 0))

        self.barra = tk.Entry(
            self.search_inner,
            relief="flat",
            font=("Courier New", 13),
            bd=0,
            highlightthickness=0,
        )
        self.barra.grid(row=0, column=1, sticky="ew", ipady=10)

        self.irbtn = tk.Button(
            self.search_inner,
            text=" IR ",
            relief="flat",
            font=("Courier New", 10, "bold"),
            cursor="hand2",
            bd=0,
            padx=12,
            pady=10,
            command=self._ir,
        )
        self.irbtn.grid(row=0, column=2)

        # Atajos rápidos
        self.hints_row = tk.Frame(self.center_frame)
        self.hints_row.pack(pady=(14, 0))

        self.hint_btns = []
        for hint in ["https://", "file:///", "~/Documentos"]:
            btn = tk.Button(
                self.hints_row,
                text=hint,
                relief="flat",
                font=FONT_SMALL,
                cursor="hand2",
                bd=0,
                padx=8,
                pady=3,
                command=lambda h=hint: self._set_hint(h),
            )
            btn.pack(side="left", padx=4)
            self.hint_btns.append(btn)

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
        self.frame_search_top.config(bg=T["topbar"])
        self.barra2.config(
            bg=T["surface"], fg=T["text_dim"],
            insertbackground=T["accent"],
            highlightbackground=T["border"], highlightcolor=T["accent"],
            disabledbackground=T["surface"], disabledforeground=T["text_dim"],
        )
        self.favbtn.config(
            bg=T["topbar"], fg=T["text_dim"],
            activebackground=T["topbar"], activeforeground=T["accent"],
        )
        self.mode_btn.config(
            bg=T["topbar"], fg=T["accent"],
            activebackground=T["topbar"], activeforeground=T["text"],
        )

        # contenido
        self.content_frame.config(bg=T["bg"])
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
        self.barra.config(
            bg=T["surface"], fg=T["text"], insertbackground=T["accent"]
        )
        self.irbtn.config(
            bg=T["accent"], fg=T["bg"],
            activebackground=T["accent2"], activeforeground=T["text"],
        )
        self.hints_row.config(bg=T["bg"])
        for btn in self.hint_btns:
            btn.config(
                bg=T["bg"], fg=T["text_dim"],
                activebackground=T["surface"], activeforeground=T["accent"],
            )

        # status bar
        self.status_bar.config(bg=T["topbar"])
        self.status_accent.config(bg=T["accent"])
        self.lbl_status.config(bg=T["topbar"], fg=T["text_dim"])
        self.lbl_sistema.config(bg=T["topbar"], fg=T["text_dim"])

    def _toggle_modo(self):
        self.is_dark = not self.is_dark
        self.theme   = DARK if self.is_dark else LIGHT
        self.mode_btn.config(text="◑" if self.is_dark else "◐")
        self._apply_theme()

    # ─────────────────────────────────────────
    #  ACCIONES
    # ─────────────────────────────────────────
    def _ir(self):
        url = self.barra.get().strip()
        if url:
            self.lbl_status.config(text=f"navegando: {url}")

    def _set_hint(self, hint):
        self.barra.delete(0, tk.END)
        self.barra.insert(0, hint)
        self.barra.focus()

    def _toggle_favorito(self):
        pass  # lógica de favoritos aquí

    # ─────────────────────────────────────────
    #  EVENTOS
    # ─────────────────────────────────────────
    def _bind_events(self):
        self.root.bind("<Return>", lambda e: self._ir())
        self.favbtn.bind("<Enter>", lambda e: self.favbtn.config(fg=self.theme["accent"]))
        self.favbtn.bind("<Leave>", lambda e: self.favbtn.config(fg=self.theme["text_dim"]))

    def _cerrado(self):
        if messagebox.askokcancel("Salir", "¿Seguro que quieres cerrar el navegador?"):
            self.root.destroy()


# ─────────────────────────────────────────────
#  ENTRY POINT
# ─────────────────────────────────────────────
if __name__ == "__main__":
    Ventana()