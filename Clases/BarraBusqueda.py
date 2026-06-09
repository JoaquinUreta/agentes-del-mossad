import os
import tkinter as tk
from tkinter import ttk, messagebox, SUNKEN
from Renderizador import RenderizadorParser
from ClienteHTTP import ClienteHTTP


class BarraBusqueda:
    """
    Componente de interfaz que representa la barra de navegación del explorador.
    Incluye un campo de texto para ingresar URLs o rutas, botones de acción,
    un selector de modo (Online/Local), un indicador visual de estado de conexión,
    una barra de progreso y una etiqueta de estado inferior.

    Se comunica con RenderizadorParser para mostrar el HTML en el área de contenido
    y con ClienteHTTP para realizar peticiones web en modo Online.
    """

    def __init__(self, parent, style, area_contenido, botones_habilitar=None,
                 boton_editar=None, botones_requieren_texto=None,
                 botones_solo_local=None, guardar_historial=None,
                 on_modo_cambio=None,navegador=None):
        """
        Inicializa todos los widgets de la barra de búsqueda y los coloca
        en el frame padre.
        """
        self.parent = parent
        self.style = style
        self.area_contenido = area_contenido
        self.botones_habilitar = botones_habilitar or []
        self.boton_editar = boton_editar
        self.botones_requieren_texto = botones_requieren_texto or []
        self.botones_solo_local = botones_solo_local or []
        self.ruta_actual = ""
        self.guardar_historial = guardar_historial
        self.on_modo_cambio = on_modo_cambio
        self.navegador=navegador
        self._navegacion_interna = False

        # Callback para actualizar el título de la pestaña.
        self.on_titulo_cambio = None

        # ── Variables de Estado ──────────────────────────────────────
        self.entrada_var = tk.StringVar()
        self.barra_progreso = tk.StringVar()
        self.modo_busqueda = tk.StringVar(value="Online")
        self.Status = True  # True = Online, False = Local
        self.url_correcta = 0

        # ── Frame Superior Contenedor ─────────────────────────────────
        self.top_frame = tk.Frame(parent, bg="#E4E2E2")
        self.top_frame.columnconfigure(0, weight=0)
        self.top_frame.columnconfigure(1, weight=0)
        self.top_frame.columnconfigure(2, weight=0)
        self.top_frame.columnconfigure(3, weight=0)
        self.top_frame.columnconfigure(4, weight=1)
        self.top_frame.columnconfigure(5, weight=0)

        # ── Estilos ──────────────────────────────────────────────────
        self.style.configure("button.TButton", background="#FFFFFF", foreground="#000")
        self.style.map(
            "button.TButton",
            background=[("active", "#E4E2E2")],
            foreground=[("active", "#000")]
        )
        self.style.configure("entry.TEntry", fieldbackground="#FFFFFF", foreground="#000")

         # ── Botón Atrás ──────────────────────────────────────────────
        self.button_atras = ttk.Button(
             self.top_frame,
             text="←",
             style="button.TButton",
             command=self.ir_atras,
             state="disabled"
             )
        self.button_atras.grid(row=0, column=0, padx=(0, 3))

        # ── Botón Adelante ───────────────────────────────────────────
        self.button_adelante = ttk.Button(
             self.top_frame,
             text="→",
             style="button.TButton",
             command=self.ir_adelante,
             state="disabled"
             )
        self.button_adelante.grid(row=0, column=1, padx=(0, 3))

        # ── Botón Recargar ───────────────────────────────────────────
        self.button_izq = ttk.Button(
            self.top_frame,
            text="⟳",
            style="button.TButton",
            command=self.iniciar_busqueda
        )
        self.button_izq.grid(row=0, column=2, padx=(0, 5))

        # ── Botón Modo de Búsqueda (Menú Desplegable) ──────────────────
        self.button_mode = ttk.Menubutton(
            self.top_frame,
            text="Online",
            style="Custom.TMenubutton"
        )
        menumode = tk.Menu(self.button_mode, tearoff=0)
        self.button_mode.grid(row=0, column=3, padx=(0, 5))
        self.button_mode["menu"] = menumode
        menumode.add_command(label="Búsqueda Local",  command=lambda: self._cambiar_modo("Local"))
        menumode.add_command(label="Búsqueda Online", command=lambda: self._cambiar_modo("Online"))

        # ── Campo de Entrada (Buscador) ────────────────────────────────
        self.frame_buscador = ttk.Entry(
            self.top_frame,
            style="entry.TEntry",
            textvariable=self.entrada_var,
            width=60
        )
        self.frame_buscador.grid(row=0, column=4, sticky="ew", padx=(0, 5))

        # ── Botón Ir ─────────────────────────────────────────────────
        self.button_ir = ttk.Button(
            self.top_frame,
            text="Ir",
            style="button.TButton",
            state="disabled",
            command=self.iniciar_busqueda
        )
        self.button_ir.grid(row=0, column=5)

        # ── Indicador Visual Online / Local ───────────────────────────
        self.estado_frame = tk.Frame(self.top_frame, bg="#E4E2E2")
        self.estado_frame.grid(row=1, column=0, columnspan=2, sticky="w", pady=(3, 0))

        self.canvas_circulo = tk.Canvas(
            self.estado_frame,
            width=12, height=12,
            bg="#E4E2E2",
            highlightthickness=0
        )
        self.canvas_circulo.pack(side="left", padx=(0, 4))
        self.circulo = self.canvas_circulo.create_oval(1, 1, 11, 11, fill="#5CB85C", outline="")

        self.label_modo = tk.Label(
            self.estado_frame,
            text="Online",
            bg="#E4E2E2",
            fg="#555555",
            font=("Segoe UI", 8)
        )
        self.label_modo.pack(side="left")

        # ── Elementos Inferiores (Barra de Estado y Progreso) ──────────
        self.estado_label = tk.Label(
            parent,
            textvariable=self.barra_progreso,
            bd=3,
            relief=SUNKEN,
            anchor="w"
        )
        self.progress = ttk.Progressbar(
            parent,
            orient="horizontal",
            length=300,
            mode="indeterminate"
        )

        # ── Traces y Binds ───────────────────────────────────────────
        self.entrada_var.trace_add("write", self._verificar_barra)
        self.frame_buscador.bind("<Return>", self._enter_busqueda)

    def aplicar_modo(self, modo: str, emitir_evento: bool = True):
        """Actualiza el estado visual y lógico del modo de búsqueda."""
        self.modo_busqueda.set(modo)
        if modo == "Online":
            self.canvas_circulo.itemconfig(self.circulo, fill="#5CB85C")
            self.label_modo.config(text="Online")
            self.button_mode.configure(text="Online")
            self.Status = True
            for _boton in self.botones_solo_local:
                _boton.config(state="disabled")
        else:
            self.canvas_circulo.itemconfig(self.circulo, fill="#D9534F")
            self.label_modo.config(text="Local")
            self.button_mode.configure(text="Local")
            self.Status = False
            for _boton in self.botones_solo_local:
                _boton.config(state="normal" if self.ruta_actual else "disabled")

        if emitir_evento and self.on_modo_cambio is not None:
            self.on_modo_cambio(modo)

    def _cambiar_modo(self, modo: str):
        "Maneja el cambio visual y lógico entre Online y Local"
        self.aplicar_modo(modo, emitir_evento=True)

    def _verificar_barra(self, *args):
        texto = self.entrada_var.get().strip()
        estado = "normal" if texto else "disabled"
        self.button_ir.config(state=estado)
        for _boton in self.botones_requieren_texto:
            _boton.config(state=estado)

    def _enter_busqueda(self, event=None):
        if self.entrada_var.get().strip():
            self.iniciar_busqueda()

    def navegar_desde_hipervinculo(self, url):
        """
        Callback llamado por el RenderizadorParser al hacer click en un enlace.
        Resuelve automáticamente si es local o remoto, ajusta el modo y navega.
        """
        if url.startswith(("http://", "https://", "www.")):
            self._cambiar_modo("Online")
            self.entrada_var.set(url)
        else:
            if self.Status:  
                url_actual = self.entrada_var.get().strip()
                from urllib.parse import urljoin
                nueva_url = urljoin(url_actual, url)
                self._cambiar_modo("Online")
                self.entrada_var.set(nueva_url)
            else:  
                if self.ruta_actual:
                    carpeta_actual = os.path.dirname(self.ruta_actual)
                    ruta_completa = os.path.normpath(os.path.join(carpeta_actual, url))
                else:
                    ruta_completa = os.path.abspath(url)
                self._cambiar_modo("Local")
                self.entrada_var.set(ruta_completa)

        self.iniciar_busqueda()

    def iniciar_busqueda(self):
        formato_correcto, extencion_correcta = self.URL_absoluta()
        if self.Status:
            if formato_correcto and extencion_correcta:
                self.barra_progreso.set("Buscando...")
                self.progress.start(10)
                self.parent.after(3000, self._ejecutar_proceso)
                return
            if not formato_correcto:
                messagebox.showerror("error de entrada", "La URL debe comenzar con http:// o https://")
                return
            if not extencion_correcta:
                messagebox.showerror("error de entrada", "La URL no tiene una extensión válida")
                return
        else:
            self.barra_progreso.set("Buscando...")
            self.progress.start(10)
            self.parent.after(3000, self._ejecutar_proceso)

    def URL_absoluta(self):
        entrada = self.entrada_var.get().strip()
        if not entrada:
            return False, False

        if not self.Status:
            return True, True

        if not entrada.lower().startswith(("http://", "https://")):
            entrada = "https://" + entrada
            self.entrada_var.set(entrada)
        if "://" not in entrada:
            return False, False
        esquema, resto = entrada.split("://", 1)
        esquema = esquema.lower()
        if esquema not in ("http", "https"):
            return False, False
        host_port, _, _ = resto.partition("/")
        if not host_port:
            return False, False
        host, sep, port = host_port.partition(":")
        host = host.lower()
        if not host:
            return False, False
        if sep:
            if not port.isdigit() or not (1 <= int(port) <= 65535):
                return False, False
        if host == "localhost":
            return True, True
        if "." not in host:
            return False, False
        extencion = host.split(".")[-1].lower()
        if extencion in ["com", "org", "net", "io", "gov", "cl"]:
            return True, True
        return True, False

    def _ejecutar_proceso(self):
        self.progress.stop()
        self.barra_progreso.set("Procesando datos...")
        resultado = self.verificar_existencia()
        if not self.Status:
            self.barra_progreso.set("Listo" if resultado else "Error")
        self._actualizar_botones_navegacion()

    def _notificar_titulo(self, texto):
        if self.on_titulo_cambio:
            titulo = texto[:30] + ("…" if len(texto) > 30 else "")
            self.on_titulo_cambio(titulo)

    def verificar_existencia(self):
        texto = self.entrada_var.get().strip()
        # Se inyecta 'self.navegar_desde_hipervinculo' para conectar el click con este componente
        parser = RenderizadorParser(self.area_contenido, callback_navegacion=self.navegar_desde_hipervinculo)

        # ── Flujo Modo Online ─────────────────────────────────────────
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
                    parser.renderizar_desde_string(html_string, ruta_base=texto)
                    if self.navegador and not self._navegacion_interna:#Guarda en NavegaAvanzada la url actual
                        self.navegador.navegar(texto)
                        self._actualizar_botones_navegacion()
                    self._notificar_titulo(texto)
                    if self.guardar_historial:
                        self.guardar_historial()
                    for _boton in self.botones_habilitar:
                        _boton.config(state="normal")
                    if self.boton_editar:
                        self.boton_editar.config(state="disabled")
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

        # ── Flujo Modo Local ──────────────────────────────────────────
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
            if self.navegador and not self._navegacion_interna:
                self.navegador.navegar(texto)
                self._actualizar_botones_navegacion()
            self._notificar_titulo(os.path.basename(texto))
            if self.guardar_historial:
                self.guardar_historial()
            for _boton in self.botones_habilitar:
                _boton.config(state="normal")
            if self.boton_editar:
                self.boton_editar.config(state="normal")
            return True
        except Exception as e:
            messagebox.showerror("Error", f"Ocurrió un error:\n{e}")
            return False

    def get_ruta_actual(self):
        return self.ruta_actual

    def get_modo_busqueda(self):
        return self.modo_busqueda.get()
    
    def ir_atras(self):
        if not self.navegador:
            return
        url = self.navegador.atras()
        if url:#Si se encuentra una url del arreglo navegador,el boton puede hacer la anterior busqueda
            self._navegacion_interna = True
            try:
                self.entrada_var.set(url)
                self._actualizar_botones_navegacion()
                self.iniciar_busqueda()
            finally:
                self._navegacion_interna = False
            self._actualizar_botones_navegacion()
        
    def ir_adelante(self):
        if not self.navegador:
            return
        url = self.navegador.adelante()
        if url:#Si se encuentra una url del arreglo navegador,el boton puede hacer la busqueda siguiente            self._navegacion_interna = True
            try:
                self.entrada_var.set(url)
                self._actualizar_botones_navegacion()
                self.iniciar_busqueda()
            finally:
                self._navegacion_interna = False
        self._actualizar_botones_navegacion()
        
    def _actualizar_botones_navegacion(self):
        if not self.navegador:
            return
        if self.navegador.puede_atras():
            self.button_atras.config(state="normal")
        else:#Desahabilita boton atras si no hay elementos
            self.button_atras.config(state="disabled")
        if self.navegador.puede_adelante():
            self.button_adelante.config(state="normal")
        else:#Desahabilita boton adelante si no hay elementos
            self.button_adelante.config(state="disabled")
    

    def actualizar_tema(self, bg_frame, bg_entry, fg_entry, bg_boton, fg_boton, active_bg):
        self.top_frame.config(bg=bg_frame)
        self.estado_frame.config(bg=bg_frame)
        self.canvas_circulo.config(bg=bg_frame)
        self.label_modo.config(bg=bg_frame, fg=fg_boton)
        self.style.configure("entry.TEntry", fieldbackground=bg_entry, foreground=fg_entry)
        self.style.configure("button.TButton", background=bg_boton, foreground=fg_boton)
        self.style.map("button.TButton", background=[("active", active_bg)], foreground=[("active", fg_boton)])