class Device:
    def __init__(self, name: str, power_w: float, usage_hours: float):
        self.name = name
        self.power_w = power_w
        self.usage_hours = usage_hours

    def daily_consumption(self) -> float:
        """Retorna o consumo diário em kWh.
        Fórmula: power_w * usage_hours / 1000
        """
        ...

    def monthly_consumption(self) -> float:
        """Retorna o consumo mensal em kWh (considera 30 dias)."""
        ...
