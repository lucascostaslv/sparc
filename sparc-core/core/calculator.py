import numpy as np

from device import Device


class EnergyCalculator:
    def calculate(self, device: Device) -> float:
        return device.monthly_consumption()

    def calculate_all(self, devices: list[Device]) -> list[float]:
        powers = np.array([d.power_w for d in devices])
        hours = np.array([d.usage_hours for d in devices])
        return (powers * hours / 1000 * 30).tolist()

