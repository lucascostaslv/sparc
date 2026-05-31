import numpy as np

from device import Device


class Scenario:
    name: str
    devices: list[Device]

    def __init__(self, name):
        self.name = name
        self.devices = []


    def add_device(self, device: Device):
        self.devices.append(device)


    def remove_device(self, name: str):
        self.devices = [device for device in self.devices if device.name != name]


    def total_consumption(self) -> float:
        return float(np.sum([d.monthly_consumption() for d in self.devices]))
