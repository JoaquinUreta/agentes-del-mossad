import http.client

class ClienteHTTP:
    def buscarurl(self, url, timeout=10): 
        if "/" in url:
            host, path = url.split("/", 1)
            path = "/" + path
        else:
            host = url
            path = "/"

        try:
            conn = http.client.HTTPSConnection(host, 443, timeout=timeout)
            conn.request("GET", path)
            response = conn.getresponse()
            status = response.status
            html = response.read().decode("utf-8", errors="replace")
            conn.close()
            return html, status

        except TimeoutError:
            return "<h1>Tiempo de espera agotado</h1>", None

        except Exception as e:
            return f"<h1>Error al conectar</h1><p>{e}</p>", None