import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from BarraBusqueda import BarraBusqueda
from Historial import Historial


class Pestaña:
    """
    Encapsula todo el estado y los widgets de una pestaña individual del navegador.
    Cada instancia tiene su propio area_contenido, BarraBusqueda e Historial,
    por lo que cada pestaña navega de forma completamente independiente.

    Estructura visual de cada pestaña:
        - Fila 0: Barra de búsqueda (top_frame de BarraBusqueda).
        - Fila 1: Sidebar (izquierda) + área principal con el texto renderizado (derecha).
        - Fila 2: Etiqueta de estado (estado_label de BarraBusqueda).
        - Fila 3: Barra de progreso (progress de BarraBusqueda).
    """

    def __init__(self, notebook, style, buttons_frame_global, menu_savedurl, menu_historial_global):
        """
        Crea todos los widgets de la pestaña, instancia su BarraBusqueda e Historial,
        y registra los botones de acción en la barra global de botones.

        Parámetros:
            notebook (ttk.Notebook): Notebook padre donde se añade esta pestaña.
            style (ttk.Style): Objeto de estilos compartido para personalizar la apariencia.
            buttons_frame_global (tk.Frame): Frame global (en la top_bar de VentanaPrincipal)
                                            donde se colocan los botones de esta pestaña.
            menu_savedurl (tk.Menu): Menú de URLs favoritas compartido globalmente.
            menu_historial_global (callable | None): Función para actualizar el menú
                                                    de historial global al navegar.

        Botones creados (en buttons_frame_global):
            boton_editar: Habilita la edición del archivo local en el área de texto.
            boton_guardar: Guarda el contenido del área en el archivo local actual.
            boton_guardar_como: Guarda el contenido con un nombre/ruta nuevo.
            fav_btn: Añade la URL actual a la lista de favoritas.

        Todos los botones inician deshabilitados (state="disabled").
        """
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

    def _actualizar_titulo_tab(self, titulo: str):
        """
        Actualiza el texto visible de esta pestaña en el ttk.Notebook.
        Es invocado como callback desde BarraBusqueda.on_titulo_cambio
        cuando se carga una página exitosamente.

        Parámetros:
            titulo (str): Texto a mostrar en la etiqueta de la pestaña
                          (ya recortado a 30 caracteres por BarraBusqueda).

        Nota:
            Si la pestaña ya no existe en el notebook (fue cerrada), la excepción
            se captura silenciosamente.
        """
        try:
            self.notebook.tab(self.frame, text=titulo)
        except Exception:
            pass

    def _guardar_menuhistorial(self):
        """
        Registra la URL actual en el historial propio de la pestaña y
        dispara la actualización del menú de historial global en la ventana principal.

        Proceso:
            1. Obtiene la URL del campo de búsqueda de la barra.
            2. Si hay texto, lo agrega al historial de esta pestaña.
            3. Si hay un callback global de historial configurado, lo invoca
               para que VentanaPrincipal refresque su menú de historial.

        Nota:
            Este método se pasa como callback 'guardar_historial' a BarraBusqueda,
            que lo llama después de cada carga exitosa.
        """
        urlactual = self.barra.entrada_var.get().strip()
        if not urlactual:
            return
        self.historial.agregar_historial(urlactual)
        if self._menu_historial_global is not None:
            self._menu_historial_global()

    def _editar_archivo(self):
        """
        Solicita confirmación al usuario y, si acepta, habilita el área de texto
        para edición directa. Si rechaza, deja el área en modo solo lectura.

        Muestra un diálogo de confirmación (Yes/No).
        Si el usuario acepta: area_contenido.config(state="normal").
        Si rechaza: area_contenido.config(state="disabled").
        """
        respuesta = messagebox.askyesno("Editar", "¿Deseas editar este documento?")
        if respuesta:
            self.area_contenido.config(state="normal")
        else:
            self.area_contenido.config(state="disabled")

    def _guardar_archivo(self, ruta_destino=None):
        """
        Guarda el contenido actual del área de texto en un archivo del sistema.

        Parámetros:
            ruta_destino (str | None): Ruta donde guardar el archivo.
                Si es None, se usa la ruta del archivo actualmente cargado
                (self.barra.get_ruta_actual()). Si tampoco hay ruta activa,
                muestra una advertencia y no hace nada.

        Proceso:
            1. Determina la ruta de destino.
            2. Habilita temporalmente el área de texto para leer su contenido.
            3. Escribe el contenido en el archivo con codificación UTF-8.
            4. Deshabilita el área de texto nuevamente.
            5. Muestra un diálogo de éxito o de error según el resultado.
        """
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
        """
        Abre un diálogo "Guardar Como" para que el usuario elija nombre y ubicación
        del archivo, luego delega el guardado a _guardar_archivo().

        Proceso:
            1. Abre filedialog.asksaveasfilename() sin restricción de tipo de archivo.
            2. Si el usuario cancela (ruta vacía), no hace nada.
            3. Si elige una ruta, llama a _guardar_archivo(ruta) para escribir el archivo.
        """
        ruta = filedialog.asksaveasfilename(
            defaultextension=".*",
            filetypes=[("Todos los archivos", "*.*")]
        )
        if not ruta:
            return
        self._guardar_archivo(ruta)

    def _añadir_fav(self, menu_savedurl):
        """
        Añade la URL actual al menú de URLs favoritas, verificando que no esté
        duplicada y que no se supere el límite de 10 favoritos.

        Parámetros:
            menu_savedurl (tk.Menu): Menú compartido donde se agregan las URLs favoritas.

        Proceso:
            1. Obtiene la URL actual del campo de búsqueda.
            2. Recorre las entradas existentes del menú para verificar duplicados.
            3. Si ya existe la URL, muestra una advertencia y no la agrega.
            4. Si hay menos de 10 favoritos, agrega la URL como nuevo comando en el menú.
               Al hacer click en la entrada del menú se carga la URL en la pestaña activa.
            5. Si ya hay 10 favoritos, muestra un error.
        """
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
        """
        Carga una URL en la pestaña activa del navegador.
        Este método actúa como un placeholder: es sobreescrito por VentanaPrincipal
        mediante monkey-patching (Pestaña._cargar_url_global = ...) para delegar
        la acción al GestorPestañas.

        Parámetros:
            url (str): URL a cargar en la pestaña activa.

        Nota:
            En su estado base (sin sobreescritura), no hace nada.
            VentanaPrincipal lo reemplaza con: lambda p, url: gestor.cargar_url_en_activa(url)
        """
        pass

    def mostrar_botones(self):
        """
        Hace visibles los botones propios de esta pestaña en el frame global de botones.
        Se llama cuando esta pestaña se convierte en la pestaña activa del Notebook.

        Botones mostrados: boton_editar, boton_guardar, boton_guardar_como, fav_btn.
        Todos se colocan con pack(side="left") en el buttons_frame_global.
        """
        for b in (self.boton_editar, self.boton_guardar, self.boton_guardar_como, self.fav_btn):
            b.pack(side="left", padx=3)

    def ocultar_botones(self):
        """
        Oculta los botones propios de esta pestaña del frame global de botones.
        Se llama cuando esta pestaña deja de ser la activa o cuando se cierra.

        Usa pack_forget() para remover los botones del layout sin destruirlos,
        permitiendo volver a mostrarlos con mostrar_botones() si fuera necesario.
        """
        for b in (self.boton_editar, self.boton_guardar, self.boton_guardar_como, self.fav_btn):
            b.pack_forget()

    def actualizar_tema(self, oscuro: bool):
        """
        Actualiza los colores de todos los widgets de la pestaña para adaptarse
        al tema claro u oscuro de la aplicación.

        Parámetros:
            oscuro (bool): True para aplicar el tema oscuro, False para el claro.

        Tema oscuro:
            - frame: #2E2E2E, sidebar: #444444, main_area: #3C3C3C
            - area_contenido: fondo #1E1E1E, texto #EEEEEE
            - BarraBusqueda: colores oscuros para entry, botones y frame.

        Tema claro:
            - frame: #EDECEC, sidebar: #EDECEC, main_area: #FFFFFF
            - area_contenido: fondo #FFFFFF, texto #000000
            - BarraBusqueda: colores claros para entry, botones y frame.
        """
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


