from .device import Device


class Scenario:
    def __init__(self, name: str):
        self.name = name
        self.devices: list[Device] = []

    def add_device(self, device: Device) -> None:
        """Adiciona um dispositivo ao cenário."""
        ...

    def remove_device(self, name: str) -> None:
        """Remove o dispositivo com o nome informado.
        Não faz nada se o nome não existir.
        """
        ...

    def total_consumption(self) -> float:
        """Retorna a soma do consumo mensal de todos os dispositivos do cenário."""
        ...
