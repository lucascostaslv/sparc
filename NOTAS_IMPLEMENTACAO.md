# Notas de Implementação — sparc-core

Coisas para não esquecer enquanto você codifica o core.

---

## device.py

- `daily_consumption()` usa a fórmula: `power_w * usage_hours / 1000`
- `monthly_consumption()` é só `daily * 30` — nada mais

---

## calculator.py

- `calculate(device)` deve retornar o consumo **mensal** (não diário)
- `calculate_all(devices)` deve manter a **mesma ordem** da lista recebida —
  o ChartAdapter depende disso para parear nome com valor no gráfico

---

## scenario.py

- `remove_device(name)` deve ser silencioso se o nome não existir (não levanta exceção)
- `total_consumption()` soma o `monthly_consumption()` de cada device —
  use o método do Device, não recalcule na mão

---

## simulator.py

- `simulate()` retorna um dict com este formato **exato** — o ChartAdapter e o
  OutputPort dependem dessa estrutura:

```python
{
    "scenario": str,
    "devices": [
        {
            "name": str,
            "daily_kwh": float,
            "monthly_kwh": float,
        }
    ],
    "total_monthly_kwh": float
}
```

- `compare()` retorna:

```python
{
    "scenario_1": dict,      # resultado de simulate(s1)
    "scenario_2": dict,      # resultado de simulate(s2)
    "difference_kwh": float, # s1.total - s2.total
    "savings_percent": float # ((s1.total - s2.total) / s1.total) * 100
}
```

- `savings_percent` assume que s1 é o cenário atual e s2 é o otimizado.
  Se s1.total for 0, retorne 0.0 para evitar divisão por zero.

---

## Contrato com o CSVAdapter

- `CSVAdapter.load()` devolve **dicts puros**, não objetos `Device`/`Scenario`.
- Quem chamar `load()` é responsável por reconstruir os objetos:

```python
data = csv_adapter.load("sessao.json")
for s in data:
    scenario = Scenario(s["name"])
    for d in s["devices"]:
        scenario.add_device(Device(d["name"], d["power_w"], d["usage_hours"]))
```

- `CSVAdapter.save()` espera objetos com `.name`, `.devices`, e cada device
  com `.name`, `.power_w`, `.usage_hours` — ou seja, suas classes precisam
  ter exatamente esses atributos.

---

## Precisão numérica (RNF)

- Arredonde para **2 casas decimais** ao exibir, mas **não arredonde internamente**.
  Deixe o arredondamento para a camada de apresentação (UI).
