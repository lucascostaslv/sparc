from .device import Device


class EnergyCalculator:
    def calculate(self, device: Device) -> float:
        """Retorna o consumo mensal em kWh de um único dispositivo."""
        ...

    def calculate_all(self, devices: list[Device]) -> list[float]:
        """Retorna uma lista com o consumo mensal de cada dispositivo,
        na mesma ordem da lista recebida.
        """
        ...
