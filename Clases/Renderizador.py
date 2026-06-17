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
        self.en_h4 = False
        self.en_h5 = False
        self.en_h6 = False
        self.en_doctype = False
        self.en_html = False
        self.en_head = False
        self.en_Strong = False
        self.en_em = False
        self.en_a = False
        self.en_li = False
        self.en_title = False
        self.en_body = False
        self.en_br = False
        self.en_hr = False
        self.titulo_pagina = ""
        self.href = ""
        self.salida = []
        self.en_script = False
        self.en_style = False
        self.url_base = ""
        self._imagenes_tk = []
        self.en_li = False
        """banderas de etiquetas avanzadas"""
        self.en_div = False
        self.en_span = False
        self.en_table = False
        self.en_tr = False
        self.en_th = False
        self.en_td = False
        self.en_form = False
        self.en_input = False
        self.en_label = False
        self.en_button = False
        self.en_select = False
        self.en_textarea = False
        self.en_header = False
        self.en_footer = False
        self.en_nav = False
        self.en_section = False
        self.en_article = False
        self.en_aside = False
        self.en_figure = False
        self.en_figcaption = False
        """banderas de etiquetas multimedia"""
        self.en_video = False
        self.en_audio = False
        self.en_source = False
        self.en_track = False
        self.en_canvas = False
        self.en_svg = False
        self.en_picture = False
        self.en_iframe = False
        self.indent_level = 0

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
        etiquetas_soportadas = {
            "html","head","body","meta","link","!doctype", "script","style","title",
            "h1","h2","h3","h4","h5","h6", "p","div","section","article","header",
            "footer","nav","ul","ol","li","br","img","a","span","table","tr","th",
            "td","form","input","label","button","select","textarea","aside",
            "figure","figcaption","video","audio","source","track","canvas","svg",
            "picture","iframe"
        }
        
        tag_lower = tag.lower()
        attr_dict = dict(attrs)
        self.attrs_actuales = attr_dict
        
        if tag_lower not in etiquetas_soportadas:
            self.salida.append(("error", f"Este elemento <{tag}> no se puede renderizar"))
            return

        # Control de Scripts y Estilos (para ignorar su contenido de texto plano)
        if tag_lower == "script": self.en_script = True
        elif tag_lower == "style": self.en_style = True
        elif tag_lower == "title": self.en_title = True
        
        # Encabezados
        elif tag_lower in ("h1", "h2", "h3", "h4", "h5", "h6"):
            # Dinámicamente seteamos la bandera (ej: self.en_h1 = True) usando setattr
            setattr(self, f"en_{tag_lower}", True)
            self.salida.append(("texto", ""))
            
        # Bloques con Identación
        elif tag_lower in ("div", "section", "article", "header", "footer", "nav", "aside"):
            setattr(self, f"en_{tag_lower}", True)
            self.salida.append(("texto", ""))
            self.indent_level += 1
            
        elif tag_lower == "p":
            self.salida.append(("texto", ""))
        elif tag_lower in ("ul", "ol"):
            self.salida.append(("texto", ""))
        elif tag_lower == "li":
            self.en_li = True
        elif tag_lower == "br":
            self.salida.append(("texto", ""))
            
        # Imágenes (Manejo de Atributos directo)
        elif tag_lower == "img":
            src = attr_dict.get("src", "")
            alt = attr_dict.get("alt", "")
            if src:
                self.salida.append(("imagen", src, alt))
                
        # Enlaces
        elif tag_lower == "a":
            self.en_a = True
            self.href = attr_dict.get("href", "")
            
        # Elementos de Formulario y otros Inline
        elif tag_lower in ("span", "table", "tr", "th", "td", "form", "input", "label", "button", "select", "textarea", "figure", "figcaption", "video", "audio", "source", "track", "canvas", "svg", "picture", "iframe"):
            setattr(self, f"en_{tag_lower}", True)

    def handle_endtag(self, tag):
        tag_lower = tag.lower()
        
        if tag_lower == "script": self.en_script = False
        elif tag_lower == "style": self.en_style = False
        elif tag_lower == "title": self.en_title = False
        elif tag_lower in ("h1", "h2", "h3", "h4", "h5", "h6"):
            setattr(self, f"en_{tag_lower}", False)
            if tag_lower == "h1" or tag_lower == "h6":
                self.salida.append(("texto", ""))
        elif tag_lower == "li":
            self.en_li = False
        elif tag_lower == "a":
            self.en_a = False
            self.href = ""
        # Reducción de indentación al cerrar bloques
        elif tag_lower in ("div", "section", "article", "header", "footer", "nav", "aside"):
            setattr(self, f"en_{tag_lower}", False)
            self.indent_level = max(0, self.indent_level - 1)
        elif tag_lower in ("span", "table", "tr", "th", "td", "form", "input", "label", "button", "select", "textarea", "figure", "figcaption", "video", "audio", "source", "track", "canvas", "svg", "picture", "iframe"):
            setattr(self, f"en_{tag_lower}", False)

    def handle_data(self, data):
        if self.en_script or self.en_style:
            return

        texto = data.strip()
        if not texto:
            return

        # Procesamiento del texto según la bandera activa
        if self.en_a and self.href:
            self.salida.append(("link", texto, self.href))
        elif self.en_title:
            self.titulo_pagina = texto
        elif self.en_h1: self.salida.append(("texto", f"=== {texto.upper()} ==="))
        elif self.en_h2: self.salida.append(("texto", f"-- {texto} --"))
        elif self.en_h3: self.salida.append(("texto", f"- {texto} -"))
        elif self.en_h4 or self.en_h5 or self.en_h6: self.salida.append(("texto", f"• {texto} •"))
        elif self.en_li: self.salida.append(("texto", f"  • {texto}"))
        elif self.en_button: self.salida.append(("texto", f"[BOTÓN: {texto}]"))
        elif self.en_label: self.salida.append(("texto", f"{texto}:"))
        elif self.en_textarea: self.salida.append(("texto", f"[ÁREA DE TEXTO]\n{texto}\n[FIN ÁREA]"))
        elif self.en_th: self.salida.append(("texto", f"║ {texto} ║"))
        elif self.en_td: self.salida.append(("texto", f"  {texto}"))
        elif self.en_figcaption: self.salida.append(("texto", f"Figura: {texto}"))
        elif self.en_span: self.salida.append(("texto", texto))
        # Contenedores estructurales respetan indentación
        elif (self.en_header or self.en_footer or self.en_nav or 
                self.en_section or self.en_article or self.en_aside or self.en_div):
            prefijo = "    " * max(0, self.indent_level)
            self.salida.append(("texto", prefijo + texto))
        else:
            self.salida.append(("texto", texto))
