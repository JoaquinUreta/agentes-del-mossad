import os
from tkinter import messagebox

# Carpeta donde viven los archivos consulta_N.html, relativa a este archivo
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CARPETA_CONSULTAS = os.path.join(BASE_DIR, "..", "Consultas")


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
        """
        Busca el texto normalizado en el diccionario de consultas.
        Devuelve la ruta ABSOLUTA al archivo HTML dentro de la carpeta Consultas,
        o None si no hay coincidencia o el archivo no existe.
        """
        clave_usuario = self.normalizarTexto(texto)
        nombre_archivo = self.busquedas.get(clave_usuario)

        if nombre_archivo is None:
            return None

        ruta_absoluta = os.path.join(CARPETA_CONSULTAS, nombre_archivo)

        if not os.path.isfile(ruta_absoluta):
            return None

        return ruta_absoluta

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