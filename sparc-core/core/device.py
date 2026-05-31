from __future__ import annotations
from bills import InstallmentsDevices


class Device:
    name: str
    power_w: float
    usage_hours: float
    cost_price: float
    installments: InstallmentsDevices | None

    def __init__(self, name: str, power_w: float, usage_hours: float, cost_price: float = 0.0, installments: InstallmentsDevices | None = None):
        self.name = name
        self.power_w = power_w
        self.usage_hours = usage_hours
        self.cost_price = cost_price
        self.installments = installments

    def daily_consumption(self) -> float:
        return self.power_w * self.usage_hours / 1000

    def monthly_consumption(self) -> float:
        return self.daily_consumption() * 30

    def installment_cost_at_month(self, month: int) -> float:
        if self.installments is None:
            return 0.0
        if month > self.installments.qdt_installments:
            return 0.0
        if self.installments.value_installment > 0:
            return self.installments.value_installment
        if self.installments.qdt_installments > 0 and self.cost_price > 0:
            return self.cost_price / self.installments.qdt_installments
        return 0.0
