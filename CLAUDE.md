# SPARC — System for Power Analysis, Reporting & Control

Sistema desktop para simulação e análise de consumo energético residencial/comercial.

**Prazo:** 2 dias a partir de 30/05/2026.
**Equipe:** Manoel Pedro, Lucas Vasconcellos, Otávio Augusto, Luís Fernando e Lucas Costa.

---

## Estrutura de Módulos

```
Sparc/
├── CLAUDE.md
├── requirements.txt
├── sparc-core/          # domínio + ports + adapters de dados
│   ├── core/
│   │   ├── device.py
│   │   ├── calculator.py
│   │   ├── scenario.py
│   │   └── simulator.py
│   ├── ports/
│   │   ├── input_port.py
│   │   ├── output_port.py
│   │   └── data_port.py
│   └── adapters/
│       ├── chart_adapter.py
│       └── csv_adapter.py
└── sparc-ui/            # GUI PyQt + gui_adapter
    ├── adapters/
    │   └── gui_adapter.py
    └── main.py
```

**Decisão de arquitetura:** `sparc-core` é 100% independente de interface gráfica — pode ser testado sem abrir janela. `sparc-ui` consome os adapters do core via ports.

---

## Arquitetura — Hexagonal Simplificada

Três camadas:
- **Core:** lógica de negócio pura, sem dependências externas
- **Ports:** interfaces/contratos que desacoplam core dos adapters
- **Adapters:** implementações concretas (GUI, gráficos, persistência)

### Entidades do Core

**Device**
- `name: str`, `power_w: float`, `usage_hours: float`
- `daily_consumption() -> float` → `power_w * usage_hours / 1000`
- `monthly_consumption() -> float` → `daily * 30`

**EnergyCalculator** (extends Device)
- `calculate(device) -> float`
- `calculate_all(devices) -> list`

**Scenario**
- `name: str`, `devices: list[Device]`
- `total_consumption() -> float`
- `add_device(device)`, `remove_device(name)`

**ScenarioSimulator** (extends Scenario)
- `scenarios: list`
- `simulate(scenario) -> dict`
- `compare(s1, s2) -> dict`

### Ports

| Port | Métodos |
|------|---------|
| `InputPort` | `get_device_data() -> Device` |
| `OutputPort` | `display_results(data: dict)` |
| `DataPort` | `save(scenarios)`, `load() -> list` |

### Adapters

| Adapter | Implementa | Tecnologia |
|---------|-----------|------------|
| `GUIAdapter` (sparc-ui) | `InputPort` | PyQt |
| `ChartAdapter` | `OutputPort` | Matplotlib |
| `CSVAdapter` | `DataPort` | CSV / JSON |

---

## Requisitos Funcionais

| ID | Descrição |
|----|-----------|
| RF01 | Cadastro de dispositivos (nome, potência W, horas/dia) |
| RF02 | Edição de dispositivos |
| RF03 | Remoção de dispositivos |
| RF04 | Cálculo de consumo individual (kWh/dia e kWh/mês) |
| RF05 | Cálculo de consumo total do ambiente |
| RF06 | Simulação e comparação de cenários |
| RF07 | Gráficos de consumo por dispositivo |
| RF08 | Análise de eficiência com sugestões de otimização |
| RF09 | Custo estimado em R$ com tarifa configurável (padrão R$ 0,60/kWh) |
| RF10 | Classificação por nível: Alto / Médio / Baixo |
| RF11 | Salvar sessão em CSV ou JSON |
| RF12 | Carregar sessão de CSV ou JSON |

---

## Interface — 3 Abas

**Aba 1 — Cadastro de Dispositivos**
- Campos: Nome, Potência (W), Tempo de uso (h/dia) + botão Adicionar
- Tabela: Dispositivo | Potência | Tempo | Consumo (kWh/mês) | [Remover]

**Aba 2 — Visualização de Consumo**
- Cards: Consumo Total (kWh/mês), Custo Estimado (R$), Média Diária
- Gráfico de barras: consumo por dispositivo
- Tabela: Dispositivo | Potência | Consumo | Custo | % do Total | Nível

**Aba 3 — Análise de Eficiência**
- Cards: Consumo Atual, Consumo Otimizado, Potencial de Economia (kWh e %)
- Gráfico de barras duplas: Atual vs. Otimizado por dispositivo
- Tabela de sugestões com economia estimada e impacto

---

## Requisitos Não Funcionais

- Cálculos em < 200 ms para até 50 dispositivos
- Interface atualizada em < 1 s após alteração
- Todas as funcionalidades em ≤ 3 cliques da tela inicial
- Precisão: erro máximo de 0,01 kWh por dispositivo, 2 casas decimais
- Sem coleta ou transmissão de dados pessoais

---

## Stack Tecnológica

- **PyQt** — interface gráfica desktop
- **Matplotlib** — gráficos
- **NumPy** — cálculos numéricos
- **Pandas** — manipulação de dados tabulares

---

## Fora do Escopo

- Tarifas dinâmicas de energia
- Perdas elétricas reais na instalação
- Integração automática com medidores ou IoT
