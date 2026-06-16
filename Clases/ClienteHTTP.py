import http.client
import socket
from urllib.parse import urljoin
from RenderAvanzado import RenderAvanzado

class ClienteHTTP:
    """
    Cliente HTTP/HTTPS simple que realiza peticiones GET a una URL dada.
    Soporta tanto conexiones seguras (HTTPS) como no seguras (HTTP),
    y maneja errores de conexión y tiempo de espera.
    """
    def __init__(self):
        self.render = RenderAvanzado()
        self.estado = ""
        self.headers_respuesta = {}

    def buscarurl(self, url, timeout=10):
        """
        Realiza una petición HTTP GET a la URL especificada y retorna
        el contenido HTML de la respuesta junto con el código de estado.

        Parámetros:
            url (str): URL completa a consultar (con o sin esquema http/https).
            timeout (int): Segundos máximos de espera antes de abortar la conexión.
                           Por defecto es 10 segundos.

        Proceso:
            1. Detecta si la URL usa HTTPS o HTTP y elimina el prefijo del esquema.
            2. Separa el host del path (ruta). Si no hay '/', el path se asume '/'.
            3. Abre una conexión HTTPSConnection (puerto 443) o HTTPConnection (puerto 80)
               según el protocolo detectado.
            4. Envía la petición GET al path indicado.
            5. Lee la respuesta: código de estado y cuerpo HTML decodificado en UTF-8.
            6. Cierra la conexión y retorna el HTML junto al código de estado.

        Retorna:
            tuple(str, int | None):
                - str: El HTML recibido como string. En caso de error, retorna
                       un HTML de error descriptivo.
                - int | None: Código de estado HTTP (ej. 200, 404) o None si
                              no se pudo establecer conexión (error o timeout).

        Manejo de errores:
            - TimeoutError: Retorna un HTML indicando tiempo agotado y None como status.
            - Cualquier otra excepción: Retorna un HTML con el mensaje de error y None.
        """
        MAX_REDIRECCIONES = 5
        try:
            protocolo, host, puerto, path,tipo = self.render.soporte_url(url)
            for _ in range(MAX_REDIRECCIONES):
                conn = None
                try:
                    headers = {
                        "Host": host,
                        "User-Agent": "...",
                        "Accept": "text/html,application/xhtml+xml,*/*;q=0.9",
                        "Accept-Language": "es-419,es;q=0.9",
                        "Connection": "close"
                        }
                    try:
                        if protocolo == "https":
                            conn = http.client.HTTPSConnection(host, puerto or 443, timeout=timeout)
                        else:
                            conn = http.client.HTTPConnection(host, puerto or 80, timeout=timeout)
                        conn.request("GET", path, headers=headers)
                        response = conn.getresponse()
                    except Exception:
                        if protocolo == "https":
                            conn = http.client.HTTPConnection(host, 80, timeout=timeout)
                            conn.request("GET", path, headers=headers)
                            response = conn.getresponse()
                        else:
                            raise
                    self.estado = f"{response.status} {response.reason}"
                    self.headers_respuesta = dict(response.getheaders())
                    if response.status in (301, 302, 303, 307, 308):
                        location = response.getheader("Location")
                        if not location:
                            return ("<h1>Redirección sin destino</h1>", response.status)
                        location = urljoin(f"{protocolo}://{host}", location)
                        protocolo, host, puerto, path, tipo = self.render.soporte_url(location)
                        continue
                    cuerpo = response.read().decode("utf-8", errors="replace")
                    return cuerpo, response.status
                finally:
                    if conn:
                        conn.close()
            return ("<h1>Demasiadas redirecciones</h1>", None)
        except socket.timeout:
            self.estado = "Timeout"
            return ("<h1>Tiempo de espera agotado</h1>", None)
        except Exception as e:
            self.estado = f"Error: {type(e).__name__}"
            return ("<h1>Error al conectar</h1>", None)