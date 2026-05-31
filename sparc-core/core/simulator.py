from .scenario import Scenario


class ScenarioSimulator:
    def __init__(self):
        self.scenarios: list[Scenario] = []

    def add_scenario(self, scenario: Scenario) -> None:
        """Registra um cenário no simulador."""
        ...

    def simulate(self, scenario: Scenario) -> dict:
        """Executa a simulação de um cenário e retorna um dicionário com:
        {
            "scenario": str,           # nome do cenário
            "devices": [               # lista de dispositivos
                {
                    "name": str,
                    "daily_kwh": float,
                    "monthly_kwh": float,
                }
            ],
            "total_monthly_kwh": float
        }
        """
        ...

    def compare(self, s1: Scenario, s2: Scenario) -> dict:
        """Compara dois cenários e retorna um dicionário com:
        {
            "scenario_1": dict,        # resultado de simulate(s1)
            "scenario_2": dict,        # resultado de simulate(s2)
            "difference_kwh": float,   # s1.total - s2.total
            "savings_percent": float   # redução percentual de s1 para s2
        }
        """
        ...
