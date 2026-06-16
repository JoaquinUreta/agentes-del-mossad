import ipaddress
from urllib.parse import urlparse

class RenderAvanzado:
    def __init__(self):
        #Puertos disponibles solicitados:
        self.puertos_soportados = {80, 8080, 443, 3000, 5173}

    def soporte_url(self, url):
        #Comprobaciones si es http o https
        if not url.startswith(("http://", "https://")):
            url = "http://" + url
        resultado = urlparse(url)
        if resultado.scheme not in ("http", "https"):
            raise ValueError("Protocolo no soportado")
        
        #Para comprobar dominio
        host = resultado.hostname
        if not host:
            raise ValueError("Host inválido")
        tipo_host = self.tipo_host(host)
        if tipo_host == "invalido":
            raise ValueError(f"Host no válido: {host}")

        #Para comprobar los puertos
        puerto = resultado.port
        if puerto is None:
            puerto = 443 if resultado.scheme == "https" else 80
        if puerto not in self.puertos_soportados:
            #En caso de que no se encuentre los puertos disponibles se dara el mensaje siguiente:
            raise ValueError(f"Conexión a puerto {puerto} no soportada")

        path = resultado.path or "/"
        if resultado.query:
            path += "?" + resultado.query
        return resultado.scheme, host, puerto, path, tipo_host

    def tipo_host(self, host):
        if self.es_ip(host):
            return "ip"
        if self.es_dominio(host):
            return "dominio"
        return "invalido"

    def es_ip(self, host):
        try:
            ipaddress.ip_address(host)
            return True
        except ValueError:
            return False

    def es_dominio(self, host):
        if host == "localhost":
            return True
        if " " in host:
            return False
        if host.startswith(".") or host.endswith("."):
            return False
        if ".." in host:
            return False
        if self.es_ip(host):
            return False
        return "." in host