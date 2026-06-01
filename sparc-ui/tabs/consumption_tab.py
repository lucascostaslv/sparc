import numpy as np
import matplotlib; matplotlib.use("QtAgg")
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
from matplotlib.figure import Figure

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QFrame, QTableWidget, QTableWidgetItem,
    QHeaderView, QSizePolicy, QDoubleSpinBox,
)
from PyQt6.QtCore import Qt

from scenario import Scenario
from simulator import ScenarioSimulator

DEFAULT_TARIFF = 0.60


class ConsumptionTab(QWidget):
    def __init__(self, simulator: ScenarioSimulator):
        super().__init__()
        self.simulator = simulator
        self._card_labels: dict[str, QLabel] = {}
        self._last_scenario: Scenario | None = None
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)

        tariff_row = QHBoxLayout()
        tariff_row.addStretch()
        tariff_row.addWidget(QLabel("Tarifa (R$/kWh):"))
        self.tariff_spin = QDoubleSpinBox()
        self.tariff_spin.setRange(0.01, 9.99)
        self.tariff_spin.setDecimals(2)
        self.tariff_spin.setSingleStep(0.01)
        self.tariff_spin.setValue(DEFAULT_TARIFF)
        self.tariff_spin.valueChanged.connect(lambda _: self._do_refresh())
        tariff_row.addWidget(self.tariff_spin)

        cards = QHBoxLayout()
        cards.addWidget(self._make_card("c_total", "Consumo Total",  "0.00 kWh/mês"))
        cards.addWidget(self._make_card("c_cost",  "Custo Estimado", "R$ 0.00"))
        cards.addWidget(self._make_card("c_daily", "Média Diária",   "0.00 kWh/dia"))

        self.fig = Figure(figsize=(6, 3), tight_layout=True)
        self.canvas = FigureCanvasQTAgg(self.fig)

        self.table = QTableWidget(0, 6)
        self.table.setHorizontalHeaderLabels(
            ["Dispositivo", "Potência (W)", "Consumo (kWh/mês)",
             "Custo (R$/mês)", "% do Total", "Nível"]
        )
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)

        layout.addLayout(tariff_row)
        layout.addLayout(cards)
        layout.addWidget(self.canvas)
        layout.addWidget(self.table)

    def refresh(self, scenario: Scenario):
        self._last_scenario = scenario
        self._do_refresh()

    def _do_refresh(self):
        scenario = self._last_scenario
        if scenario is None:
            return
        tariff = self.tariff_spin.value()

        if not scenario.devices:
            self._set_card("c_total", "0.00 kWh/mês")
            self._set_card("c_cost",  "R$ 0.00")
            self._set_card("c_daily", "0.00 kWh/dia")
            self.table.setRowCount(0)
            self.fig.clear(); self.canvas.draw()
            return

        result = self.simulator.simulate(scenario)
        total  = result["total_monthly_kwh"]

        self._set_card("c_total", f"{total:.2f} kWh/mês")
        self._set_card("c_cost",  f"R$ {total * tariff:.2f}")
        self._set_card("c_daily", f"{total / 30:.2f} kWh/dia")

        self.fig.clear()
        ax = self.fig.add_subplot(111)
        names  = [d["name"] for d in result["devices"]]
        values = np.array([d["monthly_kwh"] for d in result["devices"]])
        bars = ax.bar(names, values, color="#4C72B0")
        ax.set_title(f"Consumo por Dispositivo — {scenario.name} (kWh/mês)")
        ax.set_ylabel("kWh/mês")
        ax.tick_params(axis="x", rotation=30)
        offset = float(values.max()) * 0.01 if len(values) else 0
        for bar, val in zip(bars, values):
            ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + offset,
                    f"{val:.2f}", ha="center", va="bottom", fontsize=8)
        self.fig.tight_layout(); self.canvas.draw()

        power_map = {d.name: d.power_w for d in scenario.devices}
        self.table.setRowCount(0)
        for d in result["devices"]:
            row = self.table.rowCount(); self.table.insertRow(row)
            pct   = (d["monthly_kwh"] / total * 100) if total > 0 else 0
            level = self._classify(pct)
            for col, val in enumerate([
                d["name"], f"{power_map.get(d['name'], 0):.0f}",
                f"{d['monthly_kwh']:.2f}", f"R$ {d['monthly_kwh'] * tariff:.2f}",
                f"{pct:.1f}%", level,
            ]):
                self.table.setItem(row, col, QTableWidgetItem(val))

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
