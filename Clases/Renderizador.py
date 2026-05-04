import os
from html.parser import HTMLParser
#Recordatorios: 
#<h1> se refiere a los titulos/<p> se refiere a que ahora empieza un parrafo/<a> se refiere a los links
# .append() era para agregar cosas al final de la lista
# Esto (\n) es para los saltos de linea


class RenderizadorParser(HTMLParser):

    def __init__(self, area_contenido=None):
        super().__init__()

        # Área de texto donde se mostrará el contenido
        self.area_contenido = area_contenido

        self.ruta_actual = ""
        self.en_h1 = False
        self.en_a = False
        self.href = ""
        self.salida = []
        self.en_script = False
        self.en_style = False

    def renderizar(self, ruta):
        """
        Abre el archivo HTML, lo procesa y muestra el contenido
        """
        self.salida = [] #Limpia la lista
        self.ruta_actual = os.path.abspath(ruta) #Guarda la ruta del archivo / abspath (absolute path) es lo que nos devuelve la ruta

        with open(ruta, "r", encoding="utf-8") as archivo:
            contenido = archivo.read()

        self.feed(contenido)

        # Muestra el resultado en pantalla
        self._mostrar_en_area()

        return self.salida
    
    def renderizar_desde_string(self, html_string, ruta_base=""):
        """
        Procesa un string HTML directamente (sin leer archivo).
        ruta_base: carpeta raíz para resolver links relativos.
        """
        self.salida = []
        self.ruta_actual = os.path.abspath(ruta_base) if ruta_base else os.getcwd()

        self.feed(html_string)
        self._mostrar_en_area()

        return self.salida
    
    def _mostrar_en_area(self):
        """
        Inserta el contenido procesado en el área de texto
        """
        if self.area_contenido is None:
            return

        self.area_contenido.config(state="normal")
        self.area_contenido.delete("1.0", "end")

        for elemento in self.salida:

            if elemento[0] == "texto":
                self.area_contenido.insert("end", elemento[1] + "\n")

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


                #Estas lineas son las que cambian el color del link
                self.area_contenido.tag_bind(tag, "<Enter>", 
                    lambda e: self.area_contenido.tag_config(tag, foreground="red"))
                
                self.area_contenido.tag_bind(tag, "<Leave>", 
                    lambda e: self.area_contenido.tag_config(tag, foreground="blue"))
                

        self.area_contenido.config(state="disabled")

    def abrir_link(self, ruta):
        """
        Abre un link relativo basado en el archivo actual
        """
        carpeta_actual = os.path.dirname(self.ruta_actual)
        ruta_completa = os.path.join(carpeta_actual, ruta)

        self.renderizar(ruta_completa)

    def handle_starttag(self, tag, attrs):

        if tag == "script":
            self.en_script = True

        elif tag == "style":
            self.en_style = True

        if tag == "h1":
            self.en_h1 = True
            self.salida.append("\n")

        elif tag == "p":
            self.salida.append("\n")

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

        if tag == "h1":
            self.en_h1 = False
            self.salida.append("\n")

        elif tag == "a":
            self.en_a = False
            self.href = ""

    def handle_data(self, data):

        # Ignora contenido no visible
        if self.en_script == True or self.en_style == True:
            return

        texto = data.strip()

        if texto == "":
            return

        # Detecta links
        if self.en_a == True and self.href != "":
            self.salida.append(("link", texto, self.href))

        # Detecta títulos
        elif self.en_h1 == True:
            self.salida.append(("texto", texto.upper()))

        # Texto normal
        else:
            self.salida.append(("texto", texto))