from PyQt6.QtWidgets import QMainWindow, QTabWidget, QFileDialog, QMessageBox
from PyQt6.QtGui import QAction

from device import Device
from scenario import Scenario
from simulator import ScenarioSimulator
from bills import InstallmentsDevices
from adapters.csv_adapter import CSVAdapter

from tabs.device_tab import DeviceTab
from tabs.consumption_tab import ConsumptionTab
from tabs.efficiency_tab import EfficiencyTab
from tabs.comparison_tab import ComparisonTab


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("SPARC — Sistema de Análise de Consumo")
        self.setMinimumSize(1024, 720)

        simulator    = ScenarioSimulator()
        self._csv    = CSVAdapter()

        self.device_tab      = DeviceTab()
        self.consumption_tab = ConsumptionTab(simulator)
        self.efficiency_tab  = EfficiencyTab(simulator)
        self.comparison_tab  = ComparisonTab(simulator)

        self._setup_tabs()
        self._setup_menu()

        # Keep comparison combos in sync when scenarios change
        self.device_tab.scenarios_updated.connect(
            lambda: self.comparison_tab.refresh_combos(self.device_tab.scenarios)
        )
        self.comparison_tab.refresh_combos(self.device_tab.scenarios)

    # ------------------------------------------------------------------ #
    # Setup                                                                #
    # ------------------------------------------------------------------ #

    def _setup_tabs(self):
        tabs = QTabWidget()
        self.setCentralWidget(tabs)
        tabs.addTab(self.device_tab,      "Cadastro de Dispositivos")
        tabs.addTab(self.consumption_tab, "Visualização de Consumo")
        tabs.addTab(self.efficiency_tab,  "Análise de Eficiência")
        tabs.addTab(self.comparison_tab,  "Comparação de Cenários")
        tabs.currentChanged.connect(self._on_tab_changed)

    def _setup_menu(self):
        session_menu = self.menuBar().addMenu("Sessão")
        save_act = QAction("Salvar sessão...", self)
        save_act.triggered.connect(self._save_session)
        load_act = QAction("Carregar sessão...", self)
        load_act.triggered.connect(self._load_session)
        session_menu.addAction(save_act)
        session_menu.addAction(load_act)

    def _on_tab_changed(self, index: int):
        scenario = self.device_tab.active_scenario
        if index == 1:
            self.consumption_tab.refresh(scenario)
        elif index == 2:
            self.efficiency_tab.refresh(scenario)
        elif index == 3:
            self.comparison_tab.refresh_combos(self.device_tab.scenarios)

    # ------------------------------------------------------------------ #
    # Session save / load                                                  #
    # ------------------------------------------------------------------ #

    def _save_session(self):
        path, _ = QFileDialog.getSaveFileName(
            self, "Salvar sessão", "", "JSON (*.json);;CSV (*.csv)"
        )
        if not path:
            return
        try:
            self._csv.save(self.device_tab.scenarios, path)
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
            data = self._csv.load(path)
            if not data:
                return
            scenarios = []
            for s_data in data:
                s = Scenario(s_data["name"])
                for d in s_data["devices"]:
                    qty = d.get("installments_qty", 0)
                    val = d.get("installment_value", 0.0)
                    installments = InstallmentsDevices(qty, val) if qty > 0 else None
                    s.add_device(Device(
                        d["name"], d["power_w"], d["usage_hours"],
                        d.get("cost_price", 0.0), installments
                    ))
                scenarios.append(s)
            self.device_tab.load_scenarios(scenarios)
            QMessageBox.information(self, "Sessão carregada",
                                    f"{len(scenarios)} cenário(s) restaurado(s).")
        except Exception as e:
            QMessageBox.critical(self, "Erro ao carregar", str(e))
