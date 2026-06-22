import http.client
import json
import socket
import urllib.request

class AsistenteIA:
    def __init__(self, api_key):
        self.api_key = api_key
        self.modelo = "gemini-2.5-flash-lite"
        self.host = "generativelanguage.googleapis.com"
        self.path = f"/v1/models/{self.modelo}:generateContent?key={self.api_key}"
        self.headers = {"Content-Type": "application/json"}

    def generar_respuesta(self, pregunta):
        """Envía la consulta a Gemini y devuelve la respuesta formateada."""
        body = {
            "contents": [{"parts": [{"text": pregunta}]}]
        }
        body_json = json.dumps(body)

        try:
            # Conexión con un timeout definido de 10 segundos
            conn = http.client.HTTPSConnection(self.host, timeout=10)
            conn.request("POST", self.path, body=body_json, headers=self.headers)

            response = conn.getresponse()
            data = response.read().decode("utf-8")

            if response.status == 200:
                result = json.loads(data)
                respuesta = result["candidates"][0]["content"]["parts"][0]["text"]
                return respuesta if respuesta.strip() else "Error: El comando no generó ninguna respuesta."
            else:
                return f"Error: No es posible conectarse a Gemini. ({response.status} - {response.reason})"

        except socket.timeout:
            return "Error: El tiempo de espera de la solicitud superó los 10 segundos."
        except Exception as e:
            return "Error: No es posible conectarse a Gemini. Revisa tu conexión de red."



    def cambiar_version(self): ## Esto es para la defensa, no es necesario modificarlo ni mostarlo en pantalla, no lo pide el proyecto
        API_KEY = self.api_key
        url = f"https://generativelanguage.googleapis.com/v1/models?key={API_KEY}"

        req = urllib.request.Request(url, method="GET")
        try:
            with urllib.request.urlopen(req) as response:
                modelos = json.loads(response.read().decode("utf-8"))
                print("--- Modelos disponibles en tu proyecto ---")
                for modelo in modelos.get("models", []):
                    print(f"- {modelo['name']}")
        except urllib.error.HTTPError as e:
            print(f"Error: {e.code}")
            print(e.read().decode("utf-8"))
    
