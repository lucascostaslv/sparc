class Device:
    name: str
    power_w: float
    usage_hours: float

    def __init__(self, name, power_w, usage_hours):
        self.name = name
        self.power_w = power_w
        self.usage_hours = usage_hours


    def daily_consumption(self) -> float:
        return self.power_w * self.usage_hours / 1000


    def monthly_consumption(self) -> float:
        return self.daily_consumption() * 30
