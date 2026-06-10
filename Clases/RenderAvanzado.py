from urllib.parse import urlparse

class RenderAvanzado:
    def soportes_url(url):
        puertos_permitidos = {80, 443, 8080, 3000, 5173}
        if not url.startswith(("http://", "https://")):
         url = "https://" + url
        parsed = urlparse(url)
        protocolo = parsed.scheme.lower()
        host = parsed.hostname
        if not host:
            raise ValueError("URL inválida: host no válido")
        puerto = parsed.port
        if puerto is None:
            puerto = 443 if protocolo == "https" else 80
        if puerto not in puertos_permitidos:
            raise ValueError(f"Conexión a puerto {puerto} no soportada" )
        path = parsed.path or "/"
        return protocolo, host, puerto, path