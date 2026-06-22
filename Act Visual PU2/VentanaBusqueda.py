import tkinter as tk
from tkinter import messagebox
from MotorBusqueda import MotorBusqueda


class VentanaBusqueda:
    """
    Popup modal del Motor de Búsqueda Simulado (Requerimiento 4).
    Muestra un campo de texto y un botón 'Buscar'. Al encontrar coincidencia
    en MotorBusqueda, renderiza el HTML de resultados en la pestaña activa
    del navegador (los enlaces de resultado abren en una pestaña nueva,
    gracias a target="_blank" en los HTML de consulta).
    """

    def __init__(self, root, theme, on_buscar):
        """
        root      : ventana tk.Tk principal (para usar como parent del modal)
        theme     : diccionario de colores actual (DARK / LIGHT) de Ventana.py
        on_buscar : callback(ruta_html) -> se invoca cuando hay un resultado
                    válido; Ventana.py decide cómo cargarlo (pestaña activa).
        """
        self.motor = MotorBusqueda()
        self.on_buscar = on_buscar
        T = theme

        self.win = tk.Toplevel(root)
        self.win.title("Motor de Búsqueda")
        self.win.transient(root)
        self.win.resizable(False, False)
        self.win.config(bg=T["bg"])

        ancho, alto = 480, 200
        self.win.update_idletasks()
        x = root.winfo_rootx() + (root.winfo_width() // 2) - ancho // 2
        y = root.winfo_rooty() + (root.winfo_height() // 2) - alto // 2
        self.win.geometry(f"{ancho}x{alto}+{x}+{y}")

        contenedor = tk.Frame(self.win, bg=T["bg"], padx=20, pady=20)
        contenedor.pack(fill="both", expand=True)

        titulo = tk.Label(
            contenedor, text="🔍  Buscar en la web",
            font=("Courier New", 16, "bold"), bg=T["bg"], fg=T["text"],
        )
        titulo.pack(anchor="w", pady=(0, 4))

        subtitulo = tk.Label(
            contenedor,
            text="Ej: \"listar universidades chilenas\", \"ultimas noticias de tecnologia\"…",
            font=("Courier New", 9), bg=T["bg"], fg=T["text_dim"],
            wraplength=440, justify="left",
        )
        subtitulo.pack(anchor="w", pady=(0, 12))

        frame_entrada = tk.Frame(contenedor, bg=T["surface"], highlightthickness=1,
                                  highlightbackground=T["border"], highlightcolor=T["accent"])
        frame_entrada.pack(fill="x", pady=(0, 14))

        self.entrada_var = tk.StringVar()
        self.entrada = tk.Entry(
            frame_entrada, textvariable=self.entrada_var, relief="flat",
            font=("Courier New", 12), bd=0, highlightthickness=0,
            bg=T["surface"], fg=T["text"], insertbackground=T["accent"],
        )
        self.entrada.pack(fill="x", ipady=8, ipadx=8)
        self.entrada.bind("<Return>", lambda e: self._buscar())
        self.entrada.focus_set()

        fila_botones = tk.Frame(contenedor, bg=T["bg"])
        fila_botones.pack(fill="x")

        self.btn_buscar = tk.Button(
            fila_botones, text="Buscar", font=("Courier New", 10, "bold"),
            relief="flat", cursor="hand2", bd=0, padx=16, pady=6,
            bg=T["accent"], fg=T["bg"],
            activebackground=T["accent2"], activeforeground=T["text"],
            command=self._buscar,
        )
        self.btn_buscar.pack(side="right")

        self.btn_cancelar = tk.Button(
            fila_botones, text="Cancelar", font=("Courier New", 10),
            relief="flat", cursor="hand2", bd=0, padx=16, pady=6,
            bg=T["bg"], fg=T["text_dim"],
            activebackground=T["bg"], activeforeground=T["accent"],
            command=self.win.destroy,
        )
        self.btn_cancelar.pack(side="right", padx=(0, 8))

        self.win.bind("<Escape>", lambda e: self.win.destroy())
        self.win.grab_set()  # modal

    def _buscar(self):
        texto = self.entrada_var.get().strip()
        if not texto:
            messagebox.showwarning("Aviso", "Escribe algo para buscar", parent=self.win)
            return

        ruta_html = self.motor.buscar(texto)

        if ruta_html is None:
            messagebox.showinfo(
                "Sin resultados",
                f"La búsqueda \"{texto}\" no ha producido resultados.",
                parent=self.win,
            )
            return

        self.win.destroy()
        self.on_buscar(ruta_html)