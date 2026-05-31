import numpy as np
import matplotlib; matplotlib.use("QtAgg")
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
from matplotlib.figure import Figure

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QComboBox, QMessageBox,
)
from PyQt6.QtCore import Qt

from scenario import Scenario
from simulator import ScenarioSimulator

TARIFF = 0.60
BREAK_EVEN_MONTHS = 60


class ComparisonTab(QWidget):
    def __init__(self, simulator: ScenarioSimulator):
        super().__init__()
        self.simulator  = simulator
        self._scenarios: list[Scenario] = []
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)

        sel_row = QHBoxLayout()
        sel_row.addWidget(QLabel("Cenário base:"))
        self.combo1 = QComboBox()
        sel_row.addWidget(self.combo1)
        sel_row.addSpacing(12); sel_row.addWidget(QLabel("vs")); sel_row.addSpacing(12)
        sel_row.addWidget(QLabel("Cenário novo:"))
        self.combo2 = QComboBox()
        sel_row.addWidget(self.combo2)
        compare_btn = QPushButton("Comparar"); compare_btn.setFixedWidth(100)
        compare_btn.clicked.connect(self._run_comparison)
        sel_row.addSpacing(12); sel_row.addWidget(compare_btn); sel_row.addStretch()

        self.fig = Figure(figsize=(11, 4), tight_layout=True)
        self.canvas = FigureCanvasQTAgg(self.fig)

        self.info_label = QLabel("Selecione dois cenários e clique em Comparar.")
        self.info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        layout.addLayout(sel_row)
        layout.addWidget(self.canvas)
        layout.addWidget(self.info_label)

    def refresh_combos(self, scenarios: list[Scenario]):
        self._scenarios = scenarios
        names = [s.name for s in scenarios]
        for combo in (self.combo1, self.combo2):
            current = combo.currentText()
            combo.blockSignals(True)
            combo.clear(); combo.addItems(names)
            idx = combo.findText(current)
            combo.setCurrentIndex(max(0, idx))
            combo.blockSignals(False)
        if len(scenarios) >= 2 and self.combo2.currentIndex() == self.combo1.currentIndex():
            self.combo2.setCurrentIndex(1)

    def _run_comparison(self):
        i1, i2 = self.combo1.currentIndex(), self.combo2.currentIndex()
        if i1 < 0 or i2 < 0 or i1 == i2:
            QMessageBox.warning(self, "Seleção inválida",
                                "Selecione dois cenários diferentes.")
            return
        s1, s2 = self._scenarios[i1], self._scenarios[i2]
        if not s1.devices or not s2.devices:
            QMessageBox.warning(self, "Cenário vazio",
                                "Ambos os cenários precisam ter dispositivos.")
            return

        comparison = self.simulator.compare(s1, s2)
        break_data = self.simulator.break_even(s1, s2, TARIFF, BREAK_EVEN_MONTHS)

        self.fig.clear()
        ax_bar  = self.fig.add_subplot(1, 2, 1)
        ax_line = self.fig.add_subplot(1, 2, 2)
        self._draw_bar_chart(ax_bar, comparison, s1, s2)
        self._draw_line_chart(ax_line, break_data, s1, s2)
        self.fig.tight_layout(); self.canvas.draw()

        bep = break_data["break_even_month"]
        if bep:
            self.info_label.setText(
                f"Ponto de equilíbrio: mês {bep} — "
                f"a partir desse mês '{s2.name}' passa a ser mais barato no acumulado."
            )
        else:
            self.info_label.setText(
                f"'{s2.name}' não compensa em {BREAK_EVEN_MONTHS} meses "
                f"com tarifa de R$ {TARIFF:.2f}/kWh."
            )

    def _draw_bar_chart(self, ax, comparison: dict, s1: Scenario, s2: Scenario):
        sim1, sim2 = comparison["scenario_1"], comparison["scenario_2"]
        all_names = list(dict.fromkeys(
            [d["name"] for d in sim1["devices"]] + [d["name"] for d in sim2["devices"]]
        ))
        map1 = {d["name"]: d["monthly_kwh"] for d in sim1["devices"]}
        map2 = {d["name"]: d["monthly_kwh"] for d in sim2["devices"]}
        v1 = np.array([map1.get(n, 0) for n in all_names])
        v2 = np.array([map2.get(n, 0) for n in all_names])
        x, w = np.arange(len(all_names)), 0.35
        ax.bar(x - w / 2, v1, w, label=s1.name, color="#4C72B0")
        ax.bar(x + w / 2, v2, w, label=s2.name, color="#55A868")
        ax.set_xticks(x); ax.set_xticklabels(all_names, rotation=30, ha="right", fontsize=8)
        ax.set_title("Consumo Mensal (kWh/mês)"); ax.set_ylabel("kWh/mês"); ax.legend(fontsize=8)

    def _draw_line_chart(self, ax, break_data: dict, s1: Scenario, s2: Scenario):
        months = break_data["months"]
        cum1   = break_data["cumulative_s1"]
        cum2   = break_data["cumulative_s2"]
        bep    = break_data["break_even_month"]

        ax.plot(months, cum1, label=f"{s1.name} (base)",  color="#4C72B0", linewidth=2)
        ax.plot(months, cum2, label=f"{s2.name} (novo)",  color="#E88720", linewidth=2, linestyle="--")

        if bep:
            ax.axvline(bep, color="red", linestyle=":", linewidth=1.5)
            ax.annotate(
                f"Break-even\nMês {bep}",
                xy=(bep, cum2[bep - 1]),
                xytext=(bep + 2, cum2[bep - 1] * 0.92),
                fontsize=8, color="red",
                arrowprops=dict(arrowstyle="->", color="red"),
            )

        ax.set_title(f"Custo Acumulado em {BREAK_EVEN_MONTHS} meses (R$)")
        ax.set_xlabel("Meses"); ax.set_ylabel("R$"); ax.legend(fontsize=8)
