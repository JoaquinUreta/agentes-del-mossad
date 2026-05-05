import tkinter as tk
from tkinter import ttk, messagebox, SUNKEN
from Renderizador import RenderizadorParser
from ClienteHTTP import ClienteHTTP


class BarraBusqueda:
    def __init__(self, parent, style, area_contenido, botones_habilitar=None, boton_editar=None, botones_requieren_texto=None, botones_solo_local=None):

        self.parent = parent
        self.style = style
        self.area_contenido = area_contenido
        self.botones_habilitar = botones_habilitar or []
        self.boton_editar = boton_editar
        self.botones_requieren_texto = botones_requieren_texto or []
        self.botones_solo_local = botones_solo_local or []
        self.ruta_actual = ""

        # ── Variables ────────────────────────────────────────────────
        self.entrada_var    = tk.StringVar()
        self.barra_progreso = tk.StringVar()
        self.modo_busqueda  = tk.StringVar(value="Local")
        self.Status = False
        self.url_correcta = 0

        # ── Top frame ────────────────────────────────────────────────
        self.top_frame = tk.Frame(parent, bg="#E4E2E2")
        self.top_frame.columnconfigure(0, weight=0)
        self.top_frame.columnconfigure(1, weight=0)
        self.top_frame.columnconfigure(2, weight=1)
        self.top_frame.columnconfigure(3, weight=0)

        # ── Estilos ──────────────────────────────────────────────────
        self.style.configure("button.TButton", background="#FFFFFF", foreground="#000")
        self.style.map(
            "button.TButton",
            background=[("active", "#E4E2E2")],
            foreground=[("active", "#000")]
        )
        self.style.configure("entry.TEntry", fieldbackground="#FFFFFF", foreground="#000")

        # ── Botón Recargar ───────────────────────────────────────────
        self.button_izq = ttk.Button(
            self.top_frame,
            text="⟳",
            style="button.TButton",
            command=self.iniciar_busqueda
        )
        self.button_izq.grid(row=0, column=0, padx=(0, 5))

        # ── Botón Modo de Búsqueda ───────────────────────────────────
        self.button_mode = ttk.Menubutton(
            self.top_frame,
            text="Local",
            style="Custom.TMenubutton"
        )
        menumode = tk.Menu(self.button_mode, tearoff=0)
        self.button_mode.grid(row=0, column=1, padx=(0, 5))
        self.button_mode["menu"] = menumode
        menumode.add_command(label="Búsqueda Local",  command=lambda: self._cambiar_modo("Local"))
        menumode.add_command(label="Búsqueda Online", command=lambda: self._cambiar_modo("Online"))

        # ── Entry de búsqueda ────────────────────────────────────────
        self.frame_buscador = ttk.Entry(
            self.top_frame,
            style="entry.TEntry",
            textvariable=self.entrada_var,
            width=60
        )
        self.frame_buscador.grid(row=0, column=2, sticky="ew", padx=(0, 5))

        # ── Botón Ir ─────────────────────────────────────────────────
        self.button_ir = ttk.Button(
            self.top_frame,
            text="Ir",
            style="button.TButton",
            state="disabled",
            command=self.iniciar_busqueda
        )
        self.button_ir.grid(row=0, column=3)

        # ── Indicador Online / Offline ────────────────────────────────
        self.estado_frame = tk.Frame(self.top_frame, bg="#E4E2E2")
        self.estado_frame.grid(row=1, column=0, columnspan=2, sticky="w", pady=(3, 0))

        self.canvas_circulo = tk.Canvas(
            self.estado_frame,
            width=12, height=12,
            bg="#E4E2E2",
            highlightthickness=0
        )
        self.canvas_circulo.pack(side="left", padx=(0, 4))
        self.circulo = self.canvas_circulo.create_oval(1, 1, 11, 11, fill="#D9534F", outline="")

        self.label_modo = tk.Label(
            self.estado_frame,
            text="Offline",
            bg="#E4E2E2",
            fg="#555555",
            font=("Segoe UI", 8)
        )
        self.label_modo.pack(side="left")

        # ── Barra de estado ──────────────────────────────────────────
        self.estado_label = tk.Label(
            parent,
            textvariable=self.barra_progreso,
            bd=3,
            relief=SUNKEN,
            anchor="w"
        )

        # ── Barra de carga ───────────────────────────────────────────
        self.progress = ttk.Progressbar(
            parent,
            orient="horizontal",
            length=300,
            mode="indeterminate"
        )

        # ── Trace ────────────────────────────────────────────────────
        self.entrada_var.trace_add("write", self._verificar_barra)

    # ── Cambio de modo ────────────────────────────────────────────────
    def _cambiar_modo(self, modo: str):
        self.modo_busqueda.set(modo)
        if modo == "Online":
            self.canvas_circulo.itemconfig(self.circulo, fill="#5CB85C")
            self.label_modo.config(text="Online")
            self.button_mode.configure(text="Online")
            self.Status = True
            # Deshabilitar botones de edición local
            for boton in self.botones_solo_local:
                boton.config(state="disabled")
        else:
            self.canvas_circulo.itemconfig(self.circulo, fill="#D9534F")
            self.label_modo.config(text="Local")
            self.button_mode.configure(text="Local")
            self.Status = False
            # Rehabilitar botones solo si hay un archivo abierto
            for boton in self.botones_solo_local:
                boton.config(state="normal" if self.ruta_actual else "disabled")
    def _verificar_barra(self, *args):
        texto = self.entrada_var.get().strip()
        estado = "normal" if texto else "disabled"
        self.button_ir.config(state=estado)
        for boton in self.botones_requieren_texto:
            boton.config(state=estado)

    def iniciar_busqueda(self):
        if self.Status == True:
            if self.url_correcta == 1:
                self.barra_progreso.set("Buscando...")
                self.progress.start(10)
                self.parent.after(3000, self._ejecutar_proceso)
            if self.url_correcta == 0:
                messagebox.showerror("error de entrada", "la URL no tiene el formato correcto")
        if self.Status == False:
            self.barra_progreso.set("Buscando...")
            self.progress.start(10)
            self.parent.after(3000, self._ejecutar_proceso)

    def URL_absoluta(self):
        if self.entrada_var.get.split("://")[0] == "http" or self.entrada_var.get.split("://")[0] == "https":
            self.url_correcta=set_url_estado(self)
        url_separada_v2 = self.entrada_var.get().split(".")
        extencion = url_separada_v2[-1]
        if extencion != "com" or extencion != "cl":
            messagebox.showerror("error de entrada", "la URL localhost no tiene el formato correcto")
        
        def set_url_estado(self):
            if self.url_correcta==1:
                self.url_correcta=0
            if self.url_correcta==0:
                self.url_correcta=1
    def _ejecutar_proceso(self):
        self.progress.stop()
        self.barra_progreso.set("Procesando datos...")
        resultado = self.verificar_existencia()  # recibe el estado
        # Solo sobreescribe la barra si NO estamos en modo Online
        # (en Online, verificar_existencia ya puso 200 OK / 404 / error)
        if not self.Status:
            self.barra_progreso.set("Listo" if resultado else "Error")

    def verificar_existencia(self):
        import os
        texto = self.entrada_var.get().strip()
        parser = RenderizadorParser(self.area_contenido)

        # ── Modo Online ───────────────────────────────────────────────
        if self.Status:
            if not texto:
                messagebox.showerror("Error", "El campo está vacío")
                return False
            try:
                self.barra_progreso.set(f"Cargando {texto}...")
                self.parent.update_idletasks()

                cliente = ClienteHTTP()
                html_string, status = cliente.buscarurl(texto)

                if status == 200:
                    self.barra_progreso.set(f"200 OK — {texto}")
                    parser.renderizar_desde_string(html_string, ruta_base="")
                    for boton in self.botones_habilitar:
                        boton.config(state="normal")
                    if self.boton_editar:
                        self.boton_editar.config(state="normal")
                    return True

                elif status == 404:
                    self.barra_progreso.set(f"404 Not Found — {texto}")
                    messagebox.showerror("Error", f"Página no encontrada: {texto}")
                    return False

                elif status is None:
                    self.barra_progreso.set("Error — No se pudo conectar")
                    messagebox.showerror("Error", "No se pudo establecer conexión")
                    return False

                else:
                    self.barra_progreso.set(f"{status} — {texto}")
                    messagebox.showwarning("Aviso", f"El servidor respondió con código {status}")
                    return False

            except Exception as e:
                self.barra_progreso.set("Error inesperado")
                messagebox.showerror("Error", f"Ocurrió un error al conectar:\n{e}")
                return False

        # ── Modo Local ────────────────────────────────────────────────
        if not os.path.isfile(texto):
            messagebox.showerror("Error", "El archivo no existe")
            return False

        if not texto.lower().endswith(".html"):
            continuar = messagebox.askyesno(
                "Advertencia",
                "Tu archivo no es un HTML, ¿desea abrirlo de todas formas?"
            )
            if not continuar:
                return False

        try:
            self.ruta_actual = texto
            parser.renderizar(self.ruta_actual)

            for boton in self.botones_habilitar:
                boton.config(state="normal")
            if self.boton_editar:
                es_html = texto.lower().endswith(".html")
                self.boton_editar.config(state="disabled" if es_html else "normal")
            return True

        except Exception as e:
            messagebox.showerror("Error", f"Ocurrió un error:\n{e}")
            return False

    def get_ruta_actual(self):
        return self.ruta_actual

    def get_modo_busqueda(self):
        return self.modo_busqueda.get()

    def actualizar_tema(self, bg_frame, bg_entry, fg_entry, bg_boton, fg_boton, active_bg):
        self.top_frame.config(bg=bg_frame)
        self.estado_frame.config(bg=bg_frame)
        self.canvas_circulo.config(bg=bg_frame)
        self.label_modo.config(bg=bg_frame, fg=fg_boton)
        self.style.configure("entry.TEntry",
                              fieldbackground=bg_entry,
                              foreground=fg_entry)
        self.style.configure("button.TButton",
                              background=bg_boton,
                              foreground=fg_boton)
        self.style.map("button.TButton",
                       background=[("active", active_bg)],
                       foreground=[("active", fg_boton)])