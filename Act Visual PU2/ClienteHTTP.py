import http.client


class ClienteHTTP:
    """
    Cliente HTTP/HTTPS simple que realiza peticiones GET a una URL dada.
    Soporta tanto conexiones seguras (HTTPS) como no seguras (HTTP),
    y maneja errores de conexión y tiempo de espera.
    """

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
        # Detectar protocolo y limpiar la URL
        if url.startswith("https://"):
            usar_https = True
            url = url[len("https://"):]
        elif url.startswith("http://"):
            usar_https = False
            url = url[len("http://"):]
        else:
            usar_https = True  # Por defecto HTTPS si no especifica

        # Separar host y path
        if "/" in url:
            host, path = url.split("/", 1)
            path = "/" + path
        else:
            host = url
            path = "/"

        HEADERS = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,*/*;q=0.9",
            "Accept-Language": "es-419,es;q=0.9",
        }
        MAX_REDIRECCIONES = 5

        try:
            for _ in range(MAX_REDIRECCIONES):
                if usar_https:
                    conn = http.client.HTTPSConnection(host, 443, timeout=timeout)
                else:
                    conn = http.client.HTTPConnection(host, 80, timeout=timeout)

                conn.request("GET", path, headers=HEADERS)
                response = conn.getresponse()
                status = response.status

                # Seguir redirecciones 301 / 302 / 303 / 307 / 308
                if status in (301, 302, 303, 307, 308):
                    location = response.getheader("Location", "")
                    conn.close()
                    if not location:
                        return "<h1>Redirección sin destino</h1>", status
                    # Actualizar host/path con la nueva URL
                    if location.startswith("https://"):
                        usar_https = True
                        location = location[len("https://"):]
                    elif location.startswith("http://"):
                        usar_https = False
                        location = location[len("http://"):]
                    # Redirección relativa (solo cambia el path)
                    if "/" in location:
                        host, path = location.split("/", 1)
                        path = "/" + path
                    else:
                        host = location
                        path = "/"
                    continue

                html = response.read().decode("utf-8", errors="replace")
                conn.close()
                return html, status

            return "<h1>Demasiadas redirecciones</h1>", None

        except TimeoutError:
            return "<h1>Tiempo de espera agotado</h1>", None
        except Exception as e:
            return f"<h1>Error al conectar</h1><p>{e}</p>", None