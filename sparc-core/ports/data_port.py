from abc import ABC, abstractmethod


class DataPort(ABC):
    @abstractmethod
    def save(self, scenarios: list, filepath: str) -> None:
        """Persiste a lista de cenários no caminho indicado.

        - Se filepath terminar em '.json', salva em JSON.
        - Se terminar em '.csv', salva em CSV.
        Cada cenário deve serializar seus dispositivos (name, power_w, usage_hours).
        """
        ...

    @abstractmethod
    def load(self, filepath: str) -> list:
        """Carrega e retorna a lista de cenários do arquivo indicado.

        Retorna uma lista de dicionários no formato:
        [
            {
                "name": str,           # nome do cenário
                "devices": [
                    {
                        "name": str,
                        "power_w": float,
                        "usage_hours": float
                    }
                ]
            }
        ]
        O adapter NÃO instancia objetos Device/Scenario — isso é responsabilidade
        de quem consome o DataPort.
        """
        ...
