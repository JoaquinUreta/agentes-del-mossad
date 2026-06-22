import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from Historial import Historial
from NavegaAvanzada import NavegaAvanzada
from Asistente_de_IA import AsistenteIA


class Pestaña:
    def __init__(
        self,
        notebook,
        style,
        buttons_frame_global,
        menu_savedurl,
        menu_historial_global=None,
        on_modo_cambio=None,
        # referencias de Ventana para conectar BarraBusqueda
        btn_atras=None,
        btn_adelante=None,
        status_var=None,
        gestor_ref=None,
        modo_online=True,
        api_key_ia=None,
    ):
        self.notebook        = notebook
        self.style           = style
        self.historial       = Historial()
        self.navegacion      = NavegaAvanzada()
        self._on_modo_cambio = on_modo_cambio
        self._menu_historial_global = menu_historial_global

        # ── Asistente de IA propio de esta pestaña (independiente) ───
        # Cada pestaña tiene su propia instancia, tal como exige el Hito 3.
        self.asistente_ia = AsistenteIA(api_key_ia) if api_key_ia else None

        # URL visible en la barra de estado (StringVar compartida con BarraBusqueda)
        self.url_actual = tk.StringVar(value="")

        # ── Frame raíz de la pestaña ──────────────────────────────────
        self.frame = tk.Frame(notebook, bg="#EDECEC")
        self.frame.columnconfigure(0, weight=1)
        self.frame.rowconfigure(1, weight=1)

        # ── Área de contenido + panel de chat IA (lado a lado) ─────────
        self.main_area = tk.Frame(self.frame, bg="#FFFFFF")
        self.main_area.grid(row=1, column=0, sticky="nsew")
        self.main_area.columnconfigure(0, weight=1)   # contenido: expandible
        self.main_area.columnconfigure(1, weight=0)   # panel chat: ancho fijo
        self.main_area.rowconfigure(0, weight=1)

        self.area_contenido = tk.Text(self.main_area, state="disabled",
                                      wrap="word", font=("Courier New", 11))
        self.area_contenido.grid(row=0, column=0, sticky="nsew", padx=20, pady=10)

        # ── Panel lateral del chatbot (oculto por defecto) ─────────────
        from PanelChatIA import PanelChatIA
        theme_actual = self._obtener_theme_actual(notebook)
        self.panel_chat_ia = PanelChatIA(self.main_area, theme_actual)
        self._panel_chat_visible = False
        # No se hace .grid() todavía: permanece oculto hasta el primer toggle

        # ── BarraBusqueda (importada aquí para evitar ciclo en módulo) ─
        from BarraBusqueda import BarraBusqueda
        self.barra = BarraBusqueda(
            parent          = self.frame,         # se incrusta en fila 0
            area_contenido  = self.area_contenido,
            navegador       = self.navegacion,
            gestor_pestañas = gestor_ref,         # se inyecta desde GestorPestañas
            guardar_historial = self._guardar_menuhistorial_wrapper,
            notificar_titulo  = self._actualizar_titulo_tab,
            btn_atras       = btn_atras,
            btn_adelante    = btn_adelante,
            status_var      = status_var,
            modo_online     = modo_online,
            asistente_ia    = self.asistente_ia,
            panel_chat_ia   = self.panel_chat_ia,
            toggle_panel_ia = self.toggle_panel_chat_ia,
        )
        # Frame de la barra va en fila 0 (antes del área de contenido)
        self.barra.frame.grid(row=0, column=0, sticky="ew", padx=4, pady=(4, 0))

        # Conectar el botón "✕" del panel para que también lo oculte
        self.panel_chat_ia.on_cerrar = self.toggle_panel_chat_ia

    def toggle_panel_chat_ia(self):
        """Muestra u oculta el panel lateral del chatbot (✕)."""
        if self._panel_chat_visible:
            self.panel_chat_ia.frame.grid_forget()
            self._panel_chat_visible = False
        else:
            self.panel_chat_ia.frame.grid(row=0, column=1, sticky="ns")
            self._panel_chat_visible = True
            self.panel_chat_ia.focus_entrada()

    # ─────────────────────────────────────────────────────────────────
    #  HELPERS
    # ─────────────────────────────────────────────────────────────────
    def _actualizar_titulo_tab(self, titulo: str):
        """Actualiza el texto visible de esta pestaña en el Notebook."""
        try:
            # Recortar título largo
            titulo_corto = titulo if len(titulo) <= 24 else titulo[:21] + "…"
            self.notebook.tab(self.frame, text=titulo_corto)
        except Exception:
            pass

    def _guardar_menuhistorial_wrapper(self):
        """
        Wrapper sin argumentos para BarraBusqueda.
        Lee la URL de la propia barra y registra en el historial.
        """
        url = self.barra.entrada_var.get().strip()
        self._guardar_menuhistorial(url)

    def _guardar_menuhistorial(self, urlactual: str):
        """Registra la URL en el historial local y dispara actualización global."""
        urlactual = urlactual.strip()
        if not urlactual:
            return
        self.historial.agregar_historial(urlactual)
        self.url_actual.set(urlactual)
        if self._menu_historial_global is not None:
            self._menu_historial_global()

    # ─────────────────────────────────────────────────────────────────
    #  ACCIONES DE ARCHIVO (editar / guardar)
    # ─────────────────────────────────────────────────────────────────
    def _editar_archivo(self):
        if messagebox.askyesno("Editar", "¿Deseas editar este documento?"):
            self.area_contenido.config(state="normal")
        else:
            self.area_contenido.config(state="disabled")

    def _guardar_archivo(self, ruta_destino=None):
        ruta = ruta_destino or self.url_actual.get().strip()
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
        if ruta:
            self._guardar_archivo(ruta)

    # ─────────────────────────────────────────────────────────────────
    #  FAVORITOS
    # ─────────────────────────────────────────────────────────────────
    def _cargar_url_global(self, url):
        """Placeholder sobreescrito por VentanaPrincipal."""
        pass

    # ─────────────────────────────────────────────────────────────────
    #  TEMA
    # ─────────────────────────────────────────────────────────────────
    def _obtener_theme_actual(self, widget):
        """
        Busca el diccionario de colores (DARK/LIGHT) publicado por Ventana
        en el widget raíz. Si todavía no existe (p.ej. al construir la
        primera pestaña, antes de que Ventana llame a _apply_theme),
        se usa un fallback oscuro razonable.
        """
        FALLBACK_DARK = {
            "bg": "#0F0E0D", "surface": "#1A1916", "border": "#2E2C29",
            "accent": "#D4A843", "accent2": "#8C6A1F",
            "text": "#E8E4DC", "text_dim": "#6B6760", "topbar": "#141310",
        }
        try:
            root = widget.winfo_toplevel()
            return getattr(root, "theme", None) or FALLBACK_DARK
        except Exception:
            return FALLBACK_DARK

    def actualizar_tema(self, oscuro: bool):
        if oscuro:
            self.frame.config(bg="#2E2E2E")
            self.main_area.config(bg="#3C3C3C")
            self.area_contenido.config(bg="#1E1E1E", fg="#EEEEEE",
                                       insertbackground="#EEEEEE")
            # ── BarraBusqueda ─────────────────────────────────────────
            if hasattr(self, "barra"):
                self.barra.frame.config(bg="#2E2E2E")
                self.barra.entrada.config(bg="#1E1E1E", fg="#EEEEEE",
                                          insertbackground="#EEEEEE",
                                          disabledbackground="#1E1E1E")
                if hasattr(self.barra, "btn_asistente_ia"):
                    self.barra.btn_asistente_ia.config(
                        bg="#2E2E2E", fg="#D4A843",
                        activebackground="#2E2E2E", activeforeground="#FFFFFF",
                    )
        else:
            self.frame.config(bg="#EDECEC")
            self.main_area.config(bg="#FFFFFF")
            self.area_contenido.config(bg="#FFFFFF", fg="#000000",
                                       insertbackground="#000000")
            # ── BarraBusqueda ─────────────────────────────────────────
            if hasattr(self, "barra"):
                self.barra.frame.config(bg="#EDECEC")
                self.barra.entrada.config(bg="#FFFFFF", fg="#000000",
                                          insertbackground="#000000",
                                          disabledbackground="#FFFFFF")
                if hasattr(self.barra, "btn_asistente_ia"):
                    self.barra.btn_asistente_ia.config(
                        bg="#EDECEC", fg="#A0742A",
                        activebackground="#EDECEC", activeforeground="#1A1714",
                    )

        # ── Panel de chat IA ────────────────────────────────────────────
        if hasattr(self, "panel_chat_ia"):
            theme_actual = self._obtener_theme_actual(self.notebook)
            self.panel_chat_ia.actualizar_tema(theme_actual)


# ─────────────────────────────────────────────────────────────────────
#  GESTOR DE PESTAÑAS
# ─────────────────────────────────────────────────────────────────────
class GestorPestañas:
    """Administra la colección de pestañas dentro del ttk.Notebook."""

    def __init__(self, notebook, style, buttons_frame, menu_savedurl, api_key_ia=None):
        self.notebook       = notebook
        self.style          = style
        self.buttons_frame  = buttons_frame
        self.menu_savedurl  = menu_savedurl
        self.pestañas: list[Pestaña] = []
        self._tema_oscuro   = False
        self._menu_historial_ref = None
        self._api_key_ia    = api_key_ia   # clave compartida para AsistenteIA

        # Referencias de Ventana que se inyectan en cada nueva pestaña
        self._btn_atras    = None
        self._btn_adelante = None
        self._status_var   = None
        self._modo_online  = True

        self.notebook.bind("<<NotebookTabChanged>>", self._on_tab_changed)

    # ── Configuración desde Ventana ──────────────────────────────────
    def set_menu_historial_callback(self, cb):
        self._menu_historial_ref = cb

    def set_api_key_ia(self, api_key):
        """Permite definir/actualizar la api_key del Asistente de IA después de crear el gestor."""
        self._api_key_ia = api_key

    def set_controles_ventana(self, btn_atras, btn_adelante, status_var):
        """Ventana llama esto una vez para compartir sus botones de nav."""
        self._btn_atras    = btn_atras
        self._btn_adelante = btn_adelante
        self._status_var   = status_var

    def set_modo_online(self, online: bool):
        """Cambia el modo online/offline en todas las pestañas existentes."""
        self._modo_online = online
        for p in self.pestañas:
            p.barra.Status = online

    # ── Ciclo de vida de pestañas ────────────────────────────────────
    def nueva_pestaña(self, titulo="Nueva pestaña"):
        p = Pestaña(
            notebook          = self.notebook,
            style             = self.style,
            buttons_frame_global = self.buttons_frame,
            menu_savedurl     = self.menu_savedurl,
            menu_historial_global = self._menu_historial_ref,
            on_modo_cambio    = None,
            btn_atras         = self._btn_atras,
            btn_adelante      = self._btn_adelante,
            status_var        = self._status_var,
            gestor_ref        = self,          # ← se inyecta para área activa
            modo_online       = self._modo_online,
            api_key_ia        = self._api_key_ia,
        )
        p.actualizar_tema(self._tema_oscuro)
        self.pestañas.append(p)
        self.notebook.add(p.frame, text=titulo)
        self.notebook.select(p.frame)
        return p

    def cerrar_pestaña_activa(self):
        if len(self.pestañas) <= 1:
            messagebox.showinfo("Aviso", "Debe quedar al menos una pestaña abierta")
            return
        p = self.pestaña_activa()
        if p is None:
            return
        try:
            p.area_contenido.config(state="normal")
            p.area_contenido.delete("1.0", "end")
            p.area_contenido.config(state="disabled")
        except Exception:
            pass
        p.frame.destroy()
        p.historial  = None
        p.area_contenido = None
        self.pestañas.remove(p)

    def pestaña_activa(self) -> Pestaña | None:
        try:
            frame_id = self.notebook.select()
            return next((p for p in self.pestañas if str(p.frame) == frame_id), None)
        except Exception:
            return None

    def _on_tab_changed(self, event=None):
        if self._menu_historial_ref:
            self._menu_historial_ref()

    # ── Cargar URL en la pestaña activa (llamado desde Ventana) ─────
    def cargar_url_en_activa(self, url: str):
        """
        Pone la URL en la barra de la pestaña activa y dispara la navegación.
        Este es el método que Ventana usa para historial, favoritos y barra URL.
        """
        p = self.pestaña_activa()
        if p is None:
            return
        p.barra.entrada_var.set(url)
        p.barra.iniciar_busqueda()

    # ── Tema ─────────────────────────────────────────────────────────
    def actualizar_tema_todas(self, oscuro: bool):
        self._tema_oscuro = oscuro
        for p in self.pestañas:
            p.actualizar_tema(oscuro)