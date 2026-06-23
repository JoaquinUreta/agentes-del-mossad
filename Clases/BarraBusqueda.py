import os
import tkinter as tk
from tkinter import ttk, messagebox
import threading
import queue
from RenderAvanzado import RenderizadorParserAvanzado
from ClienteHTTP import ClienteHTTP


class BarraBusqueda:
    
    def __init__(
        self,
        parent,
        area_contenido,
        navegador=None,
        gestor_pestañas=None,
        guardar_historial=None,
        notificar_titulo=None,
        btn_atras=None,
        btn_adelante=None,
        status_var=None,
        modo_online=True,
        asistente_ia=None,
        panel_chat_ia=None,
        toggle_panel_ia=None,
    ):
        self.parent            = parent
        self.area_contenido    = area_contenido   # fallback
        self.navegador         = navegador        # NavegaAvanzada de la pestaña
        self.gestor_pestañas   = gestor_pestañas  # GestorPestañas global
        self.guardar_historial = guardar_historial
        self._notificar_titulo_cb = notificar_titulo
        self.btn_atras         = btn_atras
        self.btn_adelante      = btn_adelante
        self.status_var        = status_var
        self.Status            = modo_online      # True = online, False = offline/local
        self.asistente_ia      = asistente_ia     # AsistenteIA propio de esta pestaña
        self.panel_chat_ia     = panel_chat_ia    # PanelChatIA propio de esta pestaña
        self._toggle_panel_ia  = toggle_panel_ia  # callback de Pestaña para mostrar/ocultar

        self.entrada_var       = tk.StringVar()
        self.barra_progreso    = tk.StringVar(value="listo")
        self.ruta_actual       = ""
        self._navegacion_interna = False          # evita doble registro en NavegaAvanzada
        self.botones_habilitar = []               # botones extra a habilitar tras carga
        self.boton_editar      = None
        self._cola_respuestas_ia = queue.Queue()  # comunicación segura hilo IA -> hilo principal

        # ── Widget de entrada (se incrusta en 'parent') ───────────────
        self.frame = tk.Frame(parent)
        self.frame.grid(row=0, column=0, sticky="ew")

        self.entrada = tk.Entry(self.frame, textvariable=self.entrada_var,
                                font=("Arial", 11), relief="flat")
        self.entrada.pack(side="left", fill="x", expand=True, ipady=4, padx=(4, 2))
        self.entrada.bind("<Return>", lambda e: self.iniciar_busqueda())

        # ── Botón Asistente de IA (Requerimientos 5 y 6) ──────────────
        # Cada pestaña tiene el suyo, conectado a su propia instancia
        # de AsistenteIA y a su propio panel de chat lateral, por lo
        # que funciona de forma independiente entre pestañas.
        self.btn_asistente_ia = tk.Button(
            self.frame, text="Asistente IA", font=("Segoe UI Symbol", 12),
            relief="flat", cursor="hand2", bd=0, padx=8,
            command=self.toggle_asistente_ia,
        )
        self.btn_asistente_ia.pack(side="left", padx=(2, 4))

        # Conectar el panel de chat con esta BarraBusqueda (envío de preguntas)
        if self.panel_chat_ia is not None:
            self.panel_chat_ia.on_enviar_pregunta = self._procesar_pregunta_ia

        # Barra de progreso indeterminada (oculta por defecto)
        self.progress = ttk.Progressbar(self.frame, mode="indeterminate", length=60)
        # No se empaqueta hasta que se necesite

    # ─────────────────────────────────────────────────────────────────
    #  PUNTO DE ENTRADA PÚBLICO
    # ─────────────────────────────────────────────────────────────────
    def iniciar_busqueda(self):
        """Llama a _ejecutar_proceso. Convenio esperado por Ventana."""
        self._ejecutar_proceso()

    def navegar(self, url: str):
        """Carga una URL directamente (usado por Ventana para favoritos / historial)."""
        self.entrada_var.set(url)
        self._ejecutar_proceso()

    # ─────────────────────────────────────────────────────────────────
    #  FLUJO PRINCIPAL
    # ─────────────────────────────────────────────────────────────────
    def _ejecutar_proceso(self):
        """Decide si navegar en modo online (HTTP) o local, y lanza el proceso."""
        texto = self.entrada_var.get().strip()
        if not texto:
            messagebox.showerror("Error", "El campo está vacío")
            return

        self._set_status(f"Cargando {texto}…")

        if self.Status:
            # ── Modo online: petición HTTP en hilo secundario ─────────
            hilo = threading.Thread(
                target=self._hilo_peticion_http, args=(texto,), daemon=True
            )
            hilo.start()
        else:
            # ── Modo local: síncrono (instantáneo) ───────────────────
            resultado = self.verificar_existencia_local()
            self._set_status("Listo" if resultado else "Error")
            self._actualizar_botones_navegacion()

    # ─────────────────────────────────────────────────────────────────
    #  MODO ONLINE
    # ─────────────────────────────────────────────────────────────────
    def _hilo_peticion_http(self, texto):
        """Petición HTTP en segundo plano; devuelve resultado al hilo principal."""
        # ── Validación previa (Requerimiento 1, Hito 3) ──────────────
        # Antes de gastar tiempo/timeout conectando, se valida protocolo,
        # host y puerto con la misma regla que usa el renderizador.
        try:
            RenderizadorParserAvanzado.soportes_url(texto)
        except ValueError as e:
            self.parent.winfo_toplevel().after(
                0, self._finalizar_validacion_fallida, texto, str(e)
            )
            return

        try:
            cliente = ClienteHTTP()
            html_string, status = cliente.buscarurl(texto)
            self.parent.winfo_toplevel().after(
                0, self._finalizar_peticion_http, texto, html_string, status
            )
        except Exception as e:
            self.parent.winfo_toplevel().after(
                0, self._finalizar_peticion_http_error, e
            )

    def _finalizar_validacion_fallida(self, texto, mensaje_error):
        """Hilo principal: la URL no pasó soportes_url (puerto/host inválido)."""
        area_destino = self._area_activa()
        parser = RenderizadorParserAvanzado(
            area_destino, callback_navegacion=self.navegar_desde_hipervinculo
        )
        parser.salida = [("error", mensaje_error)]
        parser._mostrar_en_area()
        self._set_status(f"Error — {mensaje_error}")
        messagebox.showerror("Error de conexión", mensaje_error)
        self._actualizar_botones_navegacion()

    def _finalizar_peticion_http(self, texto, html_string, status):
        """Hilo principal: renderiza el HTML recibido y actualiza controles."""
        area_destino = self._area_activa()
        parser = RenderizadorParserAvanzado(
            area_destino, callback_navegacion=self.navegar_desde_hipervinculo
        )

        if status == 200:
            self._set_status(f"200 OK — {texto}")
            parser.renderizar_desde_string(html_string, ruta_base=texto, validar_conexion=True)
            self._post_navegacion_ok(texto)
        elif status == 404:
            self._set_status(f"404 Not Found — {texto}")
            messagebox.showerror("Error", f"Página no encontrada: {texto}")
        elif status is None:
            self._set_status("Error — No se pudo conectar")
            messagebox.showerror("Error", "No se pudo establecer conexión")
        else:
            self._set_status(f"{status} — {texto}")
            messagebox.showwarning("Aviso", f"El servidor respondió con código {status}")

        self._actualizar_botones_navegacion()

    def _finalizar_peticion_http_error(self, e):
        """Hilo principal: muestra error de conexión inesperado."""
        self._set_status("Error inesperado")
        messagebox.showerror("Error", f"Ocurrió un error al conectar:\n{e}")
        self._actualizar_botones_navegacion()

    # ─────────────────────────────────────────────────────────────────
    #  MODO LOCAL
    # ─────────────────────────────────────────────────────────────────
    def verificar_existencia_local(self):
        """Carga y renderiza un archivo HTML local."""
        texto = self.entrada_var.get().strip()
        area_destino = self._area_activa()
        parser = RenderizadorParserAvanzado(
            area_destino, callback_navegacion=self.navegar_desde_hipervinculo
        )

        if not os.path.isfile(texto):
            messagebox.showerror("Error", "El archivo no existe")
            return False

        if not texto.lower().endswith(".html"):
            if not messagebox.askyesno(
                "Advertencia", "Tu archivo no es HTML, ¿deseas abrirlo de todas formas?"
            ):
                return False

        try:
            self.ruta_actual = texto
            parser.renderizar(self.ruta_actual)
            self._post_navegacion_ok(texto, titulo=os.path.basename(texto))
            if self.boton_editar:
                self.boton_editar.config(state="normal")
            return True
        except Exception as e:
            messagebox.showerror("Error", f"Ocurrió un error:\n{e}")
            return False

    # ─────────────────────────────────────────────────────────────────
    #  NAVEGACIÓN POR HIPERVÍNCULO (callback del Renderizador)
    # ─────────────────────────────────────────────────────────────────
    def navegar_desde_hipervinculo(self, url: str, target: str = ""):
        """
        Llamado cuando el usuario hace clic en un enlace renderizado.
        Resuelve la URL relativa, la pone en la barra y navega.
        Si target == '_blank', se abre una pestaña nueva y se navega ahí
        en lugar de hacerlo en la pestaña actual (igual que un navegador real).
        """
        # Resolver URLs relativas (locales)
        if not url.startswith(("http://", "https://", "file://")) and not os.path.isabs(url):
            if self.ruta_actual:
                base = os.path.dirname(self.ruta_actual)
                url = os.path.join(base, url)

        if target == "_blank" and self.gestor_pestañas is not None:
            # Abrir en una pestaña nueva, sin tocar la pestaña actual
            nueva = self.gestor_pestañas.nueva_pestaña("Nueva pestaña")
            nueva.barra.navegar(url)
            return

        self._navegacion_interna = True
        self.entrada_var.set(url)
        self._ejecutar_proceso()
        self._navegacion_interna = False

    # ─────────────────────────────────────────────────────────────────
    #  ASISTENTE DE IA — PANEL DE CHAT LATERAL (Requerimientos 5 y 6)
    # ─────────────────────────────────────────────────────────────────
    def toggle_asistente_ia(self):
        """
        Muestra u oculta el panel lateral de chat de ESTA pestaña.
        Cada pestaña tiene su propio panel y su propia instancia de
        AsistenteIA, por lo que la conversación es independiente entre
        pestañas (Requerimiento 5/6).
        """
        if self._toggle_panel_ia is not None:
            self._toggle_panel_ia()

        if self.asistente_ia is None and self.panel_chat_ia is not None:
            if not getattr(self, "_aviso_sin_apikey_mostrado", False):
                self.panel_chat_ia.mostrar_error_ia(
                    "Esta pestaña no tiene una api_key configurada "
                    "para el Asistente de IA."
                )
                self.panel_chat_ia.set_entrada_habilitada(False)
                self._aviso_sin_apikey_mostrado = True

    def _procesar_pregunta_ia(self, pregunta: str):
        """
        Llamado por PanelChatIA cuando el usuario envía un mensaje.
        Lanza la consulta a Gemini en un hilo secundario (no bloquea la UI).
        El hilo NUNCA toca widgets de Tkinter directamente: solo deposita
        el resultado en una queue.Queue thread-safe. El hilo principal
        revisa esa cola periódicamente con root.after() (patrón seguro
        recomendado para combinar threading con Tkinter).
        """
        if self.panel_chat_ia is not None:
            self.panel_chat_ia.agregar_mensaje_usuario(pregunta)

        if self.asistente_ia is None:
            if self.panel_chat_ia is not None:
                self.panel_chat_ia.mostrar_error_ia(
                    "No es posible responder: falta configurar la api_key "
                    "del Asistente de IA."
                )
            return

        if self.panel_chat_ia is not None:
            self.panel_chat_ia.mostrar_indicador_escribiendo()
        self._set_status(f"Consultando IA: {pregunta}…")

        hilo = threading.Thread(
            target=self._hilo_pregunta_ia, args=(pregunta,), daemon=True
        )
        hilo.start()

        # El polling se programa desde el hilo PRINCIPAL (aquí mismo),
        # nunca desde dentro del hilo secundario.
        self.parent.winfo_toplevel().after(100, self._revisar_cola_respuestas_ia)

    def _hilo_pregunta_ia(self, pregunta: str):
        """
        Hilo secundario: SOLO hace red/IO (bloqueante), nunca toca Tkinter.
        Deposita el resultado en la cola para que el hilo principal lo recoja.
        """
        try:
            respuesta = self.asistente_ia.generar_respuesta(pregunta)
        except Exception as e:
            respuesta = f"Error: No es posible conectarse a Gemini. ({e})"

        self._cola_respuestas_ia.put((pregunta, respuesta))

    def _revisar_cola_respuestas_ia(self):
        """
        Ejecutado en el hilo PRINCIPAL (vía after). Revisa si ya llegó
        la respuesta de la IA; si no, se reprograma a sí mismo.
        """
        try:
            pregunta, respuesta = self._cola_respuestas_ia.get_nowait()
        except queue.Empty:
            # Aún no hay respuesta: reintentar en 100ms
            self.parent.winfo_toplevel().after(100, self._revisar_cola_respuestas_ia)
            return

        self._finalizar_pregunta_ia(pregunta, respuesta)

    def _finalizar_pregunta_ia(self, pregunta: str, respuesta: str):
        """
        Hilo principal: agrega la respuesta de la IA como burbuja nueva
        en el panel de chat de ESTA pestaña (independiente de cuál esté
        activa en el notebook en ese momento).
        """
        if self.panel_chat_ia is not None:
            if respuesta.startswith("Error:"):
                self.panel_chat_ia.mostrar_error_ia(respuesta)
            else:
                self.panel_chat_ia.agregar_mensaje_ia(respuesta)

        if respuesta.startswith("Error:"):
            self._set_status("Error en la consulta a la IA")
        else:
            self._set_status(f"Respuesta de la IA — {pregunta}")

    # ─────────────────────────────────────────────────────────────────
    #  HELPERS INTERNOS
    # ─────────────────────────────────────────────────────────────────
    def _area_activa(self):
        """
        Devuelve el tk.Text de la pestaña activa.
        Si no hay gestor disponible, usa el area_contenido de respaldo.
        """
        if self.gestor_pestañas is not None:
            p = self.gestor_pestañas.pestaña_activa()
            if p and p.area_contenido:
                return p.area_contenido
        return self.area_contenido

    def _post_navegacion_ok(self, url: str, titulo: str = ""):
        """Acciones comunes tras una navegación exitosa."""
        # Registrar en NavegaAvanzada de la pestaña
        if self.navegador and not self._navegacion_interna:
            self.navegador.navegar(url)

        # Actualizar título de la pestaña
        self._notificar_titulo(titulo or url)

        # Disparar callback de historial global (panel lateral de Ventana)
        if self.guardar_historial:
            self.guardar_historial()

        # Habilitar botones extra (recargar, etc.)
        for btn in self.botones_habilitar:
            btn.config(state="normal")

    def _notificar_titulo(self, titulo: str):
        if self._notificar_titulo_cb:
            self._notificar_titulo_cb(titulo)

    def _set_status(self, texto: str):
        if self.status_var is not None:
            self.status_var.set(texto)

    def _actualizar_botones_navegacion(self):
        """Habilita/deshabilita ◀ ▶ según NavegaAvanzada de la pestaña."""
        nav = self.navegador
        if nav is None:
            return
        if self.btn_atras:
            self.btn_atras.config(state="normal" if nav.puede_atras() else "disabled")
        if self.btn_adelante:
            self.btn_adelante.config(state="normal" if nav.puede_adelante() else "disabled")