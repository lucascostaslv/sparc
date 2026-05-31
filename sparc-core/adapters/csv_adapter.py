import csv
import json

from sparc_core.ports.data_port import DataPort


class CSVAdapter(DataPort):
    def save(self, scenarios: list, filepath: str) -> None:
        if filepath.endswith(".json"):
            self._save_json(scenarios, filepath)
        else:
            self._save_csv(scenarios, filepath)

    def load(self, filepath: str) -> list:
        if filepath.endswith(".json"):
            return self._load_json(filepath)
        return self._load_csv(filepath)

    # ------------------------------------------------------------------
    # JSON
    # ------------------------------------------------------------------

    def _save_json(self, scenarios: list, filepath: str) -> None:
        data = [
            {
                "name": s.name,
                "devices": [
                    {
                        "name": d.name,
                        "power_w": d.power_w,
                        "usage_hours": d.usage_hours,
                    }
                    for d in s.devices
                ],
            }
            for s in scenarios
        ]
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def _load_json(self, filepath: str) -> list:
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)

    # ------------------------------------------------------------------
    # CSV  (uma linha por dispositivo: scenario_name, name, power_w, usage_hours)
    # ------------------------------------------------------------------

    def _save_csv(self, scenarios: list, filepath: str) -> None:
        with open(filepath, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["scenario_name", "device_name", "power_w", "usage_hours"])
            for s in scenarios:
                for d in s.devices:
                    writer.writerow([s.name, d.name, d.power_w, d.usage_hours])

    def _load_csv(self, filepath: str) -> list:
        scenarios: dict[str, dict] = {}
        with open(filepath, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                sname = row["scenario_name"]
                if sname not in scenarios:
                    scenarios[sname] = {"name": sname, "devices": []}
                scenarios[sname]["devices"].append(
                    {
                        "name": row["device_name"],
                        "power_w": float(row["power_w"]),
                        "usage_hours": float(row["usage_hours"]),
                    }
                )
        return list(scenarios.values())
