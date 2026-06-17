class MotorBusqueda:

    def __init__(self):
        #Busqueda{"consulta":[(titulo,url)]}
        self.busquedas = {}

    def buscar(self, texto):
        texto = texto.lower().strip()
        if texto in self.busquedas:
            return self.busquedas[texto][:10]
        return []