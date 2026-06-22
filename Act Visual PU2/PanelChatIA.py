import tkinter as tk
from tkinter import messagebox


class PanelChatIA:
    """
    Panel lateral tipo chatbot (Requerimientos 5 y 6).
    Se incrusta como columna derecha dentro del main_area de una Pestaña,
    junto al área de contenido (ambos visibles al mismo tiempo).

    Mantiene el historial completo de la conversación en burbujas,
    con scroll, y se abre/cierra mediante:
      - el botón "✕" dentro del propio panel.

    No conoce nada de threading ni de la API de Gemini: solo expone
    agregar_mensaje_usuario() / agregar_mensaje_ia() / mostrar_error_ia()
    para que BarraBusqueda lo alimente.
    """

    ANCHO_PANEL = 300

    def __init__(self, parent, theme):
        self.theme = theme
        T = theme

        # ── Frame raíz del panel (se coloca/oculta vía grid en Pestaña) ─
        self.frame = tk.Frame(parent, bg=T["surface"], width=self.ANCHO_PANEL,
                               highlightthickness=1, highlightbackground=T["border"])
        self.frame.grid_propagate(False)
        self.frame.columnconfigure(0, weight=1)
        self.frame.rowconfigure(1, weight=1)

        # ── Encabezado ───────────────────────────────────────────────
        header = tk.Frame(self.frame, bg=T["topbar"], height=40)
        header.grid(row=0, column=0, sticky="ew")
        header.grid_propagate(False)
        header.columnconfigure(0, weight=1)

        lbl_titulo = tk.Label(
            header, text="Asistente de IA", font=("Courier New", 10, "bold"),
            bg=T["topbar"], fg=T["accent"], anchor="w",
        )
        lbl_titulo.grid(row=0, column=0, sticky="w", padx=10)

        self.btn_cerrar = tk.Button(
            header, text="✕", font=("Courier New", 10),
            relief="flat", cursor="hand2", bd=0, padx=8,
            bg=T["topbar"], fg=T["text_dim"],
            activebackground=T["topbar"], activeforeground=T["accent"],
            command=self._on_cerrar_click,
        )
        self.btn_cerrar.grid(row=0, column=1, sticky="e", padx=(0, 4))

        # ── Área de mensajes (scrollable) ─────────────────────────────
        contenedor_msgs = tk.Frame(self.frame, bg=T["surface"])
        contenedor_msgs.grid(row=1, column=0, sticky="nsew")
        contenedor_msgs.columnconfigure(0, weight=1)
        contenedor_msgs.rowconfigure(0, weight=1)

        self.canvas = tk.Canvas(contenedor_msgs, bg=T["surface"],
                                 highlightthickness=0, width=self.ANCHO_PANEL)
        self.canvas.grid(row=0, column=0, sticky="nsew")

        self.scrollbar = tk.Scrollbar(contenedor_msgs, orient="vertical",
                                       command=self.canvas.yview)
        self.scrollbar.grid(row=0, column=1, sticky="ns")
        self.canvas.config(yscrollcommand=self.scrollbar.set)

        # Frame interno donde se apilan los mensajes (vive dentro del canvas)
        self.frame_mensajes = tk.Frame(self.canvas, bg=T["surface"])
        self._id_frame_mensajes = self.canvas.create_window(
            (0, 0), window=self.frame_mensajes, anchor="nw"
        )

        self.frame_mensajes.bind("<Configure>", self._on_frame_mensajes_resize)
        self.canvas.bind("<Configure>", self._on_canvas_resize)
        # Scroll con la rueda del mouse cuando el cursor está sobre el panel
        self.canvas.bind("<Enter>", lambda e: self._bind_scroll())
        self.canvas.bind("<Leave>", lambda e: self._unbind_scroll())

        # ── Mensaje de bienvenida ──────────────────────────────────────
        self._mensaje_bienvenida_mostrado = False
        self._mostrar_bienvenida_si_vacio()

        # ── Barra de entrada (campo + botón enviar) ────────────────────
        barra_entrada = tk.Frame(self.frame, bg=T["surface"])
        barra_entrada.grid(row=2, column=0, sticky="ew")
        barra_entrada.columnconfigure(0, weight=1)

        self.entrada_var = tk.StringVar()
        self.entrada = tk.Entry(
            barra_entrada, textvariable=self.entrada_var, relief="flat",
            font=("Courier New", 10), bd=0, highlightthickness=1,
            highlightbackground=T["border"], highlightcolor=T["accent"],
            bg=T["bg"], fg=T["text"], insertbackground=T["accent"],
        )
        self.entrada.grid(row=0, column=0, sticky="ew", ipady=6, padx=(8, 4), pady=8)
        self.entrada.bind("<Return>", lambda e: self._on_enviar_click())

        self.btn_enviar = tk.Button(
            barra_entrada, text="➤", font=("Courier New", 11, "bold"),
            relief="flat", cursor="hand2", bd=0, padx=10,
            bg=T["accent"], fg=T["bg"],
            activebackground=T["accent2"], activeforeground=T["text"],
            command=self._on_enviar_click,
        )
        self.btn_enviar.grid(row=0, column=1, sticky="e", padx=(0, 8), pady=8)

        # Callbacks inyectados desde fuera (BarraBusqueda los configura)
        self.on_enviar_pregunta = None   # callback(pregunta: str)
        self.on_cerrar = None            # callback() -> oculta el panel

    # ─────────────────────────────────────────────────────────────────
    #  API PÚBLICA — usada por BarraBusqueda
    # ─────────────────────────────────────────────────────────────────
    def agregar_mensaje_usuario(self, texto: str):
        self._agregar_burbuja(texto, es_usuario=True)

    def agregar_mensaje_ia(self, texto: str):
        self._quitar_indicador_escribiendo()
        self._agregar_burbuja(texto, es_usuario=False)

    def mostrar_error_ia(self, texto: str):
        self._quitar_indicador_escribiendo()
        self._agregar_burbuja(texto, es_usuario=False, es_error=True)

    def mostrar_indicador_escribiendo(self):
        """Muestra una burbuja temporal '...' mientras se espera la respuesta."""
        T = self.theme
        self._frame_escribiendo = tk.Frame(self.frame_mensajes, bg=T["surface"])
        self._frame_escribiendo.pack(fill="x", anchor="w", padx=8, pady=(4, 2))

        lbl = tk.Label(
            self._frame_escribiendo, text="IA está escribiendo…",
            font=("Courier New", 9, "italic"), bg=T["border"], fg=T["text_dim"],
            wraplength=self.ANCHO_PANEL - 50, justify="left", padx=10, pady=6,
        )
        lbl.pack(anchor="w")
        self._scroll_al_final()

    def limpiar_conversacion(self):
        for w in self.frame_mensajes.winfo_children():
            w.destroy()
        self._mensaje_bienvenida_mostrado = False
        self._mostrar_bienvenida_si_vacio()

    def set_entrada_habilitada(self, habilitada: bool):
        estado = "normal" if habilitada else "disabled"
        self.entrada.config(state=estado)
        self.btn_enviar.config(state=estado)

    def focus_entrada(self):
        self.entrada.focus_set()

    # ─────────────────────────────────────────────────────────────────
    #  EVENTOS INTERNOS
    # ─────────────────────────────────────────────────────────────────
    def _on_enviar_click(self):
        pregunta = self.entrada_var.get().strip()
        if not pregunta:
            return
        self.entrada_var.set("")
        if self.on_enviar_pregunta:
            self.on_enviar_pregunta(pregunta)

    def _on_cerrar_click(self):
        if self.on_cerrar:
            self.on_cerrar()

    # ─────────────────────────────────────────────────────────────────
    #  RENDERIZADO DE BURBUJAS
    # ─────────────────────────────────────────────────────────────────
    def _agregar_burbuja(self, texto: str, es_usuario: bool, es_error: bool = False):
        T = self.theme
        fila = tk.Frame(self.frame_mensajes, bg=T["surface"])
        fila.pack(fill="x", anchor="e" if es_usuario else "w", padx=8, pady=4)

        if es_error:
            bg_burbuja, fg_burbuja = "#C0392B", "#FFFFFF"
        elif es_usuario:
            bg_burbuja, fg_burbuja = T["accent"], T["bg"]
        else:
            bg_burbuja, fg_burbuja = T["border"], T["text"]

        lbl = tk.Label(
            fila, text=texto, font=("Courier New", 10),
            bg=bg_burbuja, fg=fg_burbuja,
            wraplength=self.ANCHO_PANEL - 60, justify="left",
            padx=10, pady=8,
        )
        lbl.pack(anchor="e" if es_usuario else "w")

        self._scroll_al_final()

    def _quitar_indicador_escribiendo(self):
        frame = getattr(self, "_frame_escribiendo", None)
        if frame is not None and frame.winfo_exists():
            frame.destroy()
        self._frame_escribiendo = None

    def _mostrar_bienvenida_si_vacio(self):
        if self._mensaje_bienvenida_mostrado:
            return
        T = self.theme
        lbl = tk.Label(
            self.frame_mensajes,
            text="¡Hola soy Gémini!, Pregúntame lo que quieras",
            font=("Courier New", 9), bg=T["surface"], fg=T["text_dim"],
            wraplength=self.ANCHO_PANEL - 40, justify="center",
        )
        lbl.pack(pady=20, padx=10)
        self._mensaje_bienvenida_mostrado = True

    # ─────────────────────────────────────────────────────────────────
    #  SCROLL / CANVAS
    # ─────────────────────────────────────────────────────────────────
    def _on_frame_mensajes_resize(self, event):
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def _on_canvas_resize(self, event):
        # El frame interno siempre debe tener el mismo ancho que el canvas
        self.canvas.itemconfig(self._id_frame_mensajes, width=event.width)

    def _scroll_al_final(self):
        self.frame_mensajes.update_idletasks()
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        self.canvas.yview_moveto(1.0)

    def _bind_scroll(self):
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)      # Windows
        self.canvas.bind_all("<Button-4>", self._on_mousewheel_linux)  # Linux up
        self.canvas.bind_all("<Button-5>", self._on_mousewheel_linux)  # Linux down

    def _unbind_scroll(self):
        self.canvas.unbind_all("<MouseWheel>")
        self.canvas.unbind_all("<Button-4>")
        self.canvas.unbind_all("<Button-5>")

    def _on_mousewheel(self, event):
        self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def _on_mousewheel_linux(self, event):
        delta = -1 if event.num == 4 else 1
        self.canvas.yview_scroll(delta, "units")

    # ─────────────────────────────────────────────────────────────────
    #  TEMA
    # ─────────────────────────────────────────────────────────────────
    def actualizar_tema(self, theme):
        """Vuelve a pintar el panel con la nueva paleta (oscuro/claro)."""
        self.theme = theme
        T = theme
        self.frame.config(bg=T["surface"], highlightbackground=T["border"])
        self.canvas.config(bg=T["surface"])
        self.frame_mensajes.config(bg=T["surface"])
        self.entrada.config(bg=T["bg"], fg=T["text"], insertbackground=T["accent"],
                             highlightbackground=T["border"], highlightcolor=T["accent"])
        self.btn_enviar.config(bg=T["accent"], fg=T["bg"],
                                activebackground=T["accent2"], activeforeground=T["text"])
        # Nota: las burbujas ya creadas conservan los colores con los que se
        # dibujaron; los mensajes nuevos usarán la paleta actualizada.