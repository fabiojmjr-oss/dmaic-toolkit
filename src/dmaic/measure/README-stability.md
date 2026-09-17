# `dmaic.measure` — stability: how long does the answer last?

*[Português](#dmaicmeasure--estabilidade-quanto-tempo-a-resposta-dura)*

## The business problem

A gage study and a bias study are both snapshots. Neither form has a field for how far the day of
the readings sits from the last calibration, and an instrument that moves a tenth of a gram a day
is inside a twentieth of its tolerance for three weeks and outside it afterwards.

So the verdict on a measurement system is partly a statement about the calendar. Worse: because a
crossed study's sessions are spread over weeks — operators are rarely free on the same day — the
drift lands in whichever term of the ANOVA the **schedule** happens to align it with. The study
then names a cause, and the cause can be the wrong one.

## The decision it enables

1. **How often does this gage need calibrating?** An interval is an action. A drift coefficient is
   not, and a bias measured on one day is a coefficient with a date attached that nobody recorded.
2. **Is this study's verdict about the instrument or about how long the study took?** Answerable
   only if the day of each reading was written down — which is the whole ask of this document.

## Usage

```python
from dmaic.measure import calibration_interval, stability_study

checks = stability_study(readings, tolerance=50.0)  # readings with a reference and a day
checks.drift_per_day  # 0.105428
checks.days_to(5.0)  # 22.8 days until 5% of tolerance is spent
calibration_interval(0.10, tolerance=50.0)  # 25.0, from a datasheet rate and no study at all
```

## Result: the calibration interval

`BALANCA-01` again — the gage example 05 found reading 4 g heavy. Here it is watched from the day
it was calibrated: four readings on a master every five days for sixty days.

| Figure | Value |
| --- | --- |
| Drift recovered | **+0.105428 g/day** (built in: +0.10) |
| p-value | 3.3e-29 |
| r² | 0.9209 |
| Offset left behind on day 0 | −0.0932 g |
| Offset on day 60 | **+6.2325 g**, 12.47% of tolerance |
| Interval to 5% of tolerance | **22.8 days** |
| Same interval from the declared rate, no study | 25.0 days |
| Residual spread around the line | 0.5894 g |

**The calibration was fine and the instrument was not.** The offset on day zero is −0.0932 g, so
nothing was wrong when it was set; what is wrong is that it does not stay. The residual spread
around the fitted line, 0.5894, lands on the gage's own repeatability of 0.56 — once the drift is
modelled, what is left is the noise the crossed study already measured, which is the check that
this study is measuring a drift rather than dressing up scatter.

**And the 4 g offset of wave 5 arrives on day 37.9 at this rate.** That is a construction of the
generator rather than a discovery — 4.0 ÷ 0.10 is exactly 40 days, and the study recovers 37.9 —
but it is the point worth carrying out of both documents. A constant bias and a drift measured
late are *the same reading*. They are not the same problem, and they do not have the same answer:
a tare is removed once, a drift buys an interval.

## Result: where the drift goes in a crossed study

The same gage, a standard 10-part × 3-operator × 3-replicate study, spread over two weeks with
sessions a week apart. The two schedules hold **identical readings and identical days**; the only
difference is which day each reading falls on.

| Schedule | EV | AV | GRR | % study | % tolerance | ndc | Dominant source | Verdict |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| One operator per day | **0.6430** | **1.0081** | 1.1957 | 12.68 | 14.35 | 11 | **reproducibility** | conditional |
| Every operator every day | 0.9161 | 0.3829 | 0.9929 | 10.56 | 11.92 | 13 | repeatability | conditional |
| Drift removed | 0.6430 | 0.4010 | 0.7578 | 8.08 | 9.09 | 17 | repeatability | **acceptable** |

**Giving each operator their own day inflates reproducibility by 2.51× and leaves repeatability
untouched to four decimals.** 0.4010 becomes 1.0081; 0.6430 stays 0.6430. The calendar is reported
as the people. A project reading that study would go and retrain three operators who did nothing
wrong, and the sibling finding in [`README-msa.md`](README-msa.md) — that splitting GRR is what
makes a failed study actionable — becomes a way of arriving confidently at the wrong action.

**Interleaving does not make the drift disappear; it puts it in the right term.** Repeatability
goes to 0.9161, 1.42× the truth, and the operator estimate survives almost intact (0.3829 against
0.4010). That is the better schedule, and it is still not clean: a "repeatability" of 0.9161
contains two weeks of drift inside a term whose name says one session.

**Both drifted schedules come back *conditional* where the instrument on any single day is
*acceptable*.** The study's own conclusion depends on how long it took to run. Nothing on the form
records that, which is why this finding needed no new function — the evidence is in a study a
project has already run, as long as somebody wrote down the date.

## Assumptions and limitations

- **A straight line is a model of a drift, not all drifts.** Wear, contamination and a battery
  going flat are not linear, and a sensor that jumps after a knock is not drifting at all. The
  residual spread landing on the known repeatability is the check that the line fits here; where it
  comes back larger than the gage's repeatability, the shape is wrong and the rate means little.
- **`days_to` extrapolates, deliberately and beyond the data.** A gage watched for sixty days does
  not promise anything about day ninety. The interval is a planning figure that has to be re-earned
  at the next check, which is the argument for periodic checks rather than one study.
- **Environment is not separated from time.** Sixty days of drift and sixty days of a warming
  workshop are the same column here. Separating them needs the condition recorded alongside the
  day, which is another field the form does not have.
- **The schedule finding is about attribution, not about the total.** The drift is real variation
  and every drifted row above is honestly worse than the instrument on one day. What the schedule
  decides is which factor gets blamed, and that is what decides the spending.
- **Neither schedule is right.** The honest analysis adds the day as a term, which this module does
  not do: the crossed ANOVA in [`README-msa.md`](README-msa.md) has no place for it. Interleaving
  and recording the date is what can be done with the tools here.
- **Control charting a gage over time is out of scope on purpose.** A chart on a master with run
  rules is the standard way to watch stability, and charts live in the sibling `oplab.spc` package
  rather than being written twice.

---

# `dmaic.measure` — estabilidade: quanto tempo a resposta dura?

*[English](#dmaicmeasure--stability-how-long-does-the-answer-last)*

## O problema de negócio

Um estudo de gage e um estudo de viés são os dois retratos. Nenhum dos dois formulários tem campo
para a distância entre o dia das leituras e a última calibração, e um instrumento que anda um
décimo de grama por dia fica dentro de um vigésimo da tolerância por três semanas e fora dela
depois.

Então o veredito sobre um sistema de medição é em parte uma afirmação sobre o calendário. Pior:
como as sessões de um estudo cruzado se espalham por semanas — operadores raramente estão livres no
mesmo dia — a deriva cai no termo da ANOVA com o qual a **agenda** por acaso a alinhou. O estudo
então nomeia uma causa, e a causa pode ser a errada.

## A decisão que ele habilita

1. **Com que frequência este gage precisa de calibração?** Um intervalo é uma ação. Um coeficiente
   de deriva não é, e um viés medido em um dia é um coeficiente com uma data que ninguém anotou.
2. **O veredito deste estudo é sobre o instrumento ou sobre quanto tempo o estudo levou?**
   Respondível só se o dia de cada leitura foi registrado — que é o pedido inteiro deste documento.

## Uso

```python
from dmaic.measure import calibration_interval, stability_study

checks = stability_study(leituras, tolerance=50.0)  # leituras com referência e dia
checks.drift_per_day  # 0,105428
checks.days_to(5.0)  # 22,8 dias até gastar 5% da tolerância
calibration_interval(0.10, tolerance=50.0)  # 25,0, a partir de uma taxa de catálogo e nenhum estudo
```

## Resultado: o intervalo de calibração

`BALANCA-01` de novo — o gage que o exemplo 05 achou lendo 4 g acima. Aqui ele é acompanhado desde o
dia em que foi calibrado: quatro leituras num padrão a cada cinco dias, por sessenta dias.

| Figura | Valor |
| --- | --- |
| Deriva recuperada | **+0,105428 g/dia** (embutida: +0,10) |
| p-valor | 3,3e-29 |
| r² | 0,9209 |
| Desvio deixado no dia 0 | −0,0932 g |
| Desvio no dia 60 | **+6,2325 g**, 12,47% da tolerância |
| Intervalo até 5% da tolerância | **22,8 dias** |
| O mesmo intervalo pela taxa declarada, sem estudo | 25,0 dias |
| Dispersão residual em torno da reta | 0,5894 g |

**A calibração estava boa e o instrumento não.** O desvio no dia zero é −0,0932 g, então nada
estava errado quando foi ajustado; o que está errado é que ele não fica. A dispersão residual em
torno da reta, 0,5894, cai sobre a repetibilidade própria do gage, 0,56 — modelada a deriva, o que
sobra é o ruído que o estudo cruzado já media, e essa é a verificação de que este estudo mede uma
deriva em vez de enfeitar dispersão.

**E o desvio de 4 g da onda 5 chega no dia 37,9 nesta taxa.** Isso é construção do gerador e não
descoberta — 4,0 ÷ 0,10 é exatamente 40 dias, e o estudo recupera 37,9 — mas é o ponto que vale
levar dos dois documentos. Um viés constante e uma deriva medida tarde são *a mesma leitura*. Não
são o mesmo problema, e não têm a mesma resposta: uma tara se remove uma vez, uma deriva compra um
intervalo.

## Resultado: onde a deriva cai num estudo cruzado

O mesmo gage, um estudo padrão de 10 peças × 3 operadores × 3 réplicas, espalhado por duas semanas
com sessões a uma semana de distância. As duas agendas têm **leituras idênticas e dias idênticos**;
a única diferença é em que dia cada leitura cai.

| Agenda | EV | AV | GRR | % estudo | % tolerância | ndc | Fonte dominante | Veredito |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Um operador por dia | **0,6430** | **1,0081** | 1,1957 | 12,68 | 14,35 | 11 | **reprodutibilidade** | condicional |
| Todo operador todo dia | 0,9161 | 0,3829 | 0,9929 | 10,56 | 11,92 | 13 | repetibilidade | condicional |
| Deriva removida | 0,6430 | 0,4010 | 0,7578 | 8,08 | 9,09 | 17 | repetibilidade | **aceitável** |

**Dar a cada operador o seu próprio dia infla a reprodutibilidade em 2,51× e deixa a repetibilidade
intacta até a quarta decimal.** 0,4010 vira 1,0081; 0,6430 continua 0,6430. O calendário é
reportado como sendo das pessoas. Um projeto lendo esse estudo iria retreinar três operadores que
não fizeram nada errado, e o achado irmão do [`README-msa.md`](README-msa.md) — que separar o GRR é
o que torna um estudo reprovado acionável — passa a ser um jeito de chegar com confiança à ação
errada.

**Intercalar não faz a deriva desaparecer; põe ela no termo certo.** A repetibilidade vai a 0,9161,
1,42× a verdade, e a estimativa dos operadores sobrevive quase intacta (0,3829 contra 0,4010). Essa
é a agenda melhor, e ainda não é limpa: uma "repetibilidade" de 0,9161 contém duas semanas de
deriva dentro de um termo cujo nome diz uma sessão.

**As duas agendas com deriva voltam *condicional* onde o instrumento em qualquer dia único é
*aceitável*.** A conclusão do próprio estudo depende de quanto tempo ele levou. Nada no formulário
registra isso, e é por isso que este achado não precisou de função nova — a evidência está num
estudo que o projeto já rodou, desde que alguém tenha anotado a data.

## Premissas e limitações

- **Uma reta é um modelo de deriva, não de todas as derivas.** Desgaste, contaminação e uma bateria
  acabando não são lineares, e um sensor que salta depois de uma pancada não está derivando. A
  dispersão residual cair sobre a repetibilidade conhecida é a verificação de que a reta serve aqui;
  onde ela volta maior que a repetibilidade do gage, a forma está errada e a taxa significa pouco.
- **O `days_to` extrapola, deliberadamente e além do dado.** Um gage acompanhado por sessenta dias
  não promete nada sobre o dia noventa. O intervalo é uma cifra de planejamento que tem de ser
  reconquistada na próxima verificação, e esse é o argumento por verificações periódicas em vez de
  um estudo.
- **Ambiente não é separado de tempo.** Sessenta dias de deriva e sessenta dias de uma oficina
  esquentando são a mesma coluna aqui. Separar exige a condição registrada ao lado do dia, que é
  outro campo que o formulário não tem.
- **O achado da agenda é sobre atribuição, não sobre o total.** A deriva é variação real e toda
  linha com deriva acima é honestamente pior que o instrumento em um dia. O que a agenda decide é
  qual fator é culpado, e é isso que decide o gasto.
- **Nenhuma das duas agendas está certa.** A análise honesta inclui o dia como termo, o que este
  módulo não faz: a ANOVA cruzada do [`README-msa.md`](README-msa.md) não tem lugar para ele.
  Intercalar e registrar a data é o que se consegue com as ferramentas daqui.
- **Cartear um gage ao longo do tempo está fora de escopo de propósito.** Uma carta sobre um padrão
  com regras de corrida é a forma padrão de acompanhar estabilidade, e cartas moram no pacote irmão
  `oplab.spc` em vez de serem escritas duas vezes.
