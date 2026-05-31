import csv
import json

from ports.data_port import DataPort


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
        data = []
        for s in scenarios:
            devices = []
            for d in s.devices:
                entry = {
                    "name":         d.name,
                    "power_w":      d.power_w,
                    "usage_hours":  d.usage_hours,
                    "cost_price":   d.cost_price,
                }
                if d.installments is not None:
                    entry["installments_qty"]   = d.installments.qdt_installments
                    entry["installment_value"]  = d.installments.value_installment
                else:
                    entry["installments_qty"]  = 0
                    entry["installment_value"] = 0.0
                devices.append(entry)
            data.append({"name": s.name, "devices": devices})

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def _load_json(self, filepath: str) -> list:
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)

    # ------------------------------------------------------------------
    # CSV  (uma linha por dispositivo)
    # ------------------------------------------------------------------

    _CSV_FIELDS = [
        "scenario_name", "device_name", "power_w", "usage_hours",
        "cost_price", "installments_qty", "installment_value",
    ]

    def _save_csv(self, scenarios: list, filepath: str) -> None:
        with open(filepath, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(self._CSV_FIELDS)
            for s in scenarios:
                for d in s.devices:
                    qty = d.installments.qdt_installments if d.installments else 0
                    val = d.installments.value_installment if d.installments else 0.0
                    writer.writerow([s.name, d.name, d.power_w, d.usage_hours,
                                     d.cost_price, qty, val])

    def _load_csv(self, filepath: str) -> list:
        scenarios: dict[str, dict] = {}
        with open(filepath, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                sname = row["scenario_name"]
                if sname not in scenarios:
                    scenarios[sname] = {"name": sname, "devices": []}
                scenarios[sname]["devices"].append({
                    "name":              row["device_name"],
                    "power_w":           float(row["power_w"]),
                    "usage_hours":       float(row["usage_hours"]),
                    "cost_price":        float(row.get("cost_price", 0)),
                    "installments_qty":  int(float(row.get("installments_qty", 0))),
                    "installment_value": float(row.get("installment_value", 0)),
                })
        return list(scenarios.values())
