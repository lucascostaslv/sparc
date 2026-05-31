from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QComboBox,
    QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox, QInputDialog,
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QDoubleValidator

from device import Device
from scenario import Scenario
from calculator import EnergyCalculator
from bills import InstallmentsDevices


class DeviceTab(QWidget):
    scenarios_updated = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.scenarios: list[Scenario] = [Scenario("Principal")]
        self.active_scenario: Scenario = self.scenarios[0]
        self.calculator = EnergyCalculator()
        self._build_ui()

    # ------------------------------------------------------------------ #
    # Build UI                                                             #
    # ------------------------------------------------------------------ #

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)

        # Scenario bar
        scenario_bar = QHBoxLayout()
        scenario_bar.addWidget(QLabel("Cenário:"))
        self.scenario_combo = QComboBox()
        self.scenario_combo.addItem("Principal")
        self.scenario_combo.currentIndexChanged.connect(self._on_scenario_changed)
        new_btn = QPushButton("+ Novo Cenário")
        new_btn.clicked.connect(self._new_scenario)
        scenario_bar.addWidget(self.scenario_combo)
        scenario_bar.addWidget(new_btn)
        scenario_bar.addStretch()

        # Form row 1: name / power / hours
        form1 = QHBoxLayout()
        self.name_input  = QLineEdit(); self.name_input.setPlaceholderText("Nome (ex: Ar-condicionado)")
        self.power_input = QLineEdit(); self.power_input.setPlaceholderText("Potência (W)")
        self.power_input.setValidator(QDoubleValidator(0, 99999, 2))
        self.hours_input = QLineEdit(); self.hours_input.setPlaceholderText("Horas/dia (máx 24)")
        self.hours_input.setValidator(QDoubleValidator(0, 24, 2))
        form1.addWidget(QLabel("Nome:")); form1.addWidget(self.name_input)
        form1.addSpacing(8)
        form1.addWidget(QLabel("Potência (W):")); form1.addWidget(self.power_input)
        form1.addSpacing(8)
        form1.addWidget(QLabel("Horas/dia:")); form1.addWidget(self.hours_input)

        # Form row 2: cost / installments
        form2 = QHBoxLayout()
        self.cost_input     = QLineEdit(); self.cost_input.setPlaceholderText("Preço (R$)")
        self.cost_input.setValidator(QDoubleValidator(0, 999999, 2))
        self.inst_qty_input = QLineEdit(); self.inst_qty_input.setPlaceholderText("Nº parcelas")
        self.inst_qty_input.setValidator(QDoubleValidator(0, 999, 0))
        self.inst_val_input = QLineEdit(); self.inst_val_input.setPlaceholderText("Valor/parcela (R$)")
        self.inst_val_input.setValidator(QDoubleValidator(0, 99999, 2))
        add_btn = QPushButton("+ Adicionar"); add_btn.setFixedWidth(110)
        add_btn.clicked.connect(self._add_device)
        form2.addWidget(QLabel("Preço (R$):")); form2.addWidget(self.cost_input)
        form2.addSpacing(8)
        form2.addWidget(QLabel("Parcelas:")); form2.addWidget(self.inst_qty_input)
        form2.addSpacing(8)
        form2.addWidget(QLabel("Valor/parc (R$):")); form2.addWidget(self.inst_val_input)
        form2.addSpacing(8)
        form2.addWidget(add_btn)

        # Table
        self.table = QTableWidget(0, 6)
        self.table.setHorizontalHeaderLabels(
            ["Dispositivo", "Potência (W)", "Tempo (h/dia)",
             "Consumo (kWh/mês)", "Preço (R$)", ""]
        )
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.table.setColumnWidth(5, 90)
        self.table.setEditTriggers(QTableWidget.EditTrigger.DoubleClicked)
        self.table.itemChanged.connect(self._on_device_edited)

        layout.addLayout(scenario_bar)
        layout.addLayout(form1)
        layout.addLayout(form2)
        layout.addWidget(self.table)

    # ------------------------------------------------------------------ #
    # Scenario management                                                  #
    # ------------------------------------------------------------------ #

    def _new_scenario(self):
        name, ok = QInputDialog.getText(self, "Novo Cenário", "Nome do cenário:")
        if ok and name.strip():
            s = Scenario(name.strip())
            self.scenarios.append(s)
            self.scenario_combo.addItem(name.strip())
            self.scenario_combo.setCurrentIndex(len(self.scenarios) - 1)
            self.scenarios_updated.emit()

    def _on_scenario_changed(self, index: int):
        if 0 <= index < len(self.scenarios):
            self.active_scenario = self.scenarios[index]
            self._refresh_table()

    def load_scenarios(self, scenarios: list[Scenario]):
        self.scenarios = scenarios
        self.active_scenario = scenarios[0]
        self.scenario_combo.blockSignals(True)
        self.scenario_combo.clear()
        self.scenario_combo.addItems([s.name for s in scenarios])
        self.scenario_combo.setCurrentIndex(0)
        self.scenario_combo.blockSignals(False)
        self._refresh_table()
        self.scenarios_updated.emit()

    # ------------------------------------------------------------------ #
    # Device logic                                                         #
    # ------------------------------------------------------------------ #

    def _add_device(self):
        data = self._parse_form()
        if data is None:
            return
        installments = None
        if data["installments_qty"] > 0:
            installments = InstallmentsDevices(data["installments_qty"], data["installment_value"])
        self.active_scenario.add_device(
            Device(data["name"], data["power_w"], data["usage_hours"],
                   data["cost_price"], installments)
        )
        self._refresh_table()
        for f in (self.name_input, self.power_input, self.hours_input,
                  self.cost_input, self.inst_qty_input, self.inst_val_input):
            f.clear()

    def _remove_device(self, name: str):
        self.active_scenario.remove_device(name)
        self._refresh_table()

    def _refresh_table(self):
        self.table.blockSignals(True)
        self.table.setRowCount(0)
        consumptions = self.calculator.calculate_all(self.active_scenario.devices)
        for i, device in enumerate(self.active_scenario.devices):
            row = self.table.rowCount()
            self.table.insertRow(row)
            self.table.setItem(row, 0, QTableWidgetItem(device.name))
            self.table.setItem(row, 1, QTableWidgetItem(str(device.power_w)))
            self.table.setItem(row, 2, QTableWidgetItem(str(device.usage_hours)))
            monthly = QTableWidgetItem(f"{consumptions[i]:.2f}")
            monthly.setFlags(monthly.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.table.setItem(row, 3, monthly)
            self.table.setItem(row, 4, QTableWidgetItem(f"{device.cost_price:.2f}"))
            btn = QPushButton("Remover")
            btn.clicked.connect(lambda _, n=device.name: self._remove_device(n))
            self.table.setCellWidget(row, 5, btn)
        self.table.blockSignals(False)

    def _on_device_edited(self, item: QTableWidgetItem):
        row, col = item.row(), item.column()
        if row >= len(self.active_scenario.devices) or col not in (0, 1, 2, 4):
            return
        device = self.active_scenario.devices[row]
        try:
            if col == 0:   device.name        = item.text().strip()
            elif col == 1: device.power_w     = float(item.text().replace(",", "."))
            elif col == 2: device.usage_hours = float(item.text().replace(",", "."))
            elif col == 4: device.cost_price  = float(item.text().replace(",", "."))
        except ValueError:
            pass
        self._refresh_table()

    # ------------------------------------------------------------------ #
    # Form parsing                                                         #
    # ------------------------------------------------------------------ #

    def _parse_form(self) -> dict | None:
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
        return {
            "name":              name,
            "power_w":           power_f,
            "usage_hours":       hours_f,
            "cost_price":        float(self.cost_input.text().replace(",", ".") or "0"),
            "installments_qty":  int(float(self.inst_qty_input.text().replace(",", ".") or "0")),
            "installment_value": float(self.inst_val_input.text().replace(",", ".") or "0"),
        }
