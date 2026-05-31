from datetime import datetime

DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

class KWHCost:
    value: float #Custo local, tem que pesqiusar

    def __init__(self, value):
        self.value = value

class Bill:
    consumption_total: float #Está em KWh
    date: datetime

    def __init__(self, consumption_total, date: str):
        self.consumption_total = consumption_total
        self.date = datetime.strptime(date, DATE_FORMAT)

    def getBillCost(self, costLocal: KWHCost) -> float:
        return self.consumption_total * costLocal.value


class HistoricalBills:
    bills: list[Bill]

    def __init__(self):
        self.bills = []

    def addBill(self, bill):
        self.bills.append(bill)
    
    def removeBill(self, bill):
        self.bills = [b for b in self.bills if b != bill]


class InstallmentsDevices:
    qdt_installments: float
    value_installment: float

    def __init__(self, qtd_installments, value_installment):
        self.qdt_installments = qtd_installments
        self.value_installment = value_installment
