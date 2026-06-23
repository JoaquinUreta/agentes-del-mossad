class NavegaAvanzada:
    def __init__(self):
        self.navegacion = []
        self.indice = -1

    def navegar(self, url):
        if self.indice >= 0 and self.navegacion[self.indice] == url:
            return
        if self.indice < len(self.navegacion)-1:
            self.navegacion = self.navegacion[:self.indice+1]
        self.navegacion.append(url)#Del historial se le van agregando al arreglo de NavegaAvanzada
        self.indice = len(self.navegacion)-1

    def atras(self):
        if self.puede_atras():#Retrocede al anterior elemento navegado
            self.indice -= 1
            return self.navegacion[self.indice]
        return None

    def adelante(self):
        if self.puede_adelante():#Avanza al elemento siguiente navegado
            self.indice += 1
            return self.navegacion[self.indice]
        return None

    def puede_atras(self):#Comprobacion si existen elementos atras
        return self.indice > 0

    def puede_adelante(self):#Comprobacion si existen elementos adelante
        return self.indice < len(self.navegacion) - 1