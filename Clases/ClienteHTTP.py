import http.client

class ClienteHTTP:

    def enviar_get(self, host, ruta):
        conexion = http.client.HTTPConnection(host,80) #El host en teoria es el que nos dio el profe y el 80 se refiere al puerto

        headers = {
            "Host": host,
            "User-Agent": "ClienteHTTP/1.0"
        }
        
        #Esta es la solicitud como tal que enviara el codigo hacia el servidor.
        conexion.request("GET", ruta, headers=headers) 

        return conexion
    
    def buscarurl(self, url, timeout=10): 
        if "/" in url:
            host, path = url.split("/", 1)
            path = "/" + path
        else:
            host = url
            path = "/"

        try:
            conn = http.client.HTTPSConnection(host, 443, timeout=timeout)
            #conn = http.client.HTTPSConnection(host,80, timeout=timeout)
            #El puerto 80 no funciona
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