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
                 botones_solo_local=None, guardar_historial=None):
        """
        Inicializa todos los widgets de la barra de búsqueda y los coloca
        en el frame padre.

        Parámetros:
            parent (tk.Frame): Frame contenedor donde se colocarán los widgets.
            style (ttk.Style): Objeto de estilos de tkinter para personalizar apariencia.
            area_contenido (tk.Text): Widget de texto donde se renderiza el HTML.
            botones_habilitar (list): Botones que se habilitarán tras una carga exitosa
                                      (ej. Guardar, Guardar Como).
            boton_editar (ttk.Button | None): Botón "Editar Archivo"; se habilita solo
                                              en modo Local y se deshabilita en Online.
            botones_requieren_texto (list): Botones que se habilitan solo cuando hay
                                           texto en la barra (ej. Añadir Favorito).
            botones_solo_local (list): Botones que solo están disponibles en modo Local.
            guardar_historial (callable | None): Función callback que se llama tras
                                                 una carga exitosa para registrar la URL.

        Widgets creados:
            top_frame: Frame principal que contiene los controles de navegación.
            button_izq: Botón "⟳" para recargar/buscar la URL actual.
            button_mode: Menú desplegable para cambiar entre modo Online y Local.
            frame_buscador: Campo de texto (Entry) donde el usuario escribe la URL.
            button_ir: Botón "Ir" que dispara la búsqueda (deshabilitado si no hay texto).
            estado_frame: Frame con el indicador visual (círculo de color + label de modo).
            canvas_circulo: Canvas con un óvalo verde (Online) o rojo (Local).
            label_modo: Etiqueta que muestra el texto "Online" o "Local".
            estado_label: Etiqueta inferior con mensajes de estado (SUNKEN relief).
            progress: Barra de progreso indeterminada que se activa durante la carga.

        Callbacks configurados:
            on_titulo_cambio: Asignado externamente por GestorPestañas para actualizar
                              el título de la pestaña cuando se carga una página.
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

        # Callback para actualizar el título de la pestaña.
        # El GestorPestañas lo asigna al crear cada Pestaña.
        # Firma: on_titulo_cambio(nuevo_titulo: str)
        self.on_titulo_cambio = None

        # ── Variables ────────────────────────────────────────────────
        self.entrada_var    = tk.StringVar()   # Contenido del campo de texto
        self.barra_progreso = tk.StringVar()   # Mensaje en la barra de estado inferior
        self.modo_busqueda  = tk.StringVar(value="Online")  # Modo actual: "Online" o "Local"
        self.Status = True         # True = Online, False = Local
        self.url_correcta = 0      # Indicador auxiliar (no usado activamente)

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
            text="Online",
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
        self.circulo = self.canvas_circulo.create_oval(1, 1, 11, 11, fill="#5CB85C", outline="")

        self.label_modo = tk.Label(
            self.estado_frame,
            text="Online",
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
        # Observa cambios en el campo de texto para habilitar/deshabilitar botones
        self.entrada_var.trace_add("write", self._verificar_barra)

        # Enter dispara búsqueda solo si hay texto en el campo
        self.frame_buscador.bind("<Return>", self._enter_busqueda)

    def _cambiar_modo(self, modo: str):
        """
        Cambia el modo de búsqueda entre "Online" y "Local" y actualiza
        todos los elementos visuales e internos asociados al modo.

        Parámetros:
            modo (str): "Online" para búsqueda web, "Local" para archivos del sistema.

        Comportamiento:
            - Online: el círculo indicador se pone verde, self.Status = True,
              y los botones exclusivos de Local se deshabilitan.
            - Local: el círculo indicador se pone rojo, self.Status = False,
              y los botones exclusivos de Local se habilitan solo si hay
              una ruta actualmente cargada (self.ruta_actual).
        """
        self.modo_busqueda.set(modo)
        if modo == "Online":
            self.canvas_circulo.itemconfig(self.circulo, fill="#5CB85C")
            self.label_modo.config(text="Online")
            self.button_mode.configure(text="Online")
            self.Status = True
            for boton in self.botones_solo_local:
                boton.config(state="disabled")
        else:
            self.canvas_circulo.itemconfig(self.circulo, fill="#D9534F")
            self.label_modo.config(text="Local")
            self.button_mode.configure(text="Local")
            self.Status = False
            for boton in self.botones_solo_local:
                boton.config(state="normal" if self.ruta_actual else "disabled")

    def _verificar_barra(self, *args):
        """
        Callback del trace en entrada_var: habilita o deshabilita el botón "Ir"
        y los botones en botones_requieren_texto según si hay texto en el campo.

        Parámetros:
            *args: Argumentos estándar del trace de tkinter (nombre, índice, modo).
                   No se usan directamente.

        Comportamiento:
            - Si el campo tiene texto (no vacío): habilita el botón "Ir" y los
              botones en botones_requieren_texto.
            - Si el campo está vacío: los deshabilita.
        """
        texto = self.entrada_var.get().strip()
        estado = "normal" if texto else "disabled"
        self.button_ir.config(state=estado)
        for boton in self.botones_requieren_texto:
            boton.config(state=estado)

    def _enter_busqueda(self, event=None):
        """
        Manejador del evento <Return> (tecla Enter) en el campo de búsqueda.
        Dispara la búsqueda únicamente si el campo contiene texto.

        Parámetros:
            event: Evento de tkinter (no se usa directamente).
        """
        if self.entrada_var.get().strip():
            self.iniciar_busqueda()

    def iniciar_busqueda(self):
        """
        Punto de entrada principal para iniciar una búsqueda o carga de página.
        Valida la URL (en modo Online) y, si es correcta, activa la barra de
        progreso y programa la ejecución del proceso tras 3 segundos.

        Proceso en modo Online:
            1. Valida el formato y la extensión de la URL mediante URL_absoluta().
            2. Si ambas son correctas, muestra "Buscando..." y activa la progress bar.
            3. Programa _ejecutar_proceso() para ejecutarse después de 3000 ms.
            4. Si el formato es incorrecto, muestra un error de "http:// o https://".
            5. Si la extensión es inválida, muestra un error de extensión.

        Proceso en modo Local:
            - No valida la URL; simplemente activa la progress bar y programa
              _ejecutar_proceso() directamente.
        """
        formato_correcto, extencion_correcta = self.URL_absoluta()
        if self.Status == True:
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
        """
        Valida y normaliza la URL ingresada en el campo de búsqueda.
        Solo aplica en modo Online; en modo Local siempre retorna (True, True).

        Proceso:
            1. Si el campo está vacío, retorna (False, False).
            2. En modo Local, retorna (True, True) sin validación.
            3. En modo Online:
               a. Si falta el esquema (http:// o https://), lo agrega automáticamente
                  como "https://" y actualiza el campo de texto.
               b. Valida que el esquema sea "http" o "https".
               c. Extrae host y puerto; valida que el host no esté vacío.
               d. Si hay puerto, valida que sea un número entre 1 y 65535.
               e. Verifica que el host contenga al menos un punto (excepto "localhost").
               f. Comprueba que la extensión del dominio sea una de las permitidas:
                  .com, .org, .net, .io, .gov, .cl

        Retorna:
            tuple(bool, bool):
                - Primer bool: True si el formato del esquema y host es correcto.
                - Segundo bool: True si la extensión del dominio es válida.
        """
        entrada = self.entrada_var.get().strip()
        if not entrada:
            return False, False

        # En modo Local no se toca la entrada: es una ruta de archivo
        if not self.Status:
            return True, True

        # Solo modo Online: completar y validar esquema
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
        """
        Finaliza la animación de progreso y llama a verificar_existencia()
        para procesar la URL. Actualiza la barra de estado con el resultado.

        Proceso:
            1. Detiene la barra de progreso indeterminada.
            2. Muestra "Procesando datos..." en la barra de estado.
            3. Llama a verificar_existencia() para cargar el contenido.
            4. En modo Local, actualiza la barra de estado con "Listo" o "Error".
               (En modo Online, verificar_existencia() ya actualiza el estado.)
        """
        self.progress.stop()
        self.barra_progreso.set("Procesando datos...")
        resultado = self.verificar_existencia()
        if not self.Status:
            self.barra_progreso.set("Listo" if resultado else "Error")

    def _notificar_titulo(self, texto):
        """
        Invoca el callback on_titulo_cambio (si está configurado) para actualizar
        el título de la pestaña con el texto proporcionado.

        Parámetros:
            texto (str): Texto que se usará como título (URL o nombre de archivo).
                         Se recorta a 30 caracteres y se agrega "…" si es más largo.

        Nota:
            El callback on_titulo_cambio es asignado externamente por GestorPestañas.
        """
        if self.on_titulo_cambio:
            titulo = texto[:30] + ("…" if len(texto) > 30 else "")
            self.on_titulo_cambio(titulo)

    def verificar_existencia(self):
        """
        Carga y renderiza el contenido según el modo actual (Online o Local).

        Modo Online:
            1. Verifica que el campo no esté vacío.
            2. Crea un ClienteHTTP y llama a buscarurl() con la URL ingresada.
            3. Según el código de estado recibido:
               - 200: Renderiza el HTML, notifica el título, guarda en historial,
                      habilita botones y deshabilita el botón de editar.
               - 404: Muestra error "Página no encontrada".
               - None: Muestra error "No se pudo establecer conexión".
               - Otro: Muestra advertencia con el código recibido.
            4. En caso de excepción inesperada, muestra el mensaje de error.

        Modo Local:
            1. Verifica que el archivo exista en el sistema de archivos.
            2. Si el archivo no termina en .html, pide confirmación al usuario.
            3. Llama a parser.renderizar() con la ruta del archivo.
            4. Notifica el título con el nombre base del archivo.
            5. Guarda en historial, habilita botones y activa el botón de editar.

        Retorna:
            bool: True si la carga fue exitosa, False si ocurrió algún error.
        """
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
                    self._notificar_titulo(texto)
                    if self.guardar_historial:
                        self.guardar_historial()
                    for boton in self.botones_habilitar:
                        boton.config(state="normal")
                    if self.boton_editar:
                        self.boton_editar.config(state="disabled")  # online: no editable
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
            self._notificar_titulo(os.path.basename(texto))
            if self.guardar_historial:
                self.guardar_historial()
            for boton in self.botones_habilitar:
                boton.config(state="normal")
            if self.boton_editar:
                self.boton_editar.config(state="normal")
            return True

        except Exception as e:
            messagebox.showerror("Error", f"Ocurrió un error:\n{e}")
            return False

    def get_ruta_actual(self):
        """
        Retorna la ruta del archivo local actualmente cargado.

        Retorna:
            str: La ruta del archivo, o cadena vacía si no hay ninguno cargado.
        """
        return self.ruta_actual

    def get_modo_busqueda(self):
        """
        Retorna el modo de búsqueda actual como string.

        Retorna:
            str: "Online" o "Local" según el modo seleccionado.
        """
        return self.modo_busqueda.get()

    def actualizar_tema(self, bg_frame, bg_entry, fg_entry, bg_boton, fg_boton, active_bg):
        """
        Actualiza los colores de todos los widgets de la barra para adaptarse
        a un tema claro u oscuro.

        Parámetros:
            bg_frame (str): Color de fondo del frame contenedor y elementos auxiliares.
            bg_entry (str): Color de fondo del campo de texto (Entry).
            fg_entry (str): Color del texto dentro del Entry.
            bg_boton (str): Color de fondo de los botones.
            fg_boton (str): Color del texto de los botones y del label de modo.
            active_bg (str): Color de fondo de los botones al pasar el cursor encima.

        Widgets actualizados:
            top_frame, estado_frame, canvas_circulo, label_modo,
            entry.TEntry (fieldbackground, foreground),
            button.TButton (background, foreground, active states).
        """
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