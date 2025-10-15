# backend/logica.py
class Calculadora:
    """Ejemplo de backend: lógica de negocio separada del frontend."""

    def sumar(self, a: float, b: float) -> float:
        return a + b

    def restar(self, a: float, b: float) -> float:
        return a - b

    def multiplicar(self, a: float, b: float) -> float:
        return a * b

    def dividir(self, a: float, b: float) -> float:
        if b == 0:
            raise ValueError("No se puede dividir por cero.")
        return a / b
