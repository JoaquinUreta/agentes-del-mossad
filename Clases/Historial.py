import tkinter as tk

class Historial:
    #Funcion para iniciar
    #===================================
    def __init__(self,limitante=10):
        self.historial=[]
        self.limite=limitante
    
    #===========================================
    #Funcion Agregar_historial
    #=============================================
    def agregar_historial(self,url):
        if self.historial and self.historial[-1]==url:#Comprueba que el historial no este vacio
            print("Direccion repetida")
            return 
        self.historial.append(url)
        if len(self.historial)>self.limite:
             self.historial.pop(0)

    #=============================================
    #Funcion obtener_url
    #===============================================
    def obtener_url(self, indice):
        historial_invertido= list(reversed(self.historial))

        if (indice<0 or indice >= len(historial_invertido)):
            print("Indice fuera de rango")
            return None

        return historial_invertido[indice]