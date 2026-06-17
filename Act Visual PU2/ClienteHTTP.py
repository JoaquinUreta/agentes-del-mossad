import http.client


class ClienteHTTP:

    def buscarurl(self, url, timeout=10):
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