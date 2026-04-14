from html.parser import HTMLParser
#Recordatorios: 
#<h1> se refiere a los titulos/<p> se refiere a que ahora empieza un parrafo/<a> se refiere a los links
# .append() era para agregar cosas al final de la lista
# Esto (\n) es para los saltos de linea


class RenderizadorParser(HTMLParser):

    def __init__(self):
        super().__init__()
        self.en_h1 = False #Para leer los titulos
        self.en_a = False #Para leer los vinculos
        self.href = "" #Leer el contenido del link
        self.salida = []  #Aqui vamos guardando el texto que se esta procesando
        self.en_script=False
        self.en_style=False

    def renderizar(self, ruta):

        self.salida = [] #Aqui se resetea todo lo guardado, para cuando el usuario carge otra pagina en la misma ventana

        try:
            #El with lo que hara es habrir el archivo y lueggo lo cerrara automaticamente cuando termine
            with open(ruta, "r", encoding="utf-8") as archivo:  #habre la ruta, la letra r es para leer el html y el encoding sirve para leer interpretar ciertos caracteres como la ñ
                contenido = archivo.read() #leera todo el archivo como texto

            self.feed(contenido) #le dara todo el contenido del documento al parser

            return "\n".join(self.salida) #El join une todos los elementos de una lista usando un separar que es en este caso es \n 

        except Exception as e:  #Esto es lo que tirara el mensaje de error en caso de que la ruta esta mal u algun otro problema
            return f"Error: {e}"

    def handle_starttag(self, tag, attrs): #Detectara el tipo de etiqueta
        if tag=="script":
            self.en_script=True

        elif tag=="style":
            self.en_style=True

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

    def handle_endtag(self, tag):  #Cerrara las etiquetas
        if tag=="script":
            self.en_script=False
            
        elif tag=="style":
            self.en_style=False
    
        if tag == "h1":
            self.en_h1 = False
            self.salida.append("\n")

        elif tag == "a":
            self.en_a = False
            self.href = ""

    def handle_data(self, data):  #Esto leera el texto dentro de las etiquetas
        if self.en_script==True or self.en_style==True:
            return
        
        texto = data.strip()  #Elimina los espacios en blanco al inicio y al final
        if not texto: #si no tenemos texto hara el return para deternse
            return

        if self.en_h1:
            self.salida.append(texto.upper()) #Si estamos en un titulo pone las letras mayusculas

        elif self.en_a: #Agrega el link como texto mas su destino
            self.salida.append(f"{texto} (link a: {self.href})")

        else:
            self.salida.append(texto)  #Si el texto no tiene nada en especial agregalo a la lista normal