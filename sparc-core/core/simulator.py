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
        simulation_result["scenario"] = scenario.name
        simulation_result["devices"] = []

        for device in scenario.devices:
            simulation_result["devices"].append({
                "name":        device.name,
                "daily_kwh":   device.daily_consumption(),
                "monthly_kwh": device.monthly_consumption(),
            })

        monthly_values = np.array([d["monthly_kwh"] for d in simulation_result["devices"]])
        simulation_result["total_monthly_kwh"] = float(np.sum(monthly_values))
        return simulation_result

    def compare(self, s1: Scenario, s2: Scenario) -> dict:
        simulation_1 = self.simulate(s1)
        simulation_2 = self.simulate(s2)

        t1 = simulation_1["total_monthly_kwh"]
        t2 = simulation_2["total_monthly_kwh"]

        return {
            "scenario_1":       simulation_1,
            "scenario_2":       simulation_2,
            "difference_kwh":   float(np.abs(t1 - t2)),
            "savings_percent":  float((t1 - t2) / t1 * 100) if t1 > 0 else 0.0,
        }

    def break_even(self, s1: Scenario, s2: Scenario,
                   tariff: float, months: int = 60) -> dict:
        """Compara o custo acumulado de dois cenários ao longo do tempo.

        s1 — cenário base (atual).
        s2 — cenário novo (com dispositivos a adquirir, possivelmente parcelados).

        Retorna:
        {
            "months":           list[int],   # 1..months
            "cumulative_s1":    list[float], # custo acumulado do cenário base
            "cumulative_s2":    list[float], # custo acumulado do cenário novo (conta + parcelas)
            "break_even_month": int | None,  # mês onde s2 passa a compensar, ou None
            "scenario_1_name":  str,
            "scenario_2_name":  str,
        }
        """
        sim1 = self.simulate(s1)
        sim2 = self.simulate(s2)

        bill_s1 = sim1["total_monthly_kwh"] * tariff
        bill_s2 = sim2["total_monthly_kwh"] * tariff

        months_arr = np.arange(1, months + 1)

        inst_per_month = np.array([
            sum(d.installment_cost_at_month(int(m)) for d in s2.devices)
            for m in months_arr
        ])

        cum_s1 = np.cumsum(np.full(months, bill_s1))
        cum_s2 = np.cumsum(np.full(months, bill_s2) + inst_per_month)

        better = cum_s2 <= cum_s1
        break_even_month = int(np.argmax(better)) + 1 if better.any() else None

        return {
            "months":           months_arr.tolist(),
            "cumulative_s1":    cum_s1.tolist(),
            "cumulative_s2":    cum_s2.tolist(),
            "break_even_month": break_even_month,
            "scenario_1_name":  s1.name,
            "scenario_2_name":  s2.name,
        }
