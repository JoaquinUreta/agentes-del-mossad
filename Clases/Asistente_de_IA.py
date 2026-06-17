import http.client
import json
import socket

class AsistenteIa:

    def __init__(self):
        #Esta clave es de una cuenta secundaria mia
        self.API_KEY = ""  # API key de Gemini

        self.MODELO = "gemini-3.5-flash"
        self.HOST = "generativelanguage.googleapis.com"
        self.PATH = f"/v1/models/{self.MODELO}:generateContent?key={self.API_KEY}"

    def enviar_peticion(self,comando_texto):

        #Estrucutra de peticiones estandar para Gemini
        headers = {
            "Content-Type": "application/json"
        }
        body = {
            "contents": [
                {
                    "parts": [
                        {"text": self.comando_texto}
                    ]
                }
            ]
        }


        body_json = json.dumps(body)

        #Conexion a Gemini Mediante HTTP Client y POST
        try:
            conn = http.client.HTTPSConnection(self.HOST, timeout=10)
            conn.request("POST", self.PATH, body=body_json, headers=headers)

            #Almacenar respuesta de Gemini usando UFT 8
            response = conn.getresponse() 
            data = response.read().decode("utf-8")
            conn.close()

            #Verificar de respuesta exitosa desde Gemini
            if response.status == 200:
                response_data = json.loads(data) #Esto es lo que devuelve la ia
                
                # 2. VALIDACIÓN DE RESPUESTA VACÍA: Navegación segura por el JSON
                candidatos = response_data.get("candidates", [])
                if not candidatos:
                    return "<p style='color: red;'>Error: El comando no generó ninguna respuesta desde Gemini.</p>"
                
                partes = candidatos[0].get("content", {}).get("parts", [])
                if not partes:
                    return "<p style='color: red;'>Error: El comando no generó ninguna respuesta desde Gemini.</p>"
                
                texto_respuesta = partes[0].get("text", "").strip()
                if not texto_respuesta:
                    return "<p style='color: red;'>Error: El comando no generó ninguna respuesta desde Gemini.</p>"

                # Si todo está correcto, devuelve la respuesta de la IA
                return texto_respuesta
            
            else:
                # Error en la API (ej. API Key mal escrita, cuota excedida)
                return f"<p style='color: red;'>Error de API: {response.status} - {response.reason}</p>"

        # 3. CAPTURA DE TIMEOUT Y FALLOS DE RED
        except socket.timeout: #La ventana de error en caso de que demore mas de 10 segundos
            return "<p style='color: red;'>Error: Tiempo de espera de 10 segundos superado.</p>"
        except (http.client.HTTPException, ConnectionError, socket.error): #Error en caso de problemas con la conexion
            return "<p style='color: red;'>Error: No es posible conectarse a Gemini (Fallo de red).</p>"
        except Exception as e:
            # Ventana de eror para cualquier otro fallo no contemplado
            return f"<p style='color: red;'>Error inesperado: {str(e)}</p>"


#Test terminal

pregunta= print(str(input("Pregunta: ")))

            

