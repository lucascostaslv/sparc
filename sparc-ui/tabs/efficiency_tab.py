import numpy as np
import matplotlib; matplotlib.use("QtAgg")
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
from matplotlib.figure import Figure

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QFrame, QTableWidget, QTableWidgetItem,
    QHeaderView, QSizePolicy,
)
from PyQt6.QtCore import Qt

from device import Device
from scenario import Scenario
from simulator import ScenarioSimulator


class EfficiencyTab(QWidget):
    def __init__(self, simulator: ScenarioSimulator):
        super().__init__()
        self.simulator = simulator
        self._card_labels: dict[str, QLabel] = {}
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)

        cards = QHBoxLayout()
        cards.addWidget(self._make_card("e_current",   "Consumo Atual",         "0.00 kWh/mês"))
        cards.addWidget(self._make_card("e_optimized", "Consumo Otimizado",     "0.00 kWh/mês"))
        cards.addWidget(self._make_card("e_savings",   "Potencial de Economia", "0.00 kWh (0.0%)"))

        self.fig = Figure(figsize=(6, 3), tight_layout=True)
        self.canvas = FigureCanvasQTAgg(self.fig)

        self.table = QTableWidget(0, 3)
        self.table.setHorizontalHeaderLabels(
            ["Sugestão", "Economia Estimada (kWh/mês)", "Impacto"]
        )
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)

        layout.addLayout(cards)
        layout.addWidget(self.canvas)
        layout.addWidget(self.table)

    def refresh(self, scenario: Scenario):
        if not scenario.devices:
            self._set_card("e_current",   "0.00 kWh/mês")
            self._set_card("e_optimized", "0.00 kWh/mês")
            self._set_card("e_savings",   "0.00 kWh (0.0%)")
            self.table.setRowCount(0)
            self.fig.clear(); self.canvas.draw()
            return

        result = self.simulator.simulate(scenario)
        suggestions, optimized = self._generate_optimized(scenario, result)
        comparison = self.simulator.compare(scenario, optimized)

        t1 = comparison["scenario_1"]["total_monthly_kwh"]
        t2 = comparison["scenario_2"]["total_monthly_kwh"]
        self._set_card("e_current",   f"{t1:.2f} kWh/mês")
        self._set_card("e_optimized", f"{t2:.2f} kWh/mês")
        self._set_card("e_savings",
                       f"{comparison['difference_kwh']:.2f} kWh ({comparison['savings_percent']:.1f}%)")

        self.fig.clear()
        ax = self.fig.add_subplot(111)
        names    = [d["name"] for d in result["devices"]]
        cur_vals = np.array([d["monthly_kwh"] for d in result["devices"]])
        opt_map  = {d.name: d.monthly_consumption() for d in optimized.devices}
        opt_vals = np.array([opt_map.get(n, 0) for n in names])
        x, w = np.arange(len(names)), 0.35
        ax.bar(x - w / 2, cur_vals, w, label="Atual",     color="#4C72B0")
        ax.bar(x + w / 2, opt_vals, w, label="Otimizado", color="#55A868")
        ax.set_xticks(x); ax.set_xticklabels(names, rotation=30, ha="right")
        ax.set_title("Atual vs. Otimizado (kWh/mês)"); ax.set_ylabel("kWh/mês"); ax.legend()
        self.fig.tight_layout(); self.canvas.draw()

        self.table.setRowCount(0)
        for s in suggestions:
            row = self.table.rowCount(); self.table.insertRow(row)
            for col, val in enumerate([s["text"], f"{s['savings']:.2f}", s["impact"]]):
                self.table.setItem(row, col, QTableWidgetItem(val))

    # ------------------------------------------------------------------ #
    # Optimization logic                                                   #
    # ------------------------------------------------------------------ #

    def _generate_optimized(self, scenario: Scenario, result: dict):
        total = result["total_monthly_kwh"]
        suggestions, optimized = [], Scenario("Otimizado")
        reductions = {
            "Alto":  (0.30, "Substituir por modelo mais eficiente"),
            "Médio": (0.20, "Reduzir uso em 20%"),
            "Baixo": (0.10, "Reduzir uso em 10%"),
        }
        for d in result["devices"]:
            name    = d["name"]
            monthly = d["monthly_kwh"]
            pct     = (monthly / total * 100) if total > 0 else 0
            level   = self._classify(pct)
            src     = next(dev for dev in scenario.devices if dev.name == name)
            reduction, action = reductions[level]
            new_hours = src.usage_hours * (1 - reduction)
            savings   = monthly - (src.power_w * new_hours / 1000 * 30)
            suggestions.append({"text": f"{action}: {name}", "savings": savings, "impact": level})
            optimized.add_device(Device(name, src.power_w, new_hours))
        return suggestions, optimized

    # ------------------------------------------------------------------ #
    # Helpers                                                              #
    # ------------------------------------------------------------------ #

    def _make_card(self, key: str, title: str, initial: str) -> QFrame:
        frame = QFrame(); frame.setFrameShape(QFrame.Shape.StyledPanel)
        frame.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        from PyQt6.QtWidgets import QVBoxLayout
        vbox = QVBoxLayout(frame)
        t = QLabel(title); t.setAlignment(Qt.AlignmentFlag.AlignCenter)
        v = QLabel(initial); v.setAlignment(Qt.AlignmentFlag.AlignCenter)
        vbox.addWidget(t); vbox.addWidget(v)
        self._card_labels[key] = v
        return frame

    def _set_card(self, key: str, text: str):
        self._card_labels[key].setText(text)

    def _classify(self, pct: float) -> str:
        if pct >= 30: return "Alto"
        if pct >= 15: return "Médio"
        return "Baixo"
