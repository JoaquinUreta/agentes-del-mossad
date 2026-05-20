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


class VentanaPrincipal:
    """
    Clase principal del navegador. Crea y gestiona la ventana raíz de tkinter,
    orquesta todos los componentes de la interfaz y define el ciclo de vida
    completo de la aplicación.

    Orden de inicialización (en __init__):
        1. _configurar_ventana      → tamaño, título, posición.
        2. _configurar_estilos      → tema ttk.
        3. _construir_layout        → top_bar, buttons_frame, notebook.
        4. _construir_menu_savedurl → menú desplegable de URLs favoritas.
        5. _construir_gestor        → GestorPestañas + monkey-patch de _cargar_url_global.
        6. _construir_historial     → botón + menú de historial global.
        7. _construir_botones_pestañas → botones Nueva/Cerrar pestaña.
        8. _construir_ajustes       → menú Ajustes con modos claro/oscuro.
        9. _cargar_urls_default     → agrega URLs predefinidas al menú de favoritos.
       10. _abrir_primera_pestaña   → crea la pestaña inicial.
       11. _configurar_cierre       → protocolo WM_DELETE_WINDOW.
       12. mainloop()               → inicia el bucle de eventos de tkinter.
    """

    def __init__(self):
        """
        Punto de entrada de la aplicación. Crea la ventana raíz y llama
        a todos los métodos de construcción en orden, terminando con mainloop().
        """
        self.main = tk.Tk()
        self._configurar_ventana()
        self._configurar_estilos()
        self._construir_layout()
        self._construir_menu_savedurl()
        self._construir_gestor()
        self._construir_historial()
        self._construir_botones_pestañas()
        self._construir_ajustes()
        self._cargar_urls_default()
        self._abrir_primera_pestaña()
        self._configurar_cierre()
        self.main.mainloop()

    def _configurar_ventana(self):
        """
        Configura el título, color de fondo, tamaño mínimo y geometría inicial
        de la ventana principal según el sistema operativo.

        Comportamiento multiplataforma:
            - Windows: maximiza la ventana con state("zoomed").
            - Otros (Linux/macOS): calcula un tamaño que ocupa casi toda la pantalla
              (ancho y alto del monitor menos 10 px de margen por lado) y lo aplica
              con geometry().

        Atributos configurados:
            title: "GO FILE EXPLORER"
            bg: "#E4E2E2"
            minsize: 600 x 400 px
            resizable: True en ambas dimensiones.
        """
        self.main.title("GO FILE EXPLORER")
        self.main.config(bg="#E4E2E2")
        self.main.minsize(600, 400)
        self.main.resizable(True, True)

        sistema = platform.system()
        margen  = 10
        self.main.update_idletasks()

        ancho_monitor = self.main.winfo_screenwidth()
        alto_monitor  = self.main.winfo_screenheight()
        ancho = ancho_monitor - 2 * margen
        alto  = alto_monitor  - 2 * margen

        if sistema == "Windows":
            self.main.state("zoomed")
        else:
            self.main.geometry(f"{ancho}x{alto}+{margen}+{margen}")

    def _configurar_estilos(self):
        """
        Crea el objeto ttk.Style y activa el tema "clam" de tkinter,
        que permite una mayor personalización visual de los widgets ttk.

        El objeto self.style es compartido con GestorPestañas, las Pestañas
        y las instancias de BarraBusqueda para mantener coherencia visual.
        """
        self.style = ttk.Style(self.main)
        self.style.theme_use("clam")

    def _construir_layout(self):
        """
        Define la estructura de grid de la ventana principal y crea los
        contenedores principales: top_bar, buttons_frame y notebook.

        Estructura de grid (ventana principal):
            Fila 0 (weight=0): top_bar con los botones globales.
            Fila 1 (weight=1): notebook con las pestañas (se expande con la ventana).

        Widgets creados:
            top_bar (tk.Frame): Barra superior que contiene buttons_frame.
            buttons_frame (tk.Frame): Frame dentro de top_bar donde se colocan
                                      todos los botones globales (favoritos, historial,
                                      nueva pestaña, cerrar, ajustes) y los botones
                                      propios de cada pestaña activa.
            notebook (ttk.Notebook): Contenedor de pestañas; ocupa toda la zona central.
        """
        self.main.columnconfigure(0, weight=1)
        self.main.rowconfigure(0, weight=0)   # top bar
        self.main.rowconfigure(1, weight=1)   # notebook

        self.top_bar = tk.Frame(self.main, bg="#E4E2E2")
        self.top_bar.grid(row=0, column=0, sticky="ew", padx=10, pady=5)
        self.top_bar.columnconfigure(0, weight=1)

        self.buttons_frame = tk.Frame(self.top_bar, bg="#E4E2E2")
        self.buttons_frame.grid(row=0, column=0, sticky="e", pady=(3, 0))

        self.notebook = ttk.Notebook(self.main)
        self.notebook.grid(row=1, column=0, sticky="nsew", padx=10, pady=5)

    def _construir_menu_savedurl(self):
        """
        Crea el botón desplegable "URL Guardadas" y su menú asociado.
        El menú se llena con las URLs default en _cargar_urls_default()
        y con las URLs que el usuario agrega como favoritas desde cada pestaña.

        Widgets creados:
            savedurl_btn (ttk.Menubutton): Botón desplegable "URL Guardadas".
            menu_savedurl (tk.Menu): Menú de entradas de URLs; cada entrada
                                     llama a gestor.cargar_url_en_activa(url).
        """
        self.savedurl_btn  = ttk.Menubutton(self.buttons_frame, text="URL Guardadas", style="Custom.TMenubutton")
        self.menu_savedurl = tk.Menu(self.savedurl_btn, tearoff=0)
        self.savedurl_btn["menu"] = self.menu_savedurl
        self.savedurl_btn.pack(side="left", padx=3)

    def _construir_gestor(self):
        """
        Instancia el GestorPestañas y conecta el monkey-patch de _cargar_url_global
        en la clase Pestaña para que las URLs favoritas se carguen en la pestaña activa.

        Proceso:
            1. Crea GestorPestañas con el notebook, style, buttons_frame y menu_savedurl.
            2. Aplica monkey-patching al método _cargar_url_global de la clase Pestaña:
               lo reemplaza con un lambda que delega en gestor.cargar_url_en_activa(url),
               permitiendo que cualquier instancia de Pestaña cargue la URL en la activa.

        Nota sobre monkey-patching:
            Se reemplaza el método a nivel de clase (Pestaña._cargar_url_global),
            no a nivel de instancia, para que todas las pestañas futuras hereden el comportamiento.
        """
        self.gestor = GestorPestañas(
            self.notebook, self.style, self.buttons_frame, self.menu_savedurl
        )
        # Conectar favoritos de cada Pestaña al gestor
        Pestaña._cargar_url_global = lambda p, url: self.gestor.cargar_url_en_activa(url)

    def _construir_historial(self):
        """
        Crea el botón desplegable "Historial" y su menú asociado,
        y registra el callback de actualización en el GestorPestañas.

        Proceso:
            1. Crea boton_historial (ttk.Menubutton) y menu_historial (tk.Menu).
            2. Llama a gestor.set_menu_historial_callback(_actualizar_menu_historial)
               para que el gestor invoque esta función cuando deba refrescar el historial.

        El menú se llena dinámicamente por _actualizar_menu_historial() con las URLs
        del historial de la pestaña activa en ese momento.
        """
        self.boton_historial = ttk.Menubutton(self.buttons_frame, text="Historial", style="Custom.TMenubutton")
        self.menu_historial  = tk.Menu(self.boton_historial, tearoff=0)
        self.boton_historial["menu"] = self.menu_historial
        self.boton_historial.pack(side="left", padx=4)

        self.gestor.set_menu_historial_callback(self._actualizar_menu_historial)

    def _actualizar_menu_historial(self):
        """
        Reconstruye el menú de historial con las URLs del historial de la pestaña activa.

        Proceso:
            1. Borra todas las entradas actuales del menu_historial.
            2. Obtiene la pestaña activa desde el gestor.
            3. Itera sobre los índices del historial de la pestaña (0 = más reciente)
               hasta obtener None (sin más entradas).
            4. Por cada URL encontrada, agrega un comando al menú que llama
               a gestor.cargar_url_en_activa(url) al hacer click.

        Nota:
            El menú refleja el historial individual de cada pestaña, no uno global.
            Al cambiar de pestaña, el menú se actualiza vía _on_tab_changed del gestor.
        """
        self.menu_historial.delete(0, "end")
        pestaña = self.gestor.pestaña_activa()
        indice = 0
        while True:
            url = pestaña.historial.obtener_url(indice)
            if url is None:
                break
            self.menu_historial.add_command(
                label=url,
                command=lambda u=url: self.gestor.cargar_url_en_activa(u)
            )
            indice += 1

    def _construir_botones_pestañas(self):
        """
        Crea y coloca los botones "＋ Nueva pestaña" y "✕ Cerrar pestaña"
        en el buttons_frame global.

        Botones creados:
            btn_nueva_tab: Llama a gestor.nueva_pestaña() al hacer click.
            btn_cerrar_tab: Llama a gestor.cerrar_pestaña_activa() al hacer click.
        """
        self.btn_nueva_tab  = ttk.Button(self.buttons_frame, text="＋ Nueva pestaña", command=self.gestor.nueva_pestaña)
        self.btn_cerrar_tab = ttk.Button(self.buttons_frame, text="✕ Cerrar pestaña", command=self.gestor.cerrar_pestaña_activa)
        self.btn_nueva_tab.pack(side="left", padx=3)
        self.btn_cerrar_tab.pack(side="left", padx=3)

    def _construir_ajustes(self):
        """
        Crea el menú desplegable "Ajustes" con opciones de tema claro y oscuro.

        Widgets creados:
            menu_btn (ttk.Menubutton): Botón "Ajustes" con menú desplegable.
            menu_contextual (tk.Menu): Menú con dos opciones:
                - "Modo Oscuro": llama a _modo_oscuro().
                - "Modo Claro": llama a _modo_claro().
        """
        self.menu_btn        = ttk.Menubutton(self.buttons_frame, text="Ajustes", style="Custom.TMenubutton")
        self.menu_contextual = tk.Menu(self.menu_btn, tearoff=0)
        self.menu_btn["menu"] = self.menu_contextual
        self.menu_btn.pack(side="left", padx=3)

        self.menu_contextual.add_command(label="Modo Oscuro", command=self._modo_oscuro)
        self.menu_contextual.add_command(label="Modo Claro",  command=self._modo_claro)

    def _modo_oscuro(self):
        """
        Aplica el tema oscuro a la ventana principal y a todas las pestañas.

        Proceso:
            1. Cambia el color de fondo de main, top_bar y buttons_frame a #2E2E2E.
            2. Llama a gestor.actualizar_tema_todas(oscuro=True) para que cada
               Pestaña actualice sus propios colores.
            3. Intenta aplicar colores oscuros al menu_contextual y menu_btn
               (pueden no soportarlo en todos los sistemas operativos).
        """
        self.main.config(bg="#2E2E2E")
        self.top_bar.config(bg="#2E2E2E")
        self.buttons_frame.config(bg="#2E2E2E")
        self.gestor.actualizar_tema_todas(oscuro=True)
        for w in (self.menu_contextual, self.menu_btn):
            try:
                w.config(bg="#3C3C3C", fg="#FFFFFF")
            except Exception:
                pass

    def _modo_claro(self):
        """
        Aplica el tema claro a la ventana principal y a todas las pestañas.

        Proceso:
            1. Restaura el color de fondo de main, top_bar y buttons_frame a #E4E2E2.
            2. Llama a gestor.actualizar_tema_todas(oscuro=False) para que cada
               Pestaña restaure sus propios colores.
            3. Intenta restaurar colores claros al menu_contextual y menu_btn.
        """
        self.main.config(bg="#E4E2E2")
        self.top_bar.config(bg="#E4E2E2")
        self.buttons_frame.config(bg="#E4E2E2")
        self.gestor.actualizar_tema_todas(oscuro=False)
        for w in (self.menu_contextual, self.menu_btn):
            try:
                w.config(bg="#E4E2E2", fg="#000000")
            except Exception:
                pass

    def _cargar_urls_default(self):
        """
        Agrega un conjunto de URLs predefinidas al menú de URLs favoritas
        al iniciar la aplicación.

        URLs incluidas por defecto:
            - https://example.com, https://example.org, https://example.net
            - https://httpbin.org/get
            - https://www.iana.org/domains/reserved
            - https://info.cern.ch (la primera página web de la historia)
            - https://text.npr.org (versión de texto de NPR)
            - https://www.utalca.cl

        Proceso para cada URL:
            1. Verifica cuántas entradas hay actualmente en el menú.
            2. Revisa si la URL ya existe para evitar duplicados.
            3. Si no existe y hay menos de 10 entradas, la agrega como comando.
               Al hacer click se carga en la pestaña activa mediante el gestor.
        """
        urls_default = [
            "https://example.com",
            "https://example.org",
            "https://example.net",
            "https://httpbin.org/get",
            "https://www.iana.org/domains/reserved",
            "https://info.cern.ch",
            "https://text.npr.org",
            "https://www.utalca.cl",
        ]
        for url in urls_default:
            try:
                cantidad = self.menu_savedurl.index("end") + 1
            except Exception:
                cantidad = 0
            ya_existe = False
            for i in range(cantidad):
                if self.menu_savedurl.entrycget(i, "label") == url:
                    ya_existe = True
                    break
            if not ya_existe and cantidad < 10:
                self.menu_savedurl.add_command(
                    label=url,
                    command=lambda u=url: self.gestor.cargar_url_en_activa(u)
                )

    def _abrir_primera_pestaña(self):
        """
        Crea la primera pestaña al iniciar la aplicación llamando a
        gestor.nueva_pestaña() con el título "Nueva pestaña".
        Esta pestaña es la que el usuario ve al abrir el navegador.
        """
        self.gestor.nueva_pestaña("Nueva pestaña")

    def _configurar_cierre(self):
        """
        Registra el protocolo WM_DELETE_WINDOW de tkinter para interceptar
        el cierre de la ventana (click en la X del sistema operativo)
        y redirigirlo al método _cerrar() que pide confirmación al usuario.
        """
        self.main.protocol("WM_DELETE_WINDOW", self._cerrar)

    def _cerrar(self):
        """
        Maneja el cierre de la aplicación mostrando un diálogo de confirmación.

        Proceso:
            1. Muestra un messagebox.askokcancel con el mensaje "¿Seguro que quieres
               cerrar el navegador?".
            2. Si el usuario confirma (OK): destruye la ventana principal con main.destroy(),
               lo que detiene el mainloop y termina la aplicación.
            3. Si cancela: no hace nada y la ventana permanece abierta.
        """
        if messagebox.askokcancel("Salir", "¿Seguro que quieres cerrar el navegador?"):
            self.main.destroy()


if __name__ == "__main__":
    VentanaPrincipal()