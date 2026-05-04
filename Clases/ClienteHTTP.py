import http.client

class ClienteHTTP:
    def buscarurl(self, url):
        if "/" in url:
            host, path = url.split("/", 1)
            path = "/" + path
        else:
            host = url
            path = "/"

        try:
            conn = http.client.HTTPConnection(host, 80)
            #conn = http.client.HTTPSConnection(host, 443) funciona
            conn.request("GET", path)
            response = conn.getresponse()
            status = response.status
            html = response.read().decode("utf-8", errors="replace")
            conn.close()
            return html, status
        except Exception as e:
            return f"<h1>Error al conectar</h1><p>{e}</p>", None