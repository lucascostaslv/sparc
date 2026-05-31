from abc import ABC, abstractmethod


class OutputPort(ABC):
    @abstractmethod
    def display_consumption(self, data: dict) -> None:
        """Exibe o gráfico de consumo por dispositivo.

        Espera o dict retornado por ScenarioSimulator.simulate():
        {
            "scenario": str,
            "devices": [{"name": str, "daily_kwh": float, "monthly_kwh": float}],
            "total_monthly_kwh": float
        }
        """
        ...

    @abstractmethod
    def display_comparison(self, comparison: dict) -> None:
        """Exibe o gráfico de barras duplas: atual vs. otimizado.

        Espera o dict retornado por ScenarioSimulator.compare():
        {
            "scenario_1": dict,
            "scenario_2": dict,
            "difference_kwh": float,
            "savings_percent": float
        }
        """
        ...
