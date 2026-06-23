import os

class NavegaOffline:
    """
    Clase responsable de gestionar la navegación y lectura de archivos 
    locales en el computador (Modo Offline).
    Cumple con el Requerimiento 2 del Hito 3.
    """
    def __init__(self):
        self.ruta_actual = ""

    def leer_archivo_local(self, ruta):
        """
        Intenta abrir y leer un archivo local.
        Retorna el contenido en texto (HTML) o un mensaje de error formateado en HTML.
        """
        self.ruta_actual = os.path.abspath(ruta)
        try:
            with open(self.ruta_actual, "r", encoding="utf-8") as archivo:
                contenido = archivo.read()
            return contenido
        except FileNotFoundError:
            return f"<h1>Error 404 Local</h1><p>El archivo no existe en la ruta: {self.ruta_actual}</p>"
        except Exception as e:
            return f"<h1>Error Local</h1><p>No se pudo leer el archivo: {str(e)}</p>"

    def obtener_ruta_absoluta(self, enlace_relativo):
        """
        Calcula la ruta absoluta de un enlace local basándose en 
        la carpeta del archivo donde el usuario está actualmente.
        """
        if not self.ruta_actual:
            return os.path.abspath(enlace_relativo)
            
        carpeta_actual = os.path.dirname(self.ruta_actual)
        ruta_completa = os.path.normpath(os.path.join(carpeta_actual, enlace_relativo))
        return ruta_completa