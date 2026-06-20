from tkinter import messagebox

class MotorBusqueda:

    def __init__(self):
        #Busqueda{"consulta":[(titulo,url)]}
        self.busquedas={
            "listar universidades chilenas": "consulta_1.html",
            "ultimas noticias de tecnologia": "consulta_2.html",
            "resultados de futbol chileno": "consulta_3.html",
            "mejores series de streaming": "consulta_4.html",
            "descubrimientos de ciencia reciente": "consulta_5.html",
            "guias de viajes por sudamerica": "consulta_6.html",
            "consejos de salud y bienestar": "consulta_7.html",
            "noticias de finanzas globales": "consulta_8.html",
            "plataformas de educacion online": "consulta_9.html",
            "eventos de cultura local": "consulta_10.html"
        }
    def buscar(self, texto):
        clave_usuario=self.normalizarTexto(texto)
        # busca en el diccionario de consultas para mostar un resultado, si no encuentra devuelve un None
        archivo_html=self.busquedas.get(clave_usuario)

        return archivo_html
    def normalizarTexto(self, texto):
        texto=texto.lower().strip()
        #normalizamos el texto quitando tildes
        limpiado={
            "á": "a",
            "é": "e",
            "í": "i",
            "ó": "o",
            "ú": "u",
        }
        for tilde, limpia in limpiado.items():
            texto = texto.replace(tilde, limpia)
        return texto