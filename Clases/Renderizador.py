import os
import base64
import tkinter as tk
from html.parser import HTMLParser
from urllib.request import urlopen, Request
from urllib.parse import urljoin


class RenderizadorParser(HTMLParser):
    """
    Parser HTML personalizado que extrae y muestra el contenido textual
    y los enlaces de una página HTML dentro de un widget tk.Text.
    """

    def __init__(self, area_contenido=None, callback_navegacion=None):
        #Callback_navegacion tiene navegar_desde_hipervinculo para cuando demos click a un link poder dirigirnos al lugar
        """
        Inicializa el parser y configura el área de texto destino.
        Soporta de forma opcional un callback para redirigir los clicks a la barra.
        """
        super().__init__()
        self.area_contenido = area_contenido
        self.callback_navegacion = callback_navegacion
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
        self.salida = []
        self.ruta_actual = os.path.abspath(ruta)
        with open(ruta, "r", encoding="utf-8") as archivo:
            contenido = archivo.read()
        self.feed(contenido)
        self._mostrar_en_area()
        return self.salida

    def renderizar_desde_string(self, html_string, ruta_base=""):
        self.salida = []
        self._imagenes_tk = []
        self.url_base = ruta_base
        self.ruta_actual = os.path.abspath(ruta_base) if ruta_base and not ruta_base.startswith("http") else os.getcwd()
        self.feed(html_string)
        self._mostrar_en_area()
        return self.salida

    def _mostrar_en_area(self):
        if self.area_contenido is None:
            return

        self.area_contenido.config(state="normal")
        self.area_contenido.delete("1.0", "end")

        for elemento in self.salida:
            if elemento[0] == "texto":
                self.area_contenido.insert("end", elemento[1] + "\n")

            elif elemento[0]=="error":
                self.area_contenido.tag_config("letra_roja",foreground="red")
                self.area_contenido.insert("end",elemento[1]+"\n","letra_roja")

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

                tag = f"link_{inicio.replace('.', '_')}"  #Crea Tag o nombre unico en la posicion para no perder el link y que sea unico

                self.area_contenido.tag_add(tag, inicio, fin)
                self.area_contenido.tag_config(tag, foreground="blue", underline=True)

                # ── Lo que arregla el problema del raton, el tag funciona como una screenshot del momento cuando guardamos el enlace ──
                def al_entrar(event, t=tag): #Lo que al poner el raton encima vuelva rojo el hipervinculo
                    self.area_contenido.tag_config(t, foreground="red")
                    self.area_contenido.config(cursor="hand2")

                def al_salir(event, t=tag): #Que al quitar el raton deje de ser rojo el hipervinculo
                    self.area_contenido.tag_config(t, foreground="blue")
                    self.area_contenido.config(cursor="")

                def al_hacer_clic(event, r=ruta): #Al presionar el hipervinculo se llame a abrir_link
                    self.abrir_link(r)

                self.area_contenido.tag_bind(tag, "<Enter>", al_entrar)
                self.area_contenido.tag_bind(tag, "<Leave>", al_salir)
                self.area_contenido.tag_bind(tag, "<Button-1>", al_hacer_clic)

        self.area_contenido.config(state="disabled")

    def _insertar_imagen(self, src, alt=""):
        if self.area_contenido is None:
            return

        if src.startswith("//"):
            src = "https:" + src
        elif src.startswith("/") and self.url_base:
            from urllib.parse import urlparse
            parsed = urlparse(self.url_base)
            src = f"{parsed.scheme}://{parsed.netloc}{src}"
        elif not src.startswith("http"):
            src = urljoin(self.url_base, src) if self.url_base else src

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

            if img.width() > 400:
                factor = max(1, img.width() // 400)
                img = img.subsample(factor, factor)

            self._imagenes_tk.append(img)
            self.area_contenido.image_create("end", image=img, padx=4, pady=4)
            self.area_contenido.insert("end", "\n")
        except Exception:
            if alt:
                self.area_contenido.insert("end", f"[{alt}]\n")

    def abrir_link(self, ruta):
        """ Redirige el click del hipervinculo a la barra de búsqueda. """
        if self.callback_navegacion is not None:
            self.callback_navegacion(ruta)
        else:
            carpeta_actual = os.path.dirname(self.ruta_actual)
            ruta_completa = os.path.join(carpeta_actual, ruta)
            self.renderizar(ruta_completa)

    def handle_starttag(self, tag, attrs):

        etiquetas_soportadas={"html","head","body","meta","link","!doctype",
            "script","style","title","h1","h2","h3","h4","h5","h6",
            "p","div","section","article","header","footer","nav",
            "ul","ol","li","br","img","a"
            }
        
        if tag.lower()not in etiquetas_soportadas:
            self.salida.append(("error",f"Este elemento <{tag}> no se puede renderizar"))
            
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
        if self.en_script or self.en_style:
            return

        texto = data.strip()
        if texto == "":
            return

        if self.en_a and self.href != "":
            self.salida.append(("link", texto, self.href))
        elif self.en_title:
            self.titulo_pagina = texto
        elif self.en_h1:
            self.salida.append(("texto", "=== " + texto.upper() + " ==="))
        elif self.en_h2:
            self.salida.append(("texto", "-- " + texto + " --"))
        elif self.en_li:
            self.salida.append(("texto", "  • " + texto))
        else:
            self.salida.append(("texto", texto))