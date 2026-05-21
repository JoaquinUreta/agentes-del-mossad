import os
import base64
import tkinter as tk
from html.parser import HTMLParser
from urllib.request import urlopen, Request
from urllib.parse import urljoin
import threading


class RenderizadorParser(HTMLParser):
    """
    Parser HTML personalizado que extrae y muestra el contenido textual
    y los enlaces de una página HTML dentro de un widget tk.Text.

    Hereda de HTMLParser para procesar el HTML etiqueta por etiqueta.
    Reconoce: títulos <h1>, párrafos <p>, enlaces <a>, y omite el
    contenido de <script> y <style>.

    Notas de referencia:
        - <h1>: títulos de primer nivel (se muestran en mayúsculas).
        - <p>: inicio de párrafo (agrega salto de línea).
        - <a href="...">: enlace clicable con color azul y subrayado.
    """

    def __init__(self, area_contenido=None):
        """
        Inicializa el parser y configura el área de texto destino.

        Parámetros:
            area_contenido (tk.Text | None): Widget de texto de tkinter donde
                se mostrará el HTML procesado. Si es None, el contenido solo
                se almacena en self.salida sin mostrarse visualmente.

        Atributos internos:
            ruta_actual (str): Ruta absoluta del archivo HTML abierto.
                               Se usa para resolver enlaces relativos.
            en_h1 (bool): True mientras el parser está dentro de una etiqueta <h1>.
            en_a (bool): True mientras el parser está dentro de una etiqueta <a>.
            href (str): Valor del atributo href del enlace <a> actual.
            salida (list): Lista de tuplas con el contenido procesado.
                           Formato: ("texto", contenido) o ("link", texto, ruta).
            en_script (bool): True dentro de etiquetas <script> (contenido ignorado).
            en_style (bool): True dentro de etiquetas <style> (contenido ignorado).
        """
        super().__init__()
        self.area_contenido = area_contenido
        self.ruta_actual = ""
        self.en_h1 = False
        self.en_h2 = False
        self.en_h3 = False
        self.en_a = False
        self.en_li = False
        self.en_title = False
        self.titulo_pagina = ""
        self.href = ""
        self.salida = []
        self.en_script = False
        self.en_style = False
        self.url_base = ""
        self._imagenes_tk = []

    def renderizar(self, ruta):
        """
        Lee un archivo HTML desde disco, lo procesa con el parser
        y muestra el resultado en el área de contenido.

        Parámetros:
            ruta (str): Ruta relativa o absoluta al archivo HTML a renderizar.

        Proceso:
            1. Limpia la lista de salida anterior.
            2. Guarda la ruta absoluta del archivo (usada para resolver links relativos).
            3. Lee el archivo con codificación UTF-8.
            4. Alimenta el contenido al parser HTML (feed).
            5. Llama a _mostrar_en_area() para insertar el resultado en el widget.

        Retorna:
            list: La lista self.salida con las tuplas del contenido procesado.
        """
        self.salida = []  # Limpia la lista
        self.ruta_actual = os.path.abspath(ruta)  # Guarda la ruta del archivo

        with open(ruta, "r", encoding="utf-8") as archivo:
            contenido = archivo.read()

        self.feed(contenido)
        self._mostrar_en_area()
        return self.salida

    def renderizar_desde_string(self, html_string, ruta_base=""):
        """
        Procesa un string HTML directamente (sin leer un archivo en disco)
        y muestra el resultado en el área de contenido.

        Útil para páginas descargadas desde internet mediante ClienteHTTP.

        Parámetros:
            html_string (str): Contenido HTML como cadena de texto.
            ruta_base (str): Carpeta raíz para resolver links relativos.
                             Si está vacío, se usa el directorio de trabajo actual.

        Proceso:
            1. Limpia la lista de salida anterior.
            2. Define ruta_actual como la carpeta base para links relativos.
            3. Alimenta el HTML al parser.
            4. Llama a _mostrar_en_area() para insertar el resultado en el widget.

        Retorna:
            list: La lista self.salida con las tuplas del contenido procesado.
        """
        self.salida = []
        self._imagenes_tk = []
        self.url_base = ruta_base
        self.ruta_actual = os.path.abspath(ruta_base) if ruta_base else os.getcwd()
        self.feed(html_string)
        self._mostrar_en_area()
        return self.salida

    def _mostrar_en_area(self):
        """
        Inserta el contenido procesado (almacenado en self.salida) en el
        widget tk.Text de self.area_contenido.

        Proceso:
            1. Habilita el widget (state="normal") para poder escribir.
            2. Borra todo el contenido previo del widget.
            3. Itera sobre cada elemento de self.salida:
               - Tipo "texto": lo inserta seguido de un salto de línea.
               - Tipo "link": inserta el texto del enlace con estilo visual
                 (color azul, subrayado) y asocia un tag único con:
                   * Click (<Button-1>): llama a abrir_link() con la ruta.
                   * Hover (<Enter>): cambia el color a rojo.
                   * Hover (<Leave>): restaura el color a azul.
            4. Deshabilita el widget (state="disabled") para que sea solo lectura.

        Notas:
            - Si area_contenido es None, el método retorna sin hacer nada.
            - Cada enlace recibe un tag único basado en su posición de inicio
              para evitar conflictos entre múltiples links.
        """
        if self.area_contenido is None:
            return

        self.area_contenido.config(state="normal")
        self.area_contenido.delete("1.0", "end")

        for elemento in self.salida:

            if elemento[0] == "texto":
                self.area_contenido.insert("end", elemento[1] + "\n")

            elif elemento[0] == "imagen":
                src = elemento[1]
                alt = elemento[2] if len(elemento) > 2 else ""
                self._insertar_imagen(src, alt)

            elif elemento[0] == "link":
                texto_link = elemento[1]
                ruta = elemento[2]

                inicio = self.area_contenido.index("insert")
                self.area_contenido.insert("insert", texto_link + "\n")
                fin = self.area_contenido.index("insert")

                tag = f"link_{inicio}"

                # Estilo visual del link
                self.area_contenido.tag_add(tag, inicio, fin)
                self.area_contenido.tag_config(tag, foreground="blue", underline=True)

                # Evento click del link
                def callback(event, ruta=ruta):
                    self.abrir_link(ruta)

                self.area_contenido.tag_bind(tag, "<Button-1>", callback)

                # Cambia el color del link al pasar el cursor por encima
                self.area_contenido.tag_bind(tag, "<Enter>",
                    lambda e: self.area_contenido.tag_config(tag, foreground="red"))

                self.area_contenido.tag_bind(tag, "<Leave>",
                    lambda e: self.area_contenido.tag_config(tag, foreground="blue"))

        self.area_contenido.config(state="disabled")

    def _insertar_imagen(self, src, alt=""):
        """
        Descarga una imagen desde una URL o ruta local y la inserta
        en el widget tk.Text. Solo soporta PNG y GIF (sin librerias externas).
        Si la imagen falla (JPG, error de red, etc.) inserta el texto alt.
        """
        if self.area_contenido is None:
            return

        # Resolver URL absoluta
        if src.startswith("//"):
            src = "https:" + src
        elif src.startswith("/") and self.url_base:
            from urllib.parse import urlparse
            parsed = urlparse(self.url_base)
            src = f"{parsed.scheme}://{parsed.netloc}{src}"
        elif not src.startswith("http"):
            src = urljoin(self.url_base, src) if self.url_base else src

        # Solo intentar PNG y GIF (tk.PhotoImage nativo)
        src_lower = src.lower().split("?")[0]
        if not (src_lower.endswith(".png") or src_lower.endswith(".gif")):
            if alt:
                self.area_contenido.insert("end", f"[{alt}]\n")
            return

        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            }
            req = Request(src, headers=headers)
            with urlopen(req, timeout=5) as resp:
                raw = resp.read()

            b64 = base64.b64encode(raw)
            img = tk.PhotoImage(data=b64)

            # Escalar si es muy grande (max 400px de ancho)
            if img.width() > 400:
                factor = max(1, img.width() // 400)
                img = img.subsample(factor, factor)

            self._imagenes_tk.append(img)  # evitar garbage collection
            self.area_contenido.image_create("end", image=img, padx=4, pady=4)
            self.area_contenido.insert("end", "\n")

        except Exception:
            if alt:
                self.area_contenido.insert("end", f"[{alt}]\n")


    def abrir_link(self, ruta):
        """
        Abre un enlace relativo construyendo su ruta completa a partir
        del directorio del archivo HTML actualmente cargado.

        Parámetros:
            ruta (str): Ruta relativa del enlace (valor del atributo href).

        Proceso:
            1. Obtiene el directorio del archivo actual (ruta_actual).
            2. Une ese directorio con la ruta relativa del enlace.
            3. Llama a renderizar() con la ruta completa resultante.

        Nota:
            Este método solo funciona correctamente con enlaces locales/relativos.
            Los enlaces absolutos (http://) no son resueltos aquí.
        """
        carpeta_actual = os.path.dirname(self.ruta_actual)
        ruta_completa = os.path.join(carpeta_actual, ruta)
        self.renderizar(ruta_completa)

    def handle_starttag(self, tag, attrs):
        """
        Manejador llamado automáticamente por HTMLParser al encontrar
        una etiqueta de apertura (e.g. <h1>, <p>, <a href="...">, <script>).

        Parámetros:
            tag (str): Nombre de la etiqueta en minúsculas (ej. "h1", "a").
            attrs (list): Lista de tuplas (nombre_atributo, valor) de la etiqueta.

        Comportamiento por etiqueta:
            - <script>: activa en_script para ignorar su contenido.
            - <style>: activa en_style para ignorar su contenido.
            - <h1>: activa en_h1 y agrega un salto de línea a la salida.
            - <p>: agrega un salto de línea a la salida (inicio de párrafo).
            - <a>: activa en_a y extrae el valor de href de los atributos.
        """
        if tag == "script":
            self.en_script = True
        elif tag == "style":
            self.en_style = True

        if tag == "title":
            self.en_title = True
        elif tag == "h1":
            self.en_h1 = True
            self.salida.append(("texto", ""))
        elif tag in ("h2", "h3", "h4", "h5", "h6"):
            self.en_h2 = True
            self.salida.append(("texto", ""))
        elif tag in ("p", "div", "section", "article", "header", "footer", "nav"):
            self.salida.append(("texto", ""))
        elif tag in ("ul", "ol"):
            self.salida.append(("texto", ""))
        elif tag == "li":
            self.en_li = True
        elif tag == "br":
            self.salida.append(("texto", ""))
        elif tag == "img":
            src = ""
            alt = ""
            for attr in attrs:
                if attr[0] == "src":
                    src = attr[1]
                elif attr[0] == "alt":
                    alt = attr[1]
            if src:
                self.salida.append(("imagen", src, alt))
        elif tag == "a":
            self.en_a = True
            for attr in attrs:
                if attr[0] == "href":
                    self.href = attr[1]

    def handle_endtag(self, tag):
        """
        Manejador llamado automáticamente por HTMLParser al encontrar
        una etiqueta de cierre (e.g. </h1>, </a>, </script>).

        Parámetros:
            tag (str): Nombre de la etiqueta de cierre en minúsculas.

        Comportamiento por etiqueta:
            - </script>: desactiva en_script (se vuelve a procesar el contenido).
            - </style>: desactiva en_style.
            - </h1>: desactiva en_h1 y agrega un salto de línea al final del título.
            - </a>: desactiva en_a y limpia el href almacenado.
        """
        if tag == "script":
            self.en_script = False
        elif tag == "style":
            self.en_style = False

        if tag == "title":
            self.en_title = False
        elif tag == "h1":
            self.en_h1 = False
            self.salida.append(("texto", ""))
        elif tag in ("h2", "h3", "h4", "h5", "h6"):
            self.en_h2 = False
            self.salida.append(("texto", ""))
        elif tag == "li":
            self.en_li = False
        elif tag == "a":
            self.en_a = False
            self.href = ""

    def handle_data(self, data):
        """
        Manejador llamado automáticamente por HTMLParser al encontrar
        texto plano entre etiquetas HTML.

        Parámetros:
            data (str): El texto encontrado entre etiquetas.

        Comportamiento:
            1. Si se está dentro de <script> o <style>, ignora el texto
               (no es contenido visible para el usuario).
            2. Elimina espacios en blanco al inicio y final del texto.
            3. Si el texto resultante está vacío, lo ignora.
            4. Si se está dentro de un <a> con href definido, agrega
               una tupla ("link", texto, href) a la salida.
            5. Si se está dentro de <h1>, agrega el texto en MAYÚSCULAS
               como ("texto", texto_en_mayúsculas).
            6. En cualquier otro caso, agrega el texto normal
               como ("texto", texto).
        """
        # Ignora contenido no visible
        if self.en_script or self.en_style:
            return

        texto = data.strip()

        if texto == "":
            return

        # Detecta links
        if self.en_a and self.href != "":
            self.salida.append(("link", texto, self.href))

        # Captura el titulo de la pagina
        elif self.en_title:
            self.titulo_pagina = texto

        # Detecta titulos h1 (mayusculas con separadores)
        elif self.en_h1:
            self.salida.append(("texto", "=== " + texto.upper() + " ==="))

        # Detecta titulos h2/h3
        elif self.en_h2:
            self.salida.append(("texto", "-- " + texto + " --"))

        # Detecta items de lista
        elif self.en_li:
            self.salida.append(("texto", "  • " + texto))

        # Texto normal
        else:
            self.salida.append(("texto", texto))