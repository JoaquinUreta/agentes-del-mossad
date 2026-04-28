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