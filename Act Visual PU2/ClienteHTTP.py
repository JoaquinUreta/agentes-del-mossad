import http.client
from RenderAvanzado import RenderizadorParserAvanzado


class ClienteHTTP:

    def buscarurl(self, url, timeout=10):
        # ── Validación de protocolo/host/puerto (Requerimiento 1, Hito 3) ──
        # Antes esta lógica vivía sin usarse en RenderAvanzado.soportes_url.
        # Ahora vive en RenderizadorParser y SÍ se ejecuta antes de conectar.
        try:
            protocolo, host, puerto, path = RenderizadorParserAvanzado.soportes_url(url)
        except ValueError as e:
            return f"<h1>{e}</h1>", None

        usar_https = (protocolo == "https")

        HEADERS = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,*/*;q=0.9",
            "Accept-Language": "es-419,es;q=0.9",
        }
        MAX_REDIRECCIONES = 5

        try:
            for _ in range(MAX_REDIRECCIONES):
                if usar_https:
                    conn = http.client.HTTPSConnection(host, puerto, timeout=timeout)
                else:
                    conn = http.client.HTTPConnection(host, puerto, timeout=timeout)

                conn.request("GET", path, headers=HEADERS)
                response = conn.getresponse()
                status = response.status

                # Seguir redirecciones 301 / 302 / 303 / 307 / 308
                if status in (301, 302, 303, 307, 308):
                    location = response.getheader("Location", "")
                    conn.close()
                    if not location:
                        return "<h1>Redirección sin destino</h1>", status
                    # Revalidamos la URL de destino con la misma regla de puertos
                    try:
                        protocolo, host, puerto, path = RenderizadorParserAvanzado.soportes_url(location)
                    except ValueError as e:
                        return f"<h1>{e}</h1>", status
                    usar_https = (protocolo == "https")
                    continue

                html = response.read().decode("utf-8", errors="replace")
                conn.close()
                return html, status

            return "<h1>Demasiadas redirecciones</h1>", None

        except TimeoutError:
            return "<h1>Tiempo de espera agotado</h1>", None
        except Exception as e:
            return f"<h1>Error al conectar</h1><p>{e}</p>", None