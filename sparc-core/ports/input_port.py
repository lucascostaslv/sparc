from abc import ABC, abstractmethod


class InputPort(ABC):
    @abstractmethod
    def get_device_data(self) -> dict:
        """Coleta dados de um dispositivo a partir da entrada do usuário.

        Retorna um dicionário com:
        {
            "name": str,          # nome do dispositivo
            "power_w": float,     # potência em Watts
            "usage_hours": float  # horas de uso por dia
        }
        """
        ...

    @abstractmethod
    def get_scenario_name(self) -> str:
        """Coleta o nome de um cenário a partir da entrada do usuário."""
        ...
