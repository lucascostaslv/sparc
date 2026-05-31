import numpy as np

from scenario import Scenario

class ScenarioSimulator:
    scenarios: list[Scenario]

    def __init__(self):
        self.scenarios = []


    def add_scenario(self, scenario: Scenario):
        self.scenarios.append(scenario)


    def simulate(self, scenario: Scenario) -> dict:

        simulation_result = {}
        total_consume_devices = 0.0

        simulation_result["scenario"] = scenario.name
        simulation_result["devices"] = []
        for device in scenario.devices:
            total_consume_devices += device.monthly_consumption()

            simulation_result["devices"].append({
                "name" : device.name,
                "daily_kwh" : device.daily_consumption(),
                "monthly_kwh" : device.monthly_consumption()
            })

        monthly_values = np.array([d["monthly_kwh"] for d in simulation_result["devices"]])
        simulation_result["total_monthly_kwh"] = float(np.sum(monthly_values))

        return simulation_result


    def compare(self, s1: Scenario, s2: Scenario) -> dict:

        comparation_result = {}
        simulation_1 = self.simulate(s1)
        simulation_2 = self.simulate(s2)
        
        comparation_result["scenario_1"] = simulation_1
        comparation_result["scenario_2"] = simulation_2

        t1 = simulation_1["total_monthly_kwh"]
        t2 = simulation_2["total_monthly_kwh"]
        comparation_result["difference_kwh"] = float(np.abs(t1 - t2))
        comparation_result["savings_percent"] = float(((t1 - t2) / t1 * 100)) if t1 > 0 else 0.0

        return comparation_result

