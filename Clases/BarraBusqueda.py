import tkinter as tk
from tkinter import ttk, messagebox, SUNKEN
from Renderizador import RenderizadorParser


class BarraBusqueda:
    def __init__(self, parent, style, area_contenido, botones_habilitar=None, boton_editar=None, botones_requieren_texto=None):

        self.parent = parent
        self.style = style
        self.area_contenido = area_contenido
        self.botones_habilitar = botones_habilitar or []
        self.boton_editar = boton_editar
        self.botones_requieren_texto = botones_requieren_texto or []
        self.ruta_actual = ""

        # ── Variables ────────────────────────────────────────────────
        self.entrada_var    = tk.StringVar()
        self.barra_progreso = tk.StringVar()

        # ── Top frame (Botón Reload + Entry + Botón Ir) ──────────────
        self.top_frame = tk.Frame(parent, bg="#E4E2E2")
        self.top_frame.columnconfigure(0, weight=0)  # botón reload
        self.top_frame.columnconfigure(1, weight=1)  # entry
        self.top_frame.columnconfigure(2, weight=0)  # botón Ir

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

        # ── Entry de búsqueda ────────────────────────────────────────
        self.frame_buscador = ttk.Entry(
            self.top_frame,
            style="entry.TEntry",
            textvariable=self.entrada_var,
            width=60
        )
        self.frame_buscador.grid(row=0, column=1, sticky="ew", padx=(0, 5))

        # ── Botón Ir ─────────────────────────────────────────────────
        self.button_ir = ttk.Button(
            self.top_frame,
            text="Ir",
            style="button.TButton",
            state="disabled",
            command=self.iniciar_busqueda
        )
        self.button_ir.grid(row=0, column=2)

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

        # ── Trace para habilitar/deshabilitar botón Ir ───────────────
        self.entrada_var.trace_add("write", self._verificar_barra)

    def _verificar_barra(self, *args):
        """Habilita el botón Ir y botones_requieren_texto sólo si el Entry tiene texto."""
        texto = self.entrada_var.get().strip()
        estado = "normal" if texto else "disabled"
        self.button_ir.config(state=estado)
        for boton in self.botones_requieren_texto:
            boton.config(state=estado)

    def iniciar_busqueda(self):
        """Arranca la animación de carga y programa la búsqueda."""
        self.barra_progreso.set("Buscando...")
        self.progress.start(10)
        self.parent.after(3000, self._ejecutar_proceso)

    def _ejecutar_proceso(self):
        """Detiene la animación y llama a la validación/renderizado."""
        self.progress.stop()
        self.barra_progreso.set("Procesando datos...")
        self.verificar_existencia()
        self.barra_progreso.set("Listo")

    def verificar_existencia(self):
        """Valida la ruta y renderiza el archivo en area_contenido."""
        import os
        texto = self.entrada_var.get().strip()

        if not os.path.isfile(texto):
            messagebox.showerror("Error", "El archivo no existe")
            return

        if not texto.lower().endswith(".html"):
            continuar = messagebox.askyesno(
                "Advertencia",
                "Tu archivo no es un HTML, ¿desea abrirlo de todas formas?"
            )
            if not continuar:
                return

        try:
            self.ruta_actual = texto

            parser = RenderizadorParser(self.area_contenido)
            parser.renderizar(self.ruta_actual)

            # Habilitar botones externos (guardar, guardar como)
            for boton in self.botones_habilitar:
                boton.config(state="normal")

            # El botón editar solo se habilita si NO es HTML
            if self.boton_editar:
                es_html = texto.lower().endswith(".html")
                self.boton_editar.config(state="disabled" if es_html else "normal")

        except Exception as e:
            messagebox.showerror("Error", f"Ocurrió un error:\n{e}")

    def get_ruta_actual(self):
        return self.ruta_actual

    def actualizar_tema(self, bg_frame, bg_entry, fg_entry, bg_boton, fg_boton, active_bg):
        self.top_frame.config(bg=bg_frame)
        self.style.configure("entry.TEntry",
                              fieldbackground=bg_entry,
                              foreground=fg_entry)
        self.style.configure("button.TButton",
                              background=bg_boton,
                              foreground=fg_boton)
        self.style.map("button.TButton",
                       background=[("active", active_bg)],
                       foreground=[("active", fg_boton)])