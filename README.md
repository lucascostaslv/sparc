# PROJETO SPARC

## Dependencias

É necessário ter o python na versão 3.14 para rodar o projeto.

### Bibliotecas

numpy 
pandas
matplotlib
PyQt6

#### No windows : pip install <nome_da_biblioteca>
#### Baseado em Unix: pip3 install <nome_da_biblioteca> --user
(caso não tenha pip no linux ou mac) : sudo apt install python3-<<nome_da_biblioteca>>

## Rodar
Basta usar o comando: **python3 sparc-ui/main.py** ou **python sparc-ui/main.py**

---

## Como usar

### Aba 1 — Cadastro de Dispositivos
Aqui você cadastra os dispositivos elétricos que quer analisar. Preenche o nome, a potência em Watts e quantas horas por dia o aparelho fica ligado. Se quiser simular a compra de um aparelho novo, você pode informar também o preço e o parcelamento.

Você pode ter mais de um cenário, por exemplo "Casa Atual" e "Com Ar Inverter". Basta clicar em **+ Novo Cenário** e trocar pelo dropdown.

Os dispositivos aparecem na tabela abaixo e podem ser editados com duplo clique ou removidos pelo botão da linha.

### Aba 2 — Visualização de Consumo
Mostra o consumo do cenário que está selecionado na Aba 1. Tem três cards no topo com o consumo total em kWh/mês, o custo estimado em R$ e a média diária.

Abaixo tem um gráfico de barras com o consumo de cada dispositivo e uma tabela detalhada mostrando o percentual que cada um representa no total e o nível de consumo (Alto, Médio ou Baixo).

### Aba 3 — Análise de Eficiência
O sistema gera automaticamente sugestões de otimização para o cenário ativo. Dispositivos classificados como Alto recebem sugestão de substituição, os demais recebem sugestão de redução de uso.

Mostra o consumo atual vs o consumo se as sugestões fossem aplicadas, o potencial de economia em kWh e em percentual, e uma tabela com cada sugestão e o impacto estimado.

### Aba 4 — Comparação de Cenários
Aqui é onde você compara dois cenários que criou na Aba 1. Seleciona o cenário base e o cenário novo nos dropdowns e clica em **Comparar**.

Aparecem dois gráficos lado a lado:
- O da esquerda compara o consumo mensal de cada dispositivo entre os dois cenários
- O da direita mostra o custo acumulado ao longo de 60 meses, considerando a conta de luz e as parcelas do cenário novo

Se o investimento compensar dentro do prazo, aparece uma linha vermelha marcando o mês exato do ponto de equilíbrio (break-even).

### Salvar e Carregar
No menu **Sessão** você pode salvar todos os cenários em JSON ou CSV e carregar depois para continuar de onde parou.
