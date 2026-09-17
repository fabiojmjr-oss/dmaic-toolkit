# `dmaic.improve` — did it happen, was it yours, and is it cash?

*[Português](#dmaicimprove--aconteceu-foi-seu-e-é-caixa)*

## The business problem

A project closes. The months after are 10.06 BRL per order cheaper than the months before, the
arithmetic is right, and the charter books it. The project delivered **5.00**.

The other 5.06 was a trend that was already running, and the untreated sites got it too. Nothing in
a before-and-after number distinguishes the two, and no amount of extra data narrows the difference
away: the trend is *inside* the number.

## The decision it enables

1. **How much of this improvement is the project's?** Which needs somebody the project did not
   touch, and nothing else.
2. **Was any of it an artefact of how the sites were chosen?** Charters are written on the worst
   performers, and the worst performer of a period is partly a bad site and partly a bad period.
3. **How much of the saving is money?** A modelled unit cost becomes cash only where the cost was
   avoidable. The rest is capacity — real, useful, and not in a bank account.

## Usage

```python
from dmaic.improve import BenefitCase, before_after, difference_in_differences

before_after(panel, split=12).effect  # -10.0637, with the trend inside it
did = difference_in_differences(panel, split=12)
did.effect, did.attributable  # -4.2241, True
did.comparison.confidence_interval  # (-5.2545, -3.1938)

case = BenefitCase(
    effect=did.effect,
    units_per_period=60_000,
    periods=12,
    variable_share=0.35,
    project_cost=250_000,
)
case.gross, case.cash, case.net  # gross, the part that is cash, and net of cost
```

## Result: three estimates of one effect

Twenty sites over twenty-four months, five improved from month thirteen. The generator declares
the effect it applied, **−5.00 per order**, and the trend that was already running, **−0.40 per
period** — which moves the measurand −4.80 over the twelve periods after the split, in treated and
untreated sites alike.

| Basis | Estimate | Comparison sites | Attributable | Times the truth |
| --- | --- | --- | --- | --- |
| Before and after | **−10.0637** | 0 | no | **2.01×** |
| Difference in differences | −4.2241 | 15 | yes | 0.84× |
| The truth | −5.0000 | — | — | 1.00× |

**The project reports twice what it delivered, and the surplus is the calendar.** −10.0637 against
a truth of −5.00, with the trend accounting for almost exactly the difference. A project measured
this way is not imprecise about its benefit; it is systematically wrong in one direction, and the
direction is always flattering.

**A comparison group fixes it without modelling anything.** The difference in differences subtracts
the change in the fifteen untreated sites from the change in the five treated ones, and whatever
the trend was, it leaves. The estimate lands at −4.2241 with an interval of **−5.2545 to −3.1938**,
which contains the truth: it is off by chance rather than by construction, and the interval says by
how much. That is a different kind of wrong from the before-and-after number, and the only kind
more data fixes.

The test behind it is Welch's on **site-level** changes — one observation per site, twenty in
total. A panel of twenty sites over twenty-four months is not four hundred and eighty independent
observations of a change, and treating it as such is how a difference in differences arrives at a
p-value three orders of magnitude too small.

## Result: what a project shows when it does nothing at all

No effect in any row below, and no trend either — the trend is held at zero on purpose so the two
errors are priced one at a time rather than confounded. The only thing happening is the choice of
which sites to charter, and how long a baseline that choice was made on.

| Baseline periods | Worst performers selected | Randomly selected |
| --- | --- | --- |
| 1 | **−4.3401** | −0.0524 |
| 3 | −1.6997 | −0.0262 |
| 6 | −0.8365 | −0.0063 |
| 12 | −0.4562 | +0.0005 |
| 24 | −0.2294 | −0.0022 |

**Chartering on a single bad month manufactures −4.34 out of nothing**, which is 87% of a real
five-unit improvement, in sites where nothing whatever was done. Random selection returns zero in
every row, which is the control: the artefact lives in the selection rule and not in the
arithmetic.

**And the remedy is free.** Twelve periods of baseline bring the artefact to −0.4562 and
twenty-four to −0.2294. Selecting a project on a year of data rather than a month costs nothing but
patience, and it is the difference between an artefact the size of the effect and an artefact a
twentieth of it.

## Result: and then the money

60,000 orders per period across the treated sites, twelve periods, and 35% of the unit cost
avoidable as cash within the horizon. The project cost 250,000 to run.

| Basis | Effect | Gross | Cash | Capacity | Net | Payback (periods) |
| --- | --- | --- | --- | --- | --- | --- |
| Booked on before and after | −10.06 | **7,245,895** | 2,536,063 | 4,709,832 | 2,286,063 | 1.18 |
| Difference in differences | −4.22 | 3,041,368 | 1,064,479 | 1,976,889 | 814,479 | 2.82 |
| The truth | −5.00 | 3,600,000 | **1,260,000** | 2,340,000 | 1,010,000 | 2.38 |

**The charter books 7,245,895 and the project produced 1,260,000 of cash — 5.75×.** And that gap
is not a mystery, it is a product: **2.01× for attribution and 2.86× for the share that is cash
rather than capacity**, and 2.01 × 2.86 = 5.75 exactly. Two factors, neither of them written down
anywhere in the project's documentation, multiplying.

`BenefitCase` therefore reports gross and cash as separate figures and declines to add them up. A
project that books capacity as cash is not wrong about the process — the capacity is real — it is
wrong about the bank account, and the two errors get found at different times by different people.

## Assumptions and limitations

- **A comparison group has to be comparable.** The difference in differences removes any trend
  *common* to both groups and nothing else. Where the treated sites are on a different trajectory
  for their own reasons — newer equipment, a different mix, the reason they were chosen — the
  subtraction removes the wrong amount, and this module cannot tell you that it happened. Parallel
  trends before the split is the assumption, and it is checkable from the same panel; checking it
  is not implemented here.
- **The treated sites in the panel are chosen at random**, which is why the true effect is
  recoverable at all. Real charters select on performance, which is exactly the case the
  regression-to-the-mean simulation prices — separately, and with no trend, so the two errors do
  not hide inside one figure.
- **Twenty sites is a small sample of sites**, and the interval says so: ±1 on an effect of 5. The
  unit of analysis being the site rather than the site-period is what makes that honest, and it
  is also what makes the study small. More months do not help; more sites do.
- **One split, one direction.** No staggered adoption, where sites start at different times, and
  no allowance for an effect that grows or decays after the change. Both are ordinary in practice
  and both need a different estimator than a two-by-two difference.
- **The variable share is an input, not a finding.** 35% is a declared parameter here. In a real
  case it is an argument with a controller, it is the single most consequential number in the
  benefit case, and no amount of process data settles it.
- **Nothing here discounts.** A saving in period twelve is added to a saving in period one at face
  value. Over twelve periods that is a small error; over a five-year claim it is not.
- **A payback period is not a return.** It ignores everything after it, including whether the gain
  holds — which is the Control phase's question and
  [`dmaic.control`](../control/README.md)'s subject, not this module's.

---

# `dmaic.improve` — aconteceu, foi seu, e é caixa?

*[English](#dmaicimprove--did-it-happen-was-it-yours-and-is-it-cash)*

## O problema de negócio

Um projeto encerra. Os meses depois estão 10,06 BRL por pedido mais baratos que os meses antes, a
aritmética está certa, e o charter contabiliza. O projeto entregou **5,00**.

Os outros 5,06 eram uma tendência que já estava correndo, e os sites não tratados também a
pegaram. Nada num número antes-e-depois distingue os dois, e nenhuma quantidade extra de dado
elimina a diferença: a tendência está *dentro* do número.

## A decisão que ele habilita

1. **Quanto desta melhoria é do projeto?** O que exige alguém que o projeto não tocou, e mais nada.
2. **Alguma parte foi artefato de como os sites foram escolhidos?** Charters são escritos sobre os
   piores desempenhos, e o pior desempenho de um período é em parte um site ruim e em parte um
   período ruim.
3. **Quanto da economia é dinheiro?** Um custo unitário modelado vira caixa só onde o custo era
   evitável. O resto é capacidade — real, útil, e fora da conta bancária.

## Uso

```python
from dmaic.improve import BenefitCase, before_after, difference_in_differences

before_after(painel, split=12).effect  # -10,0637, com a tendência dentro
did = difference_in_differences(painel, split=12)
did.effect, did.attributable  # -4,2241, True
did.comparison.confidence_interval  # (-5,2545, -3,1938)

caso = BenefitCase(
    effect=did.effect,
    units_per_period=60_000,
    periods=12,
    variable_share=0.35,
    project_cost=250_000,
)
caso.gross, caso.cash, caso.net  # bruto, a parte que é caixa, e líquido do custo
```

## Resultado: três estimativas de um efeito

Vinte sites ao longo de vinte e quatro meses, cinco melhorados a partir do mês treze. O gerador
declara o efeito que aplicou, **−5,00 por pedido**, e a tendência que já estava correndo, **−0,40
por período** — que move o mensurando −4,80 nos doze períodos após o corte, em sites tratados e não
tratados igualmente.

| Base | Estimativa | Sites de comparação | Atribuível | Vezes a verdade |
| --- | --- | --- | --- | --- |
| Antes e depois | **−10,0637** | 0 | não | **2,01×** |
| Diferença em diferenças | −4,2241 | 15 | sim | 0,84× |
| A verdade | −5,0000 | — | — | 1,00× |

**O projeto reporta o dobro do que entregou, e o excedente é o calendário.** −10,0637 contra uma
verdade de −5,00, com a tendência respondendo por quase exatamente a diferença. Um projeto medido
assim não é impreciso sobre o benefício dele; é sistematicamente errado numa direção, e a direção é
sempre lisonjeira.

**Um grupo de comparação resolve sem modelar nada.** A diferença em diferenças subtrai a mudança
dos quinze sites não tratados da mudança dos cinco tratados, e qualquer que fosse a tendência, ela
sai. A estimativa fica em −4,2241 com intervalo de **−5,2545 a −3,1938**, que contém a verdade:
está errada por azar e não por construção, e o intervalo diz por quanto. É um tipo diferente de
erro do número antes-e-depois, e o único tipo que mais dado corrige.

O teste por trás é o de Welch sobre as mudanças **por site** — uma observação por site, vinte no
total. Um painel de vinte sites ao longo de vinte e quatro meses não é quatrocentas e oitenta
observações independentes de uma mudança, e tratá-lo assim é como uma diferença em diferenças chega
a um p-valor três ordens de grandeza pequeno demais.

## Resultado: o que um projeto mostra quando não faz nada

Sem efeito em nenhuma linha abaixo, e sem tendência também — a tendência é mantida em zero de
propósito, para que os dois erros sejam precificados um por vez em vez de confundidos. A única
coisa acontecendo é a escolha de quais sites entram no charter, e sobre quantos períodos de
histórico essa escolha foi feita.

| Períodos de histórico | Piores desempenhos selecionados | Selecionados ao acaso |
| --- | --- | --- |
| 1 | **−4,3401** | −0,0524 |
| 3 | −1,6997 | −0,0262 |
| 6 | −0,8365 | −0,0063 |
| 12 | −0,4562 | +0,0005 |
| 24 | −0,2294 | −0,0022 |

**Abrir projeto sobre um único mês ruim fabrica −4,34 do nada**, que é 87% de uma melhoria real de
cinco unidades, em sites onde absolutamente nada foi feito. Seleção aleatória devolve zero em toda
linha, e essa é a verificação de controle: o artefato mora na regra de seleção e não na aritmética.

**E o remédio é de graça.** Doze períodos de histórico levam o artefato a −0,4562 e vinte e quatro
a −0,2294. Selecionar um projeto sobre um ano de dado em vez de um mês não custa nada além de
paciência, e é a diferença entre um artefato do tamanho do efeito e um artefato de um vigésimo
dele.

## Resultado: e então o dinheiro

60.000 pedidos por período nos sites tratados, doze períodos, e 35% do custo unitário evitável como
caixa dentro do horizonte. O projeto custou 250.000 para rodar.

| Base | Efeito | Bruto | Caixa | Capacidade | Líquido | Payback (períodos) |
| --- | --- | --- | --- | --- | --- | --- |
| Contabilizado no antes e depois | −10,06 | **7.245.895** | 2.536.063 | 4.709.832 | 2.286.063 | 1,18 |
| Diferença em diferenças | −4,22 | 3.041.368 | 1.064.479 | 1.976.889 | 814.479 | 2,82 |
| A verdade | −5,00 | 3.600.000 | **1.260.000** | 2.340.000 | 1.010.000 | 2,38 |

**O charter contabiliza 7.245.895 e o projeto produziu 1.260.000 de caixa — 5,75×.** E esse
descasamento não é um mistério, é um produto: **2,01× de atribuição e 2,86× da parcela que é caixa
e não capacidade**, e 2,01 × 2,86 = 5,75 exatamente. Dois fatores, nenhum deles escrito em lugar
algum da documentação do projeto, se multiplicando.

Por isso o `BenefitCase` reporta bruto e caixa como cifras separadas e se recusa a somá-las. Um
projeto que contabiliza capacidade como caixa não está errado sobre o processo — a capacidade é
real — está errado sobre a conta bancária, e os dois erros são descobertos em momentos diferentes
por pessoas diferentes.

## Premissas e limitações

- **Um grupo de comparação precisa ser comparável.** A diferença em diferenças remove qualquer
  tendência *comum* aos dois grupos e nada mais. Onde os sites tratados estão em outra trajetória
  por razões próprias — equipamento mais novo, mix diferente, o motivo pelo qual foram escolhidos —
  a subtração remove a quantidade errada, e este módulo não consegue avisar que isso aconteceu.
  Tendências paralelas antes do corte é a premissa, e é verificável no mesmo painel; verificá-la não
  está implementado aqui.
- **Os sites tratados do painel são escolhidos ao acaso**, e é por isso que o efeito real é
  recuperável. Charters reais selecionam por desempenho, que é exatamente o caso que a simulação de
  regressão à média precifica — separadamente, e sem tendência, para que os dois erros não se
  escondam dentro de uma cifra.
- **Vinte sites são uma amostra pequena de sites**, e o intervalo diz isso: ±1 num efeito de 5. A
  unidade de análise ser o site e não o site-período é o que torna isso honesto, e é também o que
  torna o estudo pequeno. Mais meses não ajudam; mais sites ajudam.
- **Um corte, uma direção.** Sem adoção escalonada, em que sites começam em momentos diferentes, e
  sem previsão para um efeito que cresce ou decai depois da mudança. Os dois são comuns na prática
  e os dois exigem outro estimador que não um dois-por-dois.
- **A parcela variável é entrada, não achado.** 35% é parâmetro declarado aqui. Num caso real é uma
  discussão com o controller, é o número mais consequente do caso de benefício, e nenhuma
  quantidade de dado de processo o resolve.
- **Nada aqui desconta.** Uma economia no período doze é somada a uma do período um pelo valor de
  face. Em doze períodos é erro pequeno; numa alegação de cinco anos não é.
- **Payback não é retorno.** Ele ignora tudo o que vem depois, inclusive se o ganho se sustentou —
  que é a pergunta da fase Control e assunto do [`dmaic.control`](../control/README.md), não deste
  módulo.
