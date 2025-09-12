# src/meu_pacote/modulo.py

def somar(a, b):
    """Esta função retorna a soma de dois números."""
    return a + b

def subtrair(a, b):
    """Esta função retorna a diferença entre dois números."""
    return a - b

class Calculadora:
    def __init__(self, valor_inicial=0):
        self.valor = valor_inicial
    
    def adicionar(self, x):
        self.valor += x
        return self.valor
