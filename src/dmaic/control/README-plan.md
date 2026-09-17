# `dmaic.control` — the control plan: what its triggers promise

*[Português](#dmaiccontrol--o-plano-de-controle-o-que-os-gatilhos-prometem)*

## The business problem

A control plan is a table of triggers. *React if the daily average moves more than a unit.* *React if
any piece falls outside specification.* *React if the figure moves three sigma.* Each of those is a
hypothesis test, run every day, for years.

The plan records who reacts, how, and to whom it escalates. It does not record the two numbers that
decide whether reacting is worth anything: **how often the trigger fires when nothing is wrong**, and
**how long it takes when something is**.

## The decision it enables

1. **What is this trigger's false-alarm rate, in reactions a year?** Which is the cost of the plan,
   paid by the people who react.
2. **What shift does it actually catch, and how fast?** Which is the benefit.
3. **How much of both belongs to the measurement system?** More than anybody expects, and the answer
   depends on which of two ways the trigger was written.

## Usage

```python
from dmaic.control import ReactionRule, alarms_against_delay, rule_from_spread, spec_trigger

rule = ReactionRule(limit=1.0, subgroup=20, process_sd=2.0, gage_sd=1.35)
rule.false_alarm_rate, rule.alarms_per_year, rule.gage_share  # 0.1900, 47.5, 40%
rule.delay(shift=1.0)  # periods to notice
rule.shift_caught_within(2)  # what two days buys
rule_from_spread(subgroup=20, process_sd=2.0, gage_sd=1.35)  # the limit the data sets
```

## Result: an absolute trigger has a false-alarm rate the gage controls

"React if the daily average moves more than 1.00", twenty units a day, on a process whose within-day
spread is 2.00. The gage rows are the three instruments of
[`README-msa.md`](../measure/README-msa.md), as the spread each adds to a reading.

| Gage | Gage sd | Total sd | False alarms per day | Days between them | Share from the gage | Days to catch a 1.00 shift |
| --- | --- | --- | --- | --- | --- | --- |
| no gage error | 0.0000 | 2.0000 | 0.1138 | 8.78 | 0% | 2.00 |
| 5.7% of tolerance | 0.4743 | 2.0555 | 0.1239 | 8.07 | 8% | 2.00 |
| 16.2% of tolerance | 1.3500 | 2.4130 | 0.1900 | 5.26 | **40%** | 1.98 |
| 63.6% of tolerance | 5.3000 | 5.6648 | **0.5767** | **1.73** | **80%** | 1.58 |

**A false alarm every 8.78 days becomes one every 1.73 days**, and **80% of the reactions on the last
row are the instrument**. Meanwhile the detection of a real shift barely moves — 2.00 days to 1.58 —
so the bad gage buys no speed at all and costs five times the reaction workload. The people reacting
experience that as a process out of control. It is a gage out of control, and the plan cannot tell
them apart.

## Result: a relative trigger hides the gage instead

The other way plans are written: *react if the move exceeds three sigma of the observed spread.* The
limit now comes from the data, so a worse gage widens it.

| Gage | Limit | False alarms per day | Smallest shift caught in 2 days | Days to catch a 1.00 shift |
| --- | --- | --- | --- | --- |
| no gage error | 1.8974 | 0.0027 | 1.8974 | 12.83 |
| 5.7% of tolerance | 1.9500 | 0.0027 | 1.9500 | 13.90 |
| 16.2% of tolerance | 2.2892 | 0.0027 | 2.2892 | 21.94 |
| 63.6% of tolerance | **5.3741** | **0.0027** | 5.3741 | **133.43** |

**The false-alarm rate is 0.0027 in every row — identical to four decimals, whatever the gage.** That
is the figure anybody checks, and it says the plan is behaving. What changes is the reaction: **12.83
days against 133.43, ten times slower**, for the same alarm rate and the same words on the page.

So the two forms of trigger fail in opposite directions. An absolute limit lets the gage set the
false-alarm rate; a limit derived from observed spread lets the gage set the detection limit while
holding the alarm rate still. **There is no form of words that escapes the measurement system — there
is only a choice about where it hides**, and the plan records neither choice.

## Result: a specification trigger is slow, and it is not silent

The commonest trigger of all: *react when any unit of the day falls outside specification.* Process
spread 8.00 against a 50-unit tolerance, so a capability index of **1.0417**.

| Shift (σ) | Units inspected | Rate per day | Days to react |
| --- | --- | --- | --- |
| 0.0 | 5 | 0.008859 | 112.88 |
| 0.0 | 20 | 0.034967 | **28.60** |
| 0.5 | 5 | 0.022185 | 45.08 |
| 0.5 | 20 | 0.085831 | 11.65 |
| 1.0 | 5 | 0.081280 | **12.30** |
| 1.0 | 20 | 0.287585 | 3.48 |
| 2.0 | 5 | 0.502423 | 1.99 |
| 2.0 | 20 | 0.938703 | 1.07 |

**With nothing wrong at all it fires every 28.60 days** — about 2.2 reactions a quarter on a process
that is exactly on target, which is not a rate anybody would defend out loud if it were written down.
It is not written down; it is a consequence of a capability index of 1.04, and the trigger looks like
it has no false-alarm rate because it is phrased as a fact about a part rather than as a test.

**And it is slow.** A one-sigma shift — a quarter of the tolerance — takes 3.48 days to surface at
twenty pieces and **12.30 days at five**. A trigger that reacts to a shift after two working weeks is
not a control, it is a record.

## Result: the trade the plan is making without saying so

One process, one subgroup size, five possible limits:

| Limit | False alarms per day | Alarms per year | Days to catch a 1.00 shift |
| --- | --- | --- | --- |
| 0.5000 | 0.4292 | **107.30** | 1.26 |
| 1.0000 | 0.1138 | 28.46 | 2.00 |
| 1.5000 | 0.0177 | 4.43 | 4.66 |
| 2.0000 | 0.0016 | 0.39 | 17.57 |
| 3.0000 | 0.0000 | 0.0005 | **1277.63** |

From **107 false alarms a year** with a 1.26-day reaction, to one every two thousand years with a
reaction that takes five. Somebody chose a row of this table when they wrote the plan. The plan does
not say which row, or why, and the person reacting has no way to find out.

**A control chart is the instrument that makes this trade explicit and tunable**, which is exactly
why it exists and why it is worth using. It lives in the sibling `oplab.spc` package. What is priced
here are the triggers people write *instead* of one — which is most of them.

## Assumptions and limitations

- **Normal, independent periods.** Every figure is a normal-theory calculation on a stable process
  with independent periods. A process with autocorrelation — which is most processes measured often
  enough to matter — has a different false-alarm rate, and the direction depends on the sign of the
  correlation.
- **The trigger is on the move, not on the level.** Comparing consecutive figures doubles the
  variance a single figure has, which is the first thing a plan written on "the move" gets wrong
  about its own sensitivity. A trigger on the level against a fixed target is a different
  calculation and is not implemented.
- **A sustained shift, detected on the first period it could be.** `delay` is the expected number of
  periods until the trigger fires, treating each period as an independent chance. A gradual drift
  fires later than this says, and a transient fires or does not fire on its own single period.
- **`shift_caught_within` uses the near tail only.** Ignoring the chance of tripping in the wrong
  direction makes the figure conservative rather than optimistic, which is the right direction for a
  promise but is not exact.
- **One trigger at a time.** A real plan has several, and several triggers running together have a
  combined false-alarm rate higher than any of them — the multiplicity nothing in this package
  corrects for, here as everywhere else.
- **Nothing here says who should react.** That is the part a control plan is actually for, and it is
  not arithmetic. This module prices the trigger so that the reaction is worth the interruption.
- **This is not a control chart and is not a substitute for one.** No run rules, no
  within-subgroup sigma, no chart at all: those are `oplab.spc`'s, and a plan that wants a tuned
  trade between false alarms and detection should use them rather than a trigger somebody wrote in a
  meeting.

---

# `dmaic.control` — o plano de controle: o que os gatilhos prometem

*[English](#dmaiccontrol--the-control-plan-what-its-triggers-promise)*

## O problema de negócio

Um plano de controle é uma tabela de gatilhos. *Reagir se a média diária mover mais de uma unidade.*
*Reagir se qualquer peça cair fora da especificação.* *Reagir se a cifra mover três sigma.* Cada um
desses é um teste de hipótese, rodado todo dia, por anos.

O plano registra quem reage, como, e para quem escala. Não registra as duas cifras que decidem se
reagir vale algo: **com que frequência o gatilho dispara quando nada está errado** e **quanto tempo
leva quando algo está**.

## A decisão que ele habilita

1. **Qual é a taxa de alarme falso deste gatilho, em reações por ano?** Que é o custo do plano, pago
   por quem reage.
2. **Que desvio ele de fato pega, e em quanto tempo?** Que é o benefício.
3. **Quanto dos dois pertence ao sistema de medição?** Mais do que se espera, e a resposta depende de
   qual das duas formas o gatilho foi escrito.

## Uso

```python
from dmaic.control import ReactionRule, alarms_against_delay, rule_from_spread, spec_trigger

regra = ReactionRule(limit=1.0, subgroup=20, process_sd=2.0, gage_sd=1.35)
regra.false_alarm_rate, regra.alarms_per_year, regra.gage_share  # 0,1900, 47,5, 40%
regra.delay(shift=1.0)  # períodos até notar
regra.shift_caught_within(2)  # o que dois dias compram
rule_from_spread(subgroup=20, process_sd=2.0, gage_sd=1.35)  # o limite que o dado fixa
```

## Resultado: um gatilho absoluto tem taxa de alarme falso que o gage controla

"Reagir se a média diária mover mais de 1,00", vinte unidades por dia, num processo cuja dispersão
intradiária é 2,00. As linhas de gage são os três instrumentos do
[`README-msa.md`](../measure/README-msa.md), como a dispersão que cada um adiciona a uma leitura.

| Gage | sd do gage | sd total | Alarmes falsos por dia | Dias entre eles | Parcela do gage | Dias para pegar desvio de 1,00 |
| --- | --- | --- | --- | --- | --- | --- |
| sem erro de gage | 0,0000 | 2,0000 | 0,1138 | 8,78 | 0% | 2,00 |
| 5,7% da tolerância | 0,4743 | 2,0555 | 0,1239 | 8,07 | 8% | 2,00 |
| 16,2% da tolerância | 1,3500 | 2,4130 | 0,1900 | 5,26 | **40%** | 1,98 |
| 63,6% da tolerância | 5,3000 | 5,6648 | **0,5767** | **1,73** | **80%** | 1,58 |

**Um alarme falso a cada 8,78 dias vira um a cada 1,73 dias**, e **80% das reações da última linha são
o instrumento**. Enquanto isso a detecção de um desvio real quase não muda — 2,00 dias para 1,58 —
então o gage ruim não compra velocidade nenhuma e custa cinco vezes a carga de reação. Quem reage
vivencia isso como um processo fora de controle. É um gage fora de controle, e o plano não distingue
os dois.

## Resultado: um gatilho relativo esconde o gage

A outra forma como planos são escritos: *reagir se o movimento exceder três sigma da dispersão
observada.* O limite agora vem do dado, então um gage pior o alarga.

| Gage | Limite | Alarmes falsos por dia | Menor desvio pego em 2 dias | Dias para pegar desvio de 1,00 |
| --- | --- | --- | --- | --- |
| sem erro de gage | 1,8974 | 0,0027 | 1,8974 | 12,83 |
| 5,7% da tolerância | 1,9500 | 0,0027 | 1,9500 | 13,90 |
| 16,2% da tolerância | 2,2892 | 0,0027 | 2,2892 | 21,94 |
| 63,6% da tolerância | **5,3741** | **0,0027** | 5,3741 | **133,43** |

**A taxa de alarme falso é 0,0027 em toda linha — idêntica até a quarta decimal, qualquer que seja o
gage.** É a cifra que qualquer um verifica, e ela diz que o plano está se comportando. O que muda é a
reação: **12,83 dias contra 133,43, dez vezes mais lento**, com a mesma taxa de alarme e as mesmas
palavras na página.

Então as duas formas de gatilho falham em direções opostas. Um limite absoluto deixa o gage fixar a
taxa de alarme falso; um limite derivado da dispersão observada deixa o gage fixar o limite de
detecção enquanto mantém a taxa de alarme parada. **Não existe forma de redação que escape do sistema
de medição — existe apenas uma escolha sobre onde ele se esconde**, e o plano não registra nenhuma das
duas.

## Resultado: um gatilho de especificação é lento, e não é silencioso

O gatilho mais comum de todos: *reagir quando qualquer unidade do dia cair fora da especificação.*
Dispersão do processo 8,00 contra tolerância de 50 unidades, logo índice de capabilidade **1,0417**.

| Desvio (σ) | Unidades inspecionadas | Taxa por dia | Dias para reagir |
| --- | --- | --- | --- |
| 0,0 | 5 | 0,008859 | 112,88 |
| 0,0 | 20 | 0,034967 | **28,60** |
| 0,5 | 5 | 0,022185 | 45,08 |
| 0,5 | 20 | 0,085831 | 11,65 |
| 1,0 | 5 | 0,081280 | **12,30** |
| 1,0 | 20 | 0,287585 | 3,48 |
| 2,0 | 5 | 0,502423 | 1,99 |
| 2,0 | 20 | 0,938703 | 1,07 |

**Sem nada errado ele dispara a cada 28,60 dias** — cerca de 2,2 reações por trimestre num processo
que está exatamente no alvo, o que não é uma taxa que alguém defenderia em voz alta se estivesse
escrita. Não está escrita; é consequência de um índice de capabilidade de 1,04, e o gatilho parece não
ter taxa de alarme falso porque está redigido como fato sobre uma peça e não como teste.

**E é lento.** Um desvio de um sigma — um quarto da tolerância — leva 3,48 dias para aparecer com
vinte peças e **12,30 dias com cinco**. Um gatilho que reage a um desvio depois de duas semanas de
trabalho não é controle, é registro.

## Resultado: a troca que o plano faz sem dizer

Um processo, um tamanho de subgrupo, cinco limites possíveis:

| Limite | Alarmes falsos por dia | Alarmes por ano | Dias para pegar desvio de 1,00 |
| --- | --- | --- | --- |
| 0,5000 | 0,4292 | **107,30** | 1,26 |
| 1,0000 | 0,1138 | 28,46 | 2,00 |
| 1,5000 | 0,0177 | 4,43 | 4,66 |
| 2,0000 | 0,0016 | 0,39 | 17,57 |
| 3,0000 | 0,0000 | 0,0005 | **1277,63** |

De **107 alarmes falsos por ano** com reação em 1,26 dia, a um a cada dois mil anos com reação que
leva cinco. Alguém escolheu uma linha desta tabela quando escreveu o plano. O plano não diz qual
linha, nem por quê, e quem reage não tem como descobrir.

**Uma carta de controle é o instrumento que torna essa troca explícita e ajustável**, que é exatamente
por que ela existe e por que vale usá-la. Ela mora no pacote irmão `oplab.spc`. O que é precificado
aqui são os gatilhos que as pessoas escrevem *em vez* de uma carta — que são a maioria deles.

## Premissas e limitações

- **Normal, períodos independentes.** Toda cifra é cálculo de teoria normal sobre processo estável com
  períodos independentes. Um processo com autocorrelação — que é a maioria dos processos medidos com
  frequência suficiente para importar — tem outra taxa de alarme falso, e a direção depende do sinal da
  correlação.
- **O gatilho é sobre o movimento, não sobre o nível.** Comparar cifras consecutivas dobra a variância
  que uma cifra isolada tem, que é a primeira coisa que um plano escrito sobre "o movimento" erra
  sobre a própria sensibilidade. Um gatilho sobre o nível contra um alvo fixo é outro cálculo e não
  está implementado.
- **Um desvio sustentado, detectado no primeiro período em que poderia ser.** O `delay` é o número
  esperado de períodos até o gatilho disparar, tratando cada período como chance independente. Uma
  deriva gradual dispara mais tarde do que isto diz, e um transiente dispara ou não no próprio período
  dele.
- **O `shift_caught_within` usa só a cauda próxima.** Ignorar a chance de disparar na direção errada
  torna a cifra conservadora e não otimista, que é a direção certa para uma promessa, mas não é exato.
- **Um gatilho por vez.** Um plano real tem vários, e vários gatilhos juntos têm taxa de alarme falso
  combinada maior que qualquer um deles — a multiplicidade que nada neste pacote corrige, aqui como em
  todo lugar.
- **Nada aqui diz quem deve reagir.** Essa é a parte para a qual um plano de controle de fato serve, e
  não é aritmética. Este módulo precifica o gatilho para que a reação valha a interrupção.
- **Isto não é uma carta de controle e não substitui uma.** Sem regras de corrida, sem sigma
  intra-subgrupo, sem carta alguma: aquilo é do `oplab.spc`, e um plano que queira uma troca ajustada
  entre alarme falso e detecção deve usá-las em vez de um gatilho que alguém escreveu numa reunião.
