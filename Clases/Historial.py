class Historial:
    #================== Funcion para iniciar ==============
    def __init__(self,limitante=10):
        self.historial=[]
        self.limite=limitante
    
    #=============== Funcion Agregar_historial ======================
    
    def agregar_historial(self,url):
        if self.historial and self.historial[-1]==url:#Comprueba que el historial no este vacio
            return #Retorna si los url estan duplicados consecutivamente
        self.historial.append(url)
        if len(self.historial)>self.limite:#Limita el historial a 10 elementos
             self.historial.pop(0)#Elimina el url mas antiguo

    #========================= Funcion obtener_url ===================
    def obtener_url(self, indice):
        historial_invertido= list(reversed(self.historial))
        if (indice<0 or indice >= len(historial_invertido)):#Ordena del mas reciente a mas antiguo
            return None

        return historial_invertido[indice]