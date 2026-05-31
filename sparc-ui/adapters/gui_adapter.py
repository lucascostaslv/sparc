import numpy as np
import matplotlib
matplotlib.use("QtAgg")
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
from matplotlib.figure import Figure

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QTabWidget,
    QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QComboBox,
    QTableWidget, QTableWidgetItem, QHeaderView,
    QFrame, QFileDialog, QMessageBox, QSizePolicy, QInputDialog,
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QDoubleValidator, QAction

from device import Device
from scenario import Scenario
from simulator import ScenarioSimulator
from calculator import EnergyCalculator
from bills import InstallmentsDevices
from adapters.csv_adapter import CSVAdapter

TARIFF = 0.60  # R$/kWh
BREAK_EVEN_MONTHS = 60


class MainWindow(QMainWindow):

    def __init__(self):
        super().__init__()
        self.setWindowTitle("SPARC — Sistema de Análise de Consumo")
        self.setMinimumSize(1024, 720)

        self.scenarios: list[Scenario] = [Scenario("Principal")]
        self.active_scenario: Scenario = self.scenarios[0]

        self.simulator   = ScenarioSimulator()
        self.calculator  = EnergyCalculator()
        self.csv_adapter = CSVAdapter()
        self._card_labels: dict[str, QLabel] = {}

        self._setup_menu()
        self._setup_tabs()

    # ------------------------------------------------------------------ #
    # Menu                                                                 #
    # ------------------------------------------------------------------ #

    def _setup_menu(self):
        session_menu = self.menuBar().addMenu("Sessão")
        save_act = QAction("Salvar sessão...", self)
        save_act.triggered.connect(self._save_session)
        load_act = QAction("Carregar sessão...", self)
        load_act.triggered.connect(self._load_session)
        session_menu.addAction(save_act)
        session_menu.addAction(load_act)

    # ------------------------------------------------------------------ #
    # Tabs                                                                 #
    # ------------------------------------------------------------------ #

    def _setup_tabs(self):
        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)
        self.tabs.addTab(self._build_device_tab(),      "Cadastro de Dispositivos")
        self.tabs.addTab(self._build_consumption_tab(), "Visualização de Consumo")
        self.tabs.addTab(self._build_efficiency_tab(),  "Análise de Eficiência")
        self.tabs.addTab(self._build_comparison_tab(),  "Comparação de Cenários")
        self.tabs.currentChanged.connect(self._on_tab_changed)

    # ------------------------------------------------------------------ #
    # Tab 1 — Cadastro de dispositivos                                    #
    # ------------------------------------------------------------------ #

    def _build_device_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(12, 12, 12, 12)

        # Scenario selector bar
        scenario_bar = QHBoxLayout()
        scenario_bar.addWidget(QLabel("Cenário:"))
        self.scenario_combo = QComboBox()
        self.scenario_combo.addItem("Principal")
        self.scenario_combo.currentIndexChanged.connect(self._on_scenario_changed)
        new_scenario_btn = QPushButton("+ Novo Cenário")
        new_scenario_btn.clicked.connect(self._new_scenario)
        scenario_bar.addWidget(self.scenario_combo)
        scenario_bar.addWidget(new_scenario_btn)
        scenario_bar.addStretch()

        # Device form — row 1: name / power / hours
        form1 = QHBoxLayout()
        self.name_input  = QLineEdit()
        self.name_input.setPlaceholderText("Nome (ex: Ar-condicionado)")
        self.power_input = QLineEdit()
        self.power_input.setPlaceholderText("Potência (W)")
        self.power_input.setValidator(QDoubleValidator(0, 99999, 2))
        self.hours_input = QLineEdit()
        self.hours_input.setPlaceholderText("Horas/dia (máx 24)")
        self.hours_input.setValidator(QDoubleValidator(0, 24, 2))
        form1.addWidget(QLabel("Nome:")); form1.addWidget(self.name_input)
        form1.addSpacing(8)
        form1.addWidget(QLabel("Potência (W):")); form1.addWidget(self.power_input)
        form1.addSpacing(8)
        form1.addWidget(QLabel("Horas/dia:")); form1.addWidget(self.hours_input)

        # Device form — row 2: cost / installments
        form2 = QHBoxLayout()
        self.cost_input = QLineEdit()
        self.cost_input.setPlaceholderText("Preço (R$)")
        self.cost_input.setValidator(QDoubleValidator(0, 999999, 2))
        self.inst_qty_input = QLineEdit()
        self.inst_qty_input.setPlaceholderText("Nº parcelas")
        self.inst_qty_input.setValidator(QDoubleValidator(0, 999, 0))
        self.inst_val_input = QLineEdit()
        self.inst_val_input.setPlaceholderText("Valor/parcela (R$)")
        self.inst_val_input.setValidator(QDoubleValidator(0, 99999, 2))
        add_btn = QPushButton("+ Adicionar")
        add_btn.setFixedWidth(110)
        add_btn.clicked.connect(self._add_device)
        form2.addWidget(QLabel("Preço (R$):")); form2.addWidget(self.cost_input)
        form2.addSpacing(8)
        form2.addWidget(QLabel("Parcelas:")); form2.addWidget(self.inst_qty_input)
        form2.addSpacing(8)
        form2.addWidget(QLabel("Valor/parc (R$):")); form2.addWidget(self.inst_val_input)
        form2.addSpacing(8)
        form2.addWidget(add_btn)

        # Device table: name | power_w | usage_hours | monthly_kwh | cost_price | [remove]
        self.device_table = QTableWidget(0, 6)
        self.device_table.setHorizontalHeaderLabels(
            ["Dispositivo", "Potência (W)", "Tempo (h/dia)",
             "Consumo (kWh/mês)", "Preço (R$)", ""]
        )
        self.device_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.device_table.setColumnWidth(5, 90)
        self.device_table.setEditTriggers(QTableWidget.EditTrigger.DoubleClicked)
        self.device_table.itemChanged.connect(self._on_device_edited)

        layout.addLayout(scenario_bar)
        layout.addLayout(form1)
        layout.addLayout(form2)
        layout.addWidget(self.device_table)
        return widget

    # ------------------------------------------------------------------ #
    # Tab 2 — Visualização de consumo                                     #
    # ------------------------------------------------------------------ #

    def _build_consumption_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(12, 12, 12, 12)

        cards = QHBoxLayout()
        cards.addWidget(self._make_card("c_total", "Consumo Total",  "0.00 kWh/mês"))
        cards.addWidget(self._make_card("c_cost",  "Custo Estimado", "R$ 0.00"))
        cards.addWidget(self._make_card("c_daily", "Média Diária",   "0.00 kWh/dia"))

        self.fig_consumption = Figure(figsize=(6, 3), tight_layout=True)
        self.canvas_consumption = FigureCanvasQTAgg(self.fig_consumption)

        self.consumption_table = QTableWidget(0, 6)
        self.consumption_table.setHorizontalHeaderLabels(
            ["Dispositivo", "Potência (W)", "Consumo (kWh/mês)",
             "Custo (R$/mês)", "% do Total", "Nível"]
        )
        self.consumption_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.consumption_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)

        layout.addLayout(cards)
        layout.addWidget(self.canvas_consumption)
        layout.addWidget(self.consumption_table)
        return widget

    # ------------------------------------------------------------------ #
    # Tab 3 — Análise de eficiência                                       #
    # ------------------------------------------------------------------ #

    def _build_efficiency_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(12, 12, 12, 12)

        cards = QHBoxLayout()
        cards.addWidget(self._make_card("e_current",   "Consumo Atual",         "0.00 kWh/mês"))
        cards.addWidget(self._make_card("e_optimized", "Consumo Otimizado",     "0.00 kWh/mês"))
        cards.addWidget(self._make_card("e_savings",   "Potencial de Economia", "0.00 kWh (0.0%)"))

        self.fig_efficiency = Figure(figsize=(6, 3), tight_layout=True)
        self.canvas_efficiency = FigureCanvasQTAgg(self.fig_efficiency)

        self.suggestions_table = QTableWidget(0, 3)
        self.suggestions_table.setHorizontalHeaderLabels(
            ["Sugestão", "Economia Estimada (kWh/mês)", "Impacto"]
        )
        self.suggestions_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.suggestions_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)

        layout.addLayout(cards)
        layout.addWidget(self.canvas_efficiency)
        layout.addWidget(self.suggestions_table)
        return widget

    # ------------------------------------------------------------------ #
    # Tab 4 — Comparação de cenários                                      #
    # ------------------------------------------------------------------ #

    def _build_comparison_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(12, 12, 12, 12)

        sel_row = QHBoxLayout()
        sel_row.addWidget(QLabel("Cenário base:"))
        self.cmp_combo1 = QComboBox()
        sel_row.addWidget(self.cmp_combo1)
        sel_row.addSpacing(12)
        sel_row.addWidget(QLabel("vs"))
        sel_row.addSpacing(12)
        sel_row.addWidget(QLabel("Cenário novo:"))
        self.cmp_combo2 = QComboBox()
        sel_row.addWidget(self.cmp_combo2)
        compare_btn = QPushButton("Comparar")
        compare_btn.setFixedWidth(100)
        compare_btn.clicked.connect(self._run_comparison)
        sel_row.addSpacing(12)
        sel_row.addWidget(compare_btn)
        sel_row.addStretch()
        self._sync_compare_combos()

        self.fig_cmp = Figure(figsize=(11, 4), tight_layout=True)
        self.canvas_cmp = FigureCanvasQTAgg(self.fig_cmp)

        self.cmp_info_label = QLabel("Selecione dois cenários e clique em Comparar.")
        self.cmp_info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        layout.addLayout(sel_row)
        layout.addWidget(self.canvas_cmp)
        layout.addWidget(self.cmp_info_label)
        return widget

    # ------------------------------------------------------------------ #
    # Helpers de UI                                                        #
    # ------------------------------------------------------------------ #

    def _make_card(self, key: str, title: str, initial: str) -> QFrame:
        frame = QFrame()
        frame.setFrameShape(QFrame.Shape.StyledPanel)
        frame.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        vbox = QVBoxLayout(frame)
        title_lbl = QLabel(title)
        title_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        value_lbl = QLabel(initial)
        value_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        vbox.addWidget(title_lbl)
        vbox.addWidget(value_lbl)
        self._card_labels[key] = value_lbl
        return frame

    def _set_card(self, key: str, text: str):
        self._card_labels[key].setText(text)

    def _classify(self, pct: float) -> str:
        if pct >= 30:
            return "Alto"
        if pct >= 15:
            return "Médio"
        return "Baixo"

    # ------------------------------------------------------------------ #
    # Gerenciamento de cenários                                            #
    # ------------------------------------------------------------------ #

    def _new_scenario(self):
        name, ok = QInputDialog.getText(self, "Novo Cenário", "Nome do cenário:")
        if ok and name.strip():
            s = Scenario(name.strip())
            self.scenarios.append(s)
            self.scenario_combo.addItem(name.strip())
            self.scenario_combo.setCurrentIndex(len(self.scenarios) - 1)
            self._sync_compare_combos()

    def _on_scenario_changed(self, index: int):
        if 0 <= index < len(self.scenarios):
            self.active_scenario = self.scenarios[index]
            self._refresh_device_table()

    def _sync_compare_combos(self):
        names = [s.name for s in self.scenarios]
        for combo in (self.cmp_combo1, self.cmp_combo2):
            current = combo.currentText()
            combo.blockSignals(True)
            combo.clear()
            combo.addItems(names)
            idx = combo.findText(current)
            combo.setCurrentIndex(max(0, idx))
            combo.blockSignals(False)
        if len(self.scenarios) >= 2:
            if self.cmp_combo2.currentIndex() == self.cmp_combo1.currentIndex():
                self.cmp_combo2.setCurrentIndex(1)

    # ------------------------------------------------------------------ #
    # Lógica — Tab 1                                                       #
    # ------------------------------------------------------------------ #

    def _add_device(self):
        data = self.get_device_data()
        if data is None:
            return

        installments = None
        if data["installments_qty"] > 0 and data["installment_value"] > 0:
            installments = InstallmentsDevices(data["installments_qty"], data["installment_value"])

        self.active_scenario.add_device(
            Device(data["name"], data["power_w"], data["usage_hours"],
                   data["cost_price"], installments)
        )
        self._refresh_device_table()
        for field in (self.name_input, self.power_input, self.hours_input,
                      self.cost_input, self.inst_qty_input, self.inst_val_input):
            field.clear()

    def _remove_device(self, name: str):
        self.active_scenario.remove_device(name)
        self._refresh_device_table()

    def _refresh_device_table(self):
        self.device_table.blockSignals(True)
        self.device_table.setRowCount(0)
        consumptions = self.calculator.calculate_all(self.active_scenario.devices)

        for i, device in enumerate(self.active_scenario.devices):
            row = self.device_table.rowCount()
            self.device_table.insertRow(row)
            self.device_table.setItem(row, 0, QTableWidgetItem(device.name))
            self.device_table.setItem(row, 1, QTableWidgetItem(str(device.power_w)))
            self.device_table.setItem(row, 2, QTableWidgetItem(str(device.usage_hours)))

            monthly = QTableWidgetItem(f"{consumptions[i]:.2f}")
            monthly.setFlags(monthly.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.device_table.setItem(row, 3, monthly)

            self.device_table.setItem(row, 4, QTableWidgetItem(f"{device.cost_price:.2f}"))

            btn = QPushButton("Remover")
            btn.clicked.connect(lambda _, n=device.name: self._remove_device(n))
            self.device_table.setCellWidget(row, 5, btn)

        self.device_table.blockSignals(False)

    def _on_device_edited(self, item: QTableWidgetItem):
        row = item.row()
        col = item.column()
        if row >= len(self.active_scenario.devices) or col not in (0, 1, 2, 4):
            return
        device = self.active_scenario.devices[row]
        try:
            if col == 0:
                device.name = item.text().strip()
            elif col == 1:
                device.power_w = float(item.text().replace(",", "."))
            elif col == 2:
                device.usage_hours = float(item.text().replace(",", "."))
            elif col == 4:
                device.cost_price = float(item.text().replace(",", "."))
        except ValueError:
            pass
        self._refresh_device_table()

    def _on_tab_changed(self, index: int):
        if index == 1:
            self._refresh_consumption_tab()
        elif index == 2:
            self._refresh_efficiency_tab()

    # ------------------------------------------------------------------ #
    # Lógica — Tab 2                                                       #
    # ------------------------------------------------------------------ #

    def _refresh_consumption_tab(self):
        if not self.active_scenario.devices:
            self._set_card("c_total", "0.00 kWh/mês")
            self._set_card("c_cost",  "R$ 0.00")
            self._set_card("c_daily", "0.00 kWh/dia")
            self.consumption_table.setRowCount(0)
            self.fig_consumption.clear()
            self.canvas_consumption.draw()
            return

        result = self.simulator.simulate(self.active_scenario)
        total  = result["total_monthly_kwh"]
        cost   = total * TARIFF
        daily  = total / 30

        self._set_card("c_total", f"{total:.2f} kWh/mês")
        self._set_card("c_cost",  f"R$ {cost:.2f}")
        self._set_card("c_daily", f"{daily:.2f} kWh/dia")

        self.fig_consumption.clear()
        ax = self.fig_consumption.add_subplot(111)
        names  = [d["name"] for d in result["devices"]]
        values = np.array([d["monthly_kwh"] for d in result["devices"]])
        bars = ax.bar(names, values, color="#4C72B0")
        ax.set_title(f"Consumo por Dispositivo — {self.active_scenario.name} (kWh/mês)")
        ax.set_ylabel("kWh/mês")
        ax.tick_params(axis="x", rotation=30)
        offset = float(values.max()) * 0.01 if len(values) else 0
        for bar, val in zip(bars, values):
            ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + offset,
                    f"{val:.2f}", ha="center", va="bottom", fontsize=8)
        self.fig_consumption.tight_layout()
        self.canvas_consumption.draw()

        power_map = {d.name: d.power_w for d in self.active_scenario.devices}
        self.consumption_table.setRowCount(0)
        for d in result["devices"]:
            row = self.consumption_table.rowCount()
            self.consumption_table.insertRow(row)
            pct   = (d["monthly_kwh"] / total * 100) if total > 0 else 0
            level = self._classify(pct)
            for col, val in enumerate([
                d["name"],
                f"{power_map.get(d['name'], 0):.0f}",
                f"{d['monthly_kwh']:.2f}",
                f"R$ {d['monthly_kwh'] * TARIFF:.2f}",
                f"{pct:.1f}%",
                level,
            ]):
                self.consumption_table.setItem(row, col, QTableWidgetItem(val))

    # ------------------------------------------------------------------ #
    # Lógica — Tab 3                                                       #
    # ------------------------------------------------------------------ #

    def _generate_optimized(self, result: dict):
        total = result["total_monthly_kwh"]
        suggestions = []
        optimized = Scenario("Otimizado")
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
            src     = next(dev for dev in self.active_scenario.devices if dev.name == name)
            reduction, action = reductions[level]
            new_hours   = src.usage_hours * (1 - reduction)
            opt_monthly = src.power_w * new_hours / 1000 * 30
            savings     = monthly - opt_monthly
            suggestions.append({"text": f"{action}: {name}", "savings": savings, "impact": level})
            optimized.add_device(Device(name, src.power_w, new_hours))
        return suggestions, optimized

    def _refresh_efficiency_tab(self):
        if not self.active_scenario.devices:
            self._set_card("e_current",   "0.00 kWh/mês")
            self._set_card("e_optimized", "0.00 kWh/mês")
            self._set_card("e_savings",   "0.00 kWh (0.0%)")
            self.suggestions_table.setRowCount(0)
            self.fig_efficiency.clear()
            self.canvas_efficiency.draw()
            return

        result = self.simulator.simulate(self.active_scenario)
        suggestions, optimized = self._generate_optimized(result)
        comparison = self.simulator.compare(self.active_scenario, optimized)

        total_current = comparison["scenario_1"]["total_monthly_kwh"]
        total_opt     = comparison["scenario_2"]["total_monthly_kwh"]
        savings_kwh   = comparison["difference_kwh"]
        savings_pct   = comparison["savings_percent"]

        self._set_card("e_current",   f"{total_current:.2f} kWh/mês")
        self._set_card("e_optimized", f"{total_opt:.2f} kWh/mês")
        self._set_card("e_savings",   f"{savings_kwh:.2f} kWh ({savings_pct:.1f}%)")

        self.fig_efficiency.clear()
        ax = self.fig_efficiency.add_subplot(111)
        names    = [d["name"] for d in result["devices"]]
        cur_vals = np.array([d["monthly_kwh"] for d in result["devices"]])
        opt_map  = {d.name: d.monthly_consumption() for d in optimized.devices}
        opt_vals = np.array([opt_map.get(n, 0) for n in names])
        x, w = np.arange(len(names)), 0.35
        ax.bar(x - w / 2, cur_vals, w, label="Atual",     color="#4C72B0")
        ax.bar(x + w / 2, opt_vals, w, label="Otimizado", color="#55A868")
        ax.set_xticks(x)
        ax.set_xticklabels(names, rotation=30, ha="right")
        ax.set_title("Atual vs. Otimizado (kWh/mês)")
        ax.set_ylabel("kWh/mês")
        ax.legend()
        self.fig_efficiency.tight_layout()
        self.canvas_efficiency.draw()

        self.suggestions_table.setRowCount(0)
        for s in suggestions:
            row = self.suggestions_table.rowCount()
            self.suggestions_table.insertRow(row)
            for col, val in enumerate([s["text"], f"{s['savings']:.2f}", s["impact"]]):
                self.suggestions_table.setItem(row, col, QTableWidgetItem(val))

    # ------------------------------------------------------------------ #
    # Lógica — Tab 4                                                       #
    # ------------------------------------------------------------------ #

    def _run_comparison(self):
        i1 = self.cmp_combo1.currentIndex()
        i2 = self.cmp_combo2.currentIndex()

        if i1 < 0 or i2 < 0 or i1 == i2:
            QMessageBox.warning(self, "Seleção inválida",
                                "Selecione dois cenários diferentes.")
            return

        s1 = self.scenarios[i1]
        s2 = self.scenarios[i2]

        if not s1.devices or not s2.devices:
            QMessageBox.warning(self, "Cenário vazio",
                                "Ambos os cenários precisam ter dispositivos.")
            return

        comparison  = self.simulator.compare(s1, s2)
        break_data  = self.simulator.break_even(s1, s2, TARIFF, BREAK_EVEN_MONTHS)

        self.fig_cmp.clear()
        ax_bar  = self.fig_cmp.add_subplot(1, 2, 1)
        ax_line = self.fig_cmp.add_subplot(1, 2, 2)

        # --- Gráfico de barras (consumo mensal) ---
        sim1 = comparison["scenario_1"]
        sim2 = comparison["scenario_2"]
        all_names = list(dict.fromkeys(
            [d["name"] for d in sim1["devices"]] +
            [d["name"] for d in sim2["devices"]]
        ))
        map1 = {d["name"]: d["monthly_kwh"] for d in sim1["devices"]}
        map2 = {d["name"]: d["monthly_kwh"] for d in sim2["devices"]}
        v1 = np.array([map1.get(n, 0) for n in all_names])
        v2 = np.array([map2.get(n, 0) for n in all_names])
        x, w = np.arange(len(all_names)), 0.35
        ax_bar.bar(x - w / 2, v1, w, label=s1.name, color="#4C72B0")
        ax_bar.bar(x + w / 2, v2, w, label=s2.name, color="#55A868")
        ax_bar.set_xticks(x)
        ax_bar.set_xticklabels(all_names, rotation=30, ha="right", fontsize=8)
        ax_bar.set_title("Consumo Mensal (kWh/mês)")
        ax_bar.set_ylabel("kWh/mês")
        ax_bar.legend(fontsize=8)

        # --- Gráfico de linha (custo acumulado + break-even) ---
        months = break_data["months"]
        cum1   = break_data["cumulative_s1"]
        cum2   = break_data["cumulative_s2"]
        bep    = break_data["break_even_month"]

        ax_line.plot(months, cum1, label=f"{s1.name} (base)",
                     color="#4C72B0", linewidth=2)
        ax_line.plot(months, cum2, label=f"{s2.name} (novo)",
                     color="#E88720", linewidth=2, linestyle="--")

        if bep:
            ax_line.axvline(bep, color="red", linestyle=":", linewidth=1.5)
            ax_line.annotate(
                f"Break-even\nMês {bep}",
                xy=(bep, cum2[bep - 1]),
                xytext=(bep + 2, cum2[bep - 1] * 0.92),
                fontsize=8, color="red",
                arrowprops=dict(arrowstyle="->", color="red"),
            )

        ax_line.set_title(f"Custo Acumulado em {BREAK_EVEN_MONTHS} meses (R$)")
        ax_line.set_xlabel("Meses")
        ax_line.set_ylabel("R$")
        ax_line.legend(fontsize=8)

        self.fig_cmp.tight_layout()
        self.canvas_cmp.draw()

        if bep:
            self.cmp_info_label.setText(
                f"Ponto de equilíbrio: mês {bep} — "
                f"a partir desse mês '{s2.name}' passa a ser mais barato no acumulado."
            )
        else:
            self.cmp_info_label.setText(
                f"'{s2.name}' não compensa em {BREAK_EVEN_MONTHS} meses "
                f"com as condições atuais (tarifa R$ {TARIFF:.2f}/kWh)."
            )

    # ------------------------------------------------------------------ #
    # InputPort                                                            #
    # ------------------------------------------------------------------ #

    def get_device_data(self) -> dict | None:
        name  = self.name_input.text().strip()
        power = self.power_input.text().strip().replace(",", ".")
        hours = self.hours_input.text().strip().replace(",", ".")

        if not name or not power or not hours:
            QMessageBox.warning(self, "Campos incompletos",
                                "Nome, Potência e Horas são obrigatórios.")
            return None
        try:
            power_f = float(power)
            hours_f = float(hours)
        except ValueError:
            QMessageBox.warning(self, "Valores inválidos",
                                "Potência e horas devem ser números.")
            return None
        if hours_f > 24:
            QMessageBox.warning(self, "Valor inválido",
                                "Horas de uso não pode ser maior que 24.")
            return None

        cost_f     = float(self.cost_input.text().replace(",", ".") or "0")
        inst_qty   = int(float(self.inst_qty_input.text().replace(",", ".") or "0"))
        inst_val_f = float(self.inst_val_input.text().replace(",", ".") or "0")

        return {
            "name":              name,
            "power_w":           power_f,
            "usage_hours":       hours_f,
            "cost_price":        cost_f,
            "installments_qty":  inst_qty,
            "installment_value": inst_val_f,
        }

    def get_scenario_name(self) -> str:
        return self.active_scenario.name

    # ------------------------------------------------------------------ #
    # Salvar / Carregar sessão                                             #
    # ------------------------------------------------------------------ #

    def _save_session(self):
        path, _ = QFileDialog.getSaveFileName(
            self, "Salvar sessão", "", "JSON (*.json);;CSV (*.csv)"
        )
        if not path:
            return
        try:
            self.csv_adapter.save(self.scenarios, path)
            QMessageBox.information(self, "Sessão salva", f"Salvo em:\n{path}")
        except Exception as e:
            QMessageBox.critical(self, "Erro ao salvar", str(e))

    def _load_session(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Carregar sessão", "", "JSON (*.json);;CSV (*.csv)"
        )
        if not path:
            return
        try:
            data = self.csv_adapter.load(path)
            if not data:
                return

            self.scenarios = []
            for s_data in data:
                s = Scenario(s_data["name"])
                for d in s_data["devices"]:
                    installments = None
                    qty = d.get("installments_qty", 0)
                    val = d.get("installment_value", 0.0)
                    if qty > 0 and val > 0:
                        installments = InstallmentsDevices(qty, val)
                    s.add_device(Device(
                        d["name"], d["power_w"], d["usage_hours"],
                        d.get("cost_price", 0.0), installments
                    ))
                self.scenarios.append(s)

            self.active_scenario = self.scenarios[0]

            self.scenario_combo.blockSignals(True)
            self.scenario_combo.clear()
            self.scenario_combo.addItems([s.name for s in self.scenarios])
            self.scenario_combo.setCurrentIndex(0)
            self.scenario_combo.blockSignals(False)

            self._refresh_device_table()
            self._sync_compare_combos()
            QMessageBox.information(self, "Sessão carregada",
                                    f"{len(self.scenarios)} cenário(s) restaurado(s).")
        except Exception as e:
            QMessageBox.critical(self, "Erro ao carregar", str(e))
