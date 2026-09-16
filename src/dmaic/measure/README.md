# `dmaic.measure` — measurement system analysis

*[Português](#dmaicmeasure--análise-do-sistema-de-medição)*

## The business problem

Before an improvement project measures anything, something has to establish that its
measurements mean something. A gage study answers one question: **of the variation you can see,
how much is the parts and how much is the act of measuring them?**

It is the phase gate projects skip most often, and skipping it is not a documentation lapse.
Every number that comes later — a capability index, a before-and-after test, a factorial effect —
is computed on readings. A measurement system that cannot resolve the parts it measures makes all
of them noise with a decimal point on.

## The decision it enables

Three decisions, in this order:

1. **Can this gage be used at all?** Percent study variation against the 10% / 30% bands, and the
   number of distinct categories against five.
2. **If not, what would fix it?** Repeatability is the instrument — resolution, fixturing, wear.
   Reproducibility is the method — training, procedure, how the reading is taken. The two have
   different budgets and different owners.
3. **Can it support the specification?** A separate question from (1), and a gage can pass one
   and fail the other.

## Usage

```python
from dmaic.measure import gage_rr
from dmaic.synth import generate_dataset

data = generate_dataset()
study = data.gage_studies[data.gage_studies["gage"] == "PAQUIMETRO-02"]

fitted = gage_rr(study, tolerance=1.0, gage="PAQUIMETRO-02")
print(fitted.verdict(), fitted.pct_study, fitted.pct_tolerance, fitted.ndc)
print(fitted.summary())
```

## Result

Three measurement systems from the synthetic dataset, each a 10-part × 3-operator × 3-replicate
crossed study:

| Gage | EV | AV | GRR | PV | % contribution | % study variation | % tolerance | ndc | verdict |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `BALANCA-01` | 0.3956 | 0.2616 | 0.4743 | 7.5277 | 0.40 | 6.29 | 5.69 | 22 | acceptable |
| `PAQUIMETRO-02` | 0.0659 | 0.0830 | 0.1060 | 0.6439 | **2.64** | **16.24** | **63.58** | 8 | unacceptable |
| `INSPECAO-03` | 1.2467 | 3.9790 | 4.1698 | 5.0036 | 40.99 | 64.02 | 62.55 | 1 | unacceptable |

### `PAQUIMETRO-02` is the same gage read three ways

**2.64, 16.24 and 63.58 are the same measurement system.** Percent contribution is a ratio of
variances, percent study variation is a ratio of standard deviations, and percent tolerance
compares the gage to the specification instead of to the parts.

Only one of them answers the question the acceptance bands are written for. The 10% / 30% bands
are percent **study variation** — so this gage is conditional against the process it measures, and
unacceptable against the specification it is used to disposition against. A practitioner reading
percent contribution sees 2.64 and calls it excellent, which is not a rounding disagreement: it is
the same number squared, and squaring a fraction moves it toward zero.

The gap between 16.24 and 63.58 is not an error either. The parts vary more than the tolerance
allows for, so a gage that can just about tell these parts apart cannot tell a conforming part
from a non-conforming one. Both figures are true and they answer different questions; a study that
reports one without the other has picked a verdict rather than derived it.

### Splitting GRR is what makes a failed study actionable

`INSPECAO-03` fails at 64% of study variation, and its reproducibility is **3.2× its
repeatability** (3.9790 against 1.2467). The instrument is not the problem. Replacing it — the
commonest response to a failed study, and the one with an invoice attached — would change almost
nothing, because the variation is in how three operators take the same reading differently.

`BALANCA-01` is the mirror image: repeatability dominates, the people are consistent, and what is
left is the instrument's own resolution. It is also already acceptable, so there is nothing to buy.

## Pooling the interaction is a decision, and it changes the diagnosis

AIAG's rule drops the part-by-operator term when its p-value exceeds 0.25 and pools it into
repeatability. On this dataset the rule retains the interaction for all three gages
(p = 0.0357, < 0.0001 and < 0.0001). Forcing the pool anyway shows what the rule is protecting:

| | EV | AV | GRR | % study variation | dominant source |
| --- | --- | --- | --- | --- | --- |
| `PAQUIMETRO-02`, interaction retained | 0.0659 | 0.0830 | 0.1060 | 16.24 | reproducibility |
| `PAQUIMETRO-02`, interaction pooled | 0.0954 | **0.0000** | 0.0954 | 14.63 | **repeatability** |
| `INSPECAO-03`, interaction retained | 1.2467 | 3.9790 | 4.1698 | 64.02 | reproducibility |
| `INSPECAO-03`, interaction pooled | 2.9918 | 2.4435 | 3.8628 | 59.12 | **repeatability** |

The GRR barely moves — 16.24 to 14.63 — and that is the least of it. **Pooling flips the
diagnosis.** On `PAQUIMETRO-02` reproducibility goes to exactly zero, and a study that reported
it would send the project to buy an instrument when the problem is that operators diverge on
particular parts. The cheap error here is not the 1.6 points of GRR; it is the capital
expenditure the number justifies.

So `gage_rr` applies the rule, reports which branch it took in
`GageStudy.interaction_pooled`, and lets the caller override it.

## Assumptions and limitations

- **The design must be crossed and balanced.** Every operator measures every part the same number
  of times. This decomposition has no meaning otherwise, so `anova` raises rather than returning a
  number. Nested designs — destructive testing, where no two operators can measure the same part —
  need a different model, which this module does not yet implement.
- **Two replicates minimum.** One measurement per cell leaves no degrees of freedom for
  repeatability, and the interaction cannot be separated from the error. `anova` raises.
- **Negative variance components are clamped to zero and reported.** A negative estimate is not a
  negative quantity; it means the study is too small to resolve that effect. `PAQUIMETRO-02`
  reports `clamped=('operator',)` — with an interaction that strong, ten parts cannot resolve the
  operator main effect, and the zero is an admission rather than a measurement.
- **Percent tolerance depends on the sigma multiplier; percent study variation does not.** AIAG
  moved from 5.15 to 6.0, and the two give figures exactly 1.1650× apart on identical data. A
  study quoting percent tolerance without its multiplier cannot be reproduced. The default is 6.0.
- **The F tests use random-effects denominators.** Part and operator are tested against the
  interaction mean square, not against error. A fixed-effects routine tests them against error and
  reports operator effects as significant that are not.
- **Parts should span the process range.** Ten parts drawn from a narrow window inflate the GRR
  percentage without the gage having changed, because the denominator shrank. Nothing in the
  arithmetic can detect this, which is why it is a limitation rather than a check.
- **No bias or linearity study.** GRR measures precision, not accuracy. A gage can be perfectly
  repeatable and consistently wrong, and nothing in this module would notice. That needs a
  reference standard, which the synthetic dataset does not yet carry.

## Where the control charts are

Statistical process control — control charts, Nelson run rules, capability against
within-subgroup sigma — is **not** reimplemented here. It lives in the sibling `oplab.spc`
package. Two repositories holding the same code under one name would read as padding, so the
`control` phase in this toolkit covers the control plan, the sampling plan and sustaining
verification, and points at `oplab.spc` for the charting.

---

# `dmaic.measure` — análise do sistema de medição

*[English](#dmaicmeasure--measurement-system-analysis)*

## O problema de negócio

Antes de um projeto de melhoria medir qualquer coisa, alguém tem de estabelecer que as medições
significam algo. Um estudo de gage responde a uma pergunta: **da variação que você vê, quanto é
das peças e quanto é do ato de medi-las?**

É o portão de fase que projetos mais pulam, e pular não é uma falha de documentação. Todo número
que vem depois — índice de capabilidade, teste antes-e-depois, efeito fatorial — é calculado sobre
leituras. Um sistema de medição que não resolve as peças que mede transforma todos eles em ruído
com casa decimal.

## A decisão que ele habilita

Três decisões, nesta ordem:

1. **Este gage pode ser usado?** %variação do estudo contra as faixas de 10% / 30%, e o número de
   categorias distintas contra cinco.
2. **Se não, o que resolveria?** Repetibilidade é o instrumento — resolução, fixação, desgaste.
   Reprodutibilidade é o método — treinamento, procedimento, como a leitura é tomada. As duas têm
   orçamentos diferentes e donos diferentes.
3. **Ele sustenta a especificação?** Pergunta separada da (1), e um gage pode passar numa e
   reprovar na outra.

## Uso

```python
from dmaic.measure import gage_rr
from dmaic.synth import generate_dataset

data = generate_dataset()
study = data.gage_studies[data.gage_studies["gage"] == "PAQUIMETRO-02"]

fitted = gage_rr(study, tolerance=1.0, gage="PAQUIMETRO-02")
print(fitted.verdict(), fitted.pct_study, fitted.pct_tolerance, fitted.ndc)
print(fitted.summary())
```

## Resultado

Três sistemas de medição do conjunto sintético, cada um um estudo cruzado de 10 peças ×
3 operadores × 3 réplicas:

| Gage | EV | AV | GRR | PV | % contribuição | % variação do estudo | % tolerância | ndc | veredito |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `BALANCA-01` | 0,3956 | 0,2616 | 0,4743 | 7,5277 | 0,40 | 6,29 | 5,69 | 22 | aceitável |
| `PAQUIMETRO-02` | 0,0659 | 0,0830 | 0,1060 | 0,6439 | **2,64** | **16,24** | **63,58** | 8 | inaceitável |
| `INSPECAO-03` | 1,2467 | 3,9790 | 4,1698 | 5,0036 | 40,99 | 64,02 | 62,55 | 1 | inaceitável |

### `PAQUIMETRO-02` é o mesmo gage lido de três formas

**2,64, 16,24 e 63,58 são o mesmo sistema de medição.** %contribuição é razão de variâncias,
%variação do estudo é razão de desvios-padrão, e %tolerância compara o gage à especificação em vez
de às peças.

Só uma delas responde à pergunta para a qual as faixas de aceitação foram escritas. As faixas de
10% / 30% são de %**variação do estudo** — então este gage é condicional contra o processo que ele
mede, e inaceitável contra a especificação para a qual é usado para liberar peça. Quem lê
%contribuição vê 2,64 e chama de excelente, e isso não é divergência de arredondamento: é o mesmo
número ao quadrado, e elevar uma fração ao quadrado a empurra para zero.

A distância entre 16,24 e 63,58 também não é erro. As peças variam mais do que a tolerância
admite, então um gage que consegue mal distinguir estas peças não consegue distinguir peça conforme
de peça não conforme. As duas figuras são verdadeiras e respondem a perguntas diferentes; um estudo
que reporta uma sem a outra escolheu um veredito em vez de derivá-lo.

### Separar o GRR é o que torna um estudo reprovado acionável

`INSPECAO-03` reprova a 64% da variação do estudo, e sua reprodutibilidade é **3,2× a
repetibilidade** (3,9790 contra 1,2467). O instrumento não é o problema. Substituí-lo — a resposta
mais comum a um estudo reprovado, e a que vem com nota fiscal — mudaria quase nada, porque a
variação está em como três operadores tomam a mesma leitura de formas diferentes.

`BALANCA-01` é a imagem espelhada: repetibilidade domina, as pessoas são consistentes, e o que
resta é a resolução do próprio instrumento. Ele também já é aceitável, então não há o que comprar.

## Agrupar a interação é uma decisão, e ela muda o diagnóstico

A regra da AIAG descarta o termo peça × operador quando seu p-valor passa de 0,25 e o agrupa na
repetibilidade. Neste conjunto a regra retém a interação nos três gages
(p = 0,0357, < 0,0001 e < 0,0001). Forçar o agrupamento mostra o que a regra está protegendo:

| | EV | AV | GRR | % variação do estudo | fonte dominante |
| --- | --- | --- | --- | --- | --- |
| `PAQUIMETRO-02`, interação retida | 0,0659 | 0,0830 | 0,1060 | 16,24 | reprodutibilidade |
| `PAQUIMETRO-02`, interação agrupada | 0,0954 | **0,0000** | 0,0954 | 14,63 | **repetibilidade** |
| `INSPECAO-03`, interação retida | 1,2467 | 3,9790 | 4,1698 | 64,02 | reprodutibilidade |
| `INSPECAO-03`, interação agrupada | 2,9918 | 2,4435 | 3,8628 | 59,12 | **repetibilidade** |

O GRR quase não se move — 16,24 para 14,63 — e isso é o menos importante. **Agrupar inverte o
diagnóstico.** No `PAQUIMETRO-02` a reprodutibilidade vai a exatamente zero, e um estudo que
reportasse isso mandaria o projeto comprar instrumento quando o problema é que operadores divergem
em peças específicas. O erro caro aqui não são os 1,6 pontos de GRR; é o investimento que o número
justifica.

Então `gage_rr` aplica a regra, reporta qual ramo tomou em `GageStudy.interaction_pooled`, e
permite que quem chama sobreponha a decisão.

## Premissas e limitações

- **O desenho tem de ser cruzado e balanceado.** Cada operador mede cada peça o mesmo número de
  vezes. Esta decomposição não tem significado fora disso, então `anova` levanta erro em vez de
  devolver número. Desenhos aninhados — ensaio destrutivo, em que dois operadores não podem medir a
  mesma peça — pedem outro modelo, que este módulo ainda não implementa.
- **Mínimo de duas réplicas.** Uma medição por célula não deixa graus de liberdade para
  repetibilidade, e a interação não se separa do erro. `anova` levanta erro.
- **Componentes de variância negativos são zerados e reportados.** Estimativa negativa não é
  quantidade negativa; significa que o estudo é pequeno demais para resolver aquele efeito.
  `PAQUIMETRO-02` reporta `clamped=('operator',)` — com interação tão forte, dez peças não resolvem
  o efeito principal de operador, e o zero é uma admissão, não uma medição.
- **%tolerância depende do multiplicador sigma; %variação do estudo não.** A AIAG mudou de 5,15
  para 6,0, e os dois dão figuras exatamente 1,1650× distantes nos mesmos dados. Um estudo que cita
  %tolerância sem o multiplicador não é reproduzível. O padrão é 6,0.
- **Os testes F usam denominadores de efeitos aleatórios.** Peça e operador são testados contra o
  quadrado médio da interação, não contra o erro. Uma rotina de efeitos fixos os testa contra o
  erro e reporta como significativos efeitos de operador que não são.
- **As peças devem cobrir a faixa do processo.** Dez peças tiradas de uma janela estreita inflam o
  percentual de GRR sem o gage ter mudado, porque o denominador encolheu. Nada na aritmética
  detecta isso, e é por isso que é limitação e não verificação.
- **Sem estudo de bias ou linearidade.** GRR mede precisão, não exatidão. Um gage pode ser
  perfeitamente repetível e consistentemente errado, e nada neste módulo notaria. Isso exige padrão
  de referência, que o conjunto sintético ainda não carrega.

## Onde estão as cartas de controle

Controle estatístico de processo — cartas de controle, regras de Nelson, capabilidade contra sigma
intra-subgrupo — **não** é reimplementado aqui. Vive no pacote irmão `oplab.spc`. Dois
repositórios com o mesmo código sob um nome leriam como enchimento, então a fase `control` deste
toolkit cobre o plano de controle, o plano de amostragem e a verificação de sustentação, e aponta
para o `oplab.spc` para a parte de cartas.