class GestorPestañas:
    """
    Administra la colección de pestañas dentro del ttk.Notebook.
    Es responsable de crear, cerrar y cambiar entre pestañas, así como
    de coordinar la visibilidad de los botones según la pestaña activa
    y de propagar cambios de tema a todas las pestañas.
    """

    def __init__(self, notebook, style, buttons_frame, menu_savedurl):
        """
        Inicializa el gestor y configura el evento de cambio de pestaña.

        Parámetros:
            notebook (ttk.Notebook): Componente de pestañas de tkinter.
            style (ttk.Style): Estilos compartidos de la aplicación.
            buttons_frame (tk.Frame): Frame global donde se muestran los botones
                                      de la pestaña activa.
            menu_savedurl (tk.Menu): Menú de URLs favoritas, compartido entre pestañas.

        Atributos internos:
            pestañas (list[Pestaña]): Lista de todas las instancias de Pestaña activas.
            _tema_oscuro (bool): Estado del tema actual (False = claro).
            _menu_historial_ref (callable | None): Callback para actualizar el menú
                                                   de historial global.
        """
        self.notebook       = notebook
        self.style          = style
        self.buttons_frame  = buttons_frame
        self.menu_savedurl  = menu_savedurl
        self.pestañas: list[Pestaña] = []
        self._tema_oscuro   = False
        self._menu_historial_ref = None

        self.notebook.bind("<<NotebookTabChanged>>", self._on_tab_changed)

    def set_menu_historial_callback(self, cb):
        """
        Registra la función callback que se invocará cada vez que se necesite
        actualizar el menú de historial global (en VentanaPrincipal).

        Parámetros:
            cb (callable): Función sin argumentos que actualiza el menú de historial.
                           Generalmente es VentanaPrincipal._actualizar_menu_historial.
        """
        self._menu_historial_ref = cb

    def _actualizar_historial_global(self):
        """
        Obtiene la URL actual de la pestaña activa y la registra en el historial global.
        Luego llama al callback del menú de historial si está configurado.

        Nota:
            Este método no es llamado directamente en el flujo actual; el historial
            se actualiza desde _guardar_menuhistorial() en cada Pestaña.
        """
        pestaña = self.pestaña_activa()
        if not pestaña:
            return
        url = pestaña.barra.entrada_var.get().strip()
        if url:
            self._historial_global.agregar_historial(url)
        if self._menu_historial_ref:
            self._menu_historial_ref()

    def nueva_pestaña(self, titulo="Nueva pestaña"):
        """
        Crea una nueva instancia de Pestaña, la agrega al Notebook y la selecciona.

        Parámetros:
            titulo (str): Texto inicial de la etiqueta de la pestaña.
                          Por defecto es "Nueva pestaña".

        Proceso:
            1. Instancia un nuevo objeto Pestaña con la configuración actual.
            2. Aplica el tema actual (claro u oscuro) a la nueva pestaña.
            3. Agrega la pestaña a la lista interna self.pestañas.
            4. Añade el frame de la pestaña al Notebook con el título dado.
            5. Selecciona la nueva pestaña como la activa.
        """
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
        """
        Cierra la pestaña actualmente seleccionada en el Notebook,
        liberando sus recursos. Impide cerrar si solo queda una pestaña.

        Proceso:
            1. Si solo hay una pestaña, muestra un aviso y retorna.
            2. Obtiene la pestaña activa.
            3. Oculta sus botones del frame global.
            4. Detiene la barra de progreso (si estaba activa).
            5. Limpia y deshabilita el área de texto.
            6. Destruye el frame de la pestaña (lo elimina del Notebook).
            7. Limpia las referencias internas (historial, barra, area_contenido).
            8. Elimina la pestaña de la lista self.pestañas.
        """
        if len(self.pestañas) <= 1:
            messagebox.showinfo("Aviso", "Debe quedar al menos una pestaña abierta")
            return
        p = self.pestaña_activa()
        if p is None:
            return
        p.ocultar_botones()
        p.ocultar_botones()

        try:
            p.barra.progress.stop()
        except:
            pass

        try:
            p.area_contenido.config(state="normal")
            p.area_contenido.delete("1.0", "end")
            p.area_contenido.config(state="disabled")
        except:
            pass

        p.frame.destroy()

        p.historial = None
        p.barra = None
        p.area_contenido = None

        self.pestañas.remove(p)

    def pestaña_activa(self):
        """
        Retorna la instancia de Pestaña correspondiente a la pestaña
        actualmente seleccionada en el Notebook.

        Proceso:
            Obtiene el ID del frame seleccionado en el Notebook y lo compara
            con el str() del frame de cada Pestaña en la lista.

        Retorna:
            Pestaña | None: La pestaña activa, o None si no se encuentra ninguna
                            (por ejemplo, si el Notebook está vacío o hubo un error).
        """
        try:
            frame_id = self.notebook.select()
            return next((p for p in self.pestañas if str(p.frame) == frame_id), None)
        except Exception:
            return None

    def _on_tab_changed(self, event=None):
        """
        Manejador del evento <<NotebookTabChanged>> que se dispara cuando el usuario
        cambia de pestaña haciendo click en otra etiqueta del Notebook.

        Proceso:
            1. Oculta los botones de TODAS las pestañas.
            2. Muestra los botones de la pestaña recién activada.
            3. Actualiza el menú de historial global para mostrar el historial
               de la pestaña ahora activa.

        Parámetros:
            event: Evento de tkinter (no se usa directamente).
        """
        for p in self.pestañas:
            p.ocultar_botones()
        activa = self.pestaña_activa()
        if activa:
            activa.mostrar_botones()
        if self._menu_historial_ref:
            self._menu_historial_ref()

    def cargar_url_en_activa(self, url: str):
        """
        Carga una URL dada en la pestaña actualmente activa del Notebook.
        Se usa cuando el usuario elige una URL del menú de favoritos o historial.

        Parámetros:
            url (str): URL a cargar (se escribe en el campo de búsqueda de la pestaña).

        Proceso:
            1. Obtiene la pestaña activa.
            2. Escribe la URL en el campo de búsqueda (entrada_var).
            3. Llama a iniciar_busqueda() para disparar la navegación.
        """
        p = self.pestaña_activa()
        if p is None:
            return
        p.barra.entrada_var.set(url)
        p.barra.iniciar_busqueda()

    def actualizar_tema_todas(self, oscuro: bool):
        """
        Aplica el tema indicado a todas las pestañas existentes en el Notebook.
        También almacena el estado del tema para aplicarlo a futuras pestañas nuevas.

        Parámetros:
            oscuro (bool): True para aplicar el tema oscuro, False para el tema claro.

        Proceso:
            1. Guarda el estado en self._tema_oscuro.
            2. Itera sobre todas las pestañas y llama a su método actualizar_tema().
        """
        self._tema_oscuro = oscuro
        for p in self.pestañas:
            p.actualizar_tema(oscuro)