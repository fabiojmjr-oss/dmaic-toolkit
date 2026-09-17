# `dmaic.control` — acceptance sampling: what the plan guarantees

*[Português](#dmaiccontrol--amostragem-de-aceitação-o-que-o-plano-garante)*

## The business problem

A sampling plan is written as a rule: *inspect ten percent of the lot, reject on any defective*, or
*AQL 1.0%*. It is read as a threshold and defended as a policy. It is neither. Two numbers — how
many units to draw and how many defectives to tolerate — fix a **curve**, and almost every argument
about sampling is an argument about one point on a curve nobody drew.

## The decision it enables

1. **What does this plan actually catch, and what does it let through?** Both, as probabilities, at
   every quality level rather than at the one the plan is named after.
2. **What is the cheapest plan that meets the two quality levels I care about?** Which requires
   naming both: the level a lot should pass at, and the level it should fail at. A plan derived
   from one of them is half a plan.
3. **What did the inspection buy?** In defective units shipped and good lots quarantined, against
   the units inspected to get there.

## Usage

```python
from dmaic.control import SamplingPlan, oc_curve, percentage_plan, plan_for

percentage_plan(lot_size=1000)  # what "inspect 10%" really is: n=100, c=0
SamplingPlan(125, 3, lot_size=1000).verdict(0.01, 0.03)
plan_for(aql=0.01, rql=0.04, lot_size=1000)  # n=189 c=4, searched not looked up
oc_curve(plan, (0.005, 0.01, 0.02, 0.03))  # the plan, as the thing it really is
```

## Result: "inspect ten percent" controls nothing

The rule is one sentence and it is the same everywhere. The only number in it that matters — the
sample size — is set by the lot size, which is a shipping decision. Good lots here are 0.5%
defective and excursions are 4.0%.

| Lot size | 10% rule, n | Accepts good lots | Accepts excursions | n=80 accepts good | n=80 accepts excursions |
| --- | --- | --- | --- | --- | --- |
| 100 | 10 | 1.000000 | **0.651631** | 1.000000 | 0.001236 |
| 500 | 50 | 0.809820 | 0.116411 | 0.705331 | 0.028394 |
| 1,000 | 100 | 0.589832 | 0.013520 | 0.658507 | 0.033206 |
| 5,000 | 500 | 0.071311 | ~0 | 0.667502 | 0.037165 |
| 20,000 | 2,000 | **0.000026** | ~0 | 0.669115 | 0.037917 |

**The same written rule runs from accepting two excursions in three to rejecting essentially every
lot, good ones included.** On a lot of a hundred it is a formality; on a lot of twenty thousand it
rejects 99.997% of material that is perfectly fine, because a 0.5% defect rate puts ten defectives
in the lot and the rule draws two thousand units and tolerates none. Neither level was chosen by
anybody.

A fixed sample of eighty holds both numbers steady across every lot size above five hundred —
0.659 to 0.669 on good lots, 0.028 to 0.038 on excursions. That constancy is the property the
percentage rule is usually assumed to have, and it belongs to the fixed plan instead.

## Result: an acceptance quality level is a producer's risk

The classic published plan, `n=125, c=3`, quoted at AQL 1.0%, on a lot of a thousand:

| Incoming defective | Accepted | Average outgoing quality |
| --- | --- | --- |
| 0.500% | 0.9989 | 0.00437 |
| 1.000% | **0.9732** | 0.00852 |
| 2.000% | 0.7668 | 0.01342 |
| 3.000% | **0.4713** | 0.01237 |
| 4.000% | 0.2408 | 0.00843 |
| 5.000% | 0.1077 | 0.00471 |

**At the quoted 1% the plan does exactly what its name says — it rejects 2.7% of good lots. At
three times that level it is a coin toss.** The number in the plan's name is the point where the
*producer* is protected; what the customer receives at any other level is a separate point on the
same curve, and nothing in the name refers to it.

The average outgoing quality column says the other half: it has a **maximum**, at 2% incoming. A
plan cannot make outgoing quality better than incoming; it bounds it, and the bound is not zero.
Sampling sorts lots. It does not change what is in them.

## Result: a zero acceptance number is not the strict option

"Reject on a single defective" sounds like the tightest rule available, and at the same sample size
it is. But plans exist to let good material through, so the comparison that matters holds the
producer's risk fixed:

| Plan | Sample | Rejects good lots (1%) | Accepts 3% lots | Accepts 4% lots |
| --- | --- | --- | --- | --- |
| `n=125, c=3` | 125 | 2.7% | 47.1% | 24.1% |
| `c=0` matched at the 1% level | **3** | 3.0% | **91.3%** | **88.5%** |
| `c=0` at the same sample size | 125 | **73.9%** | 1.7% | 0.4% |

**Matching the published plan's producer risk with a zero acceptance number takes a sample of
three, and that plan accepts 88.5% of the lots it exists to catch.** Push the sample back up to
125 and the same rule rejects three quarters of good production. There is no `c=0` plan that is
both tolerable at the acceptance level and discriminating above it: the acceptance number is not a
strictness dial, and the discrimination of a plan comes from its **sample size**.

## Result: what each plan bought

Two hundred lots of a thousand units, one in ten an excursion, 1,478 defective units in total.
Each plan applied to the same lots, sampling drawn from the defectives each lot actually contains.

| Plan | Units inspected | Excursions caught | Good lots rejected | Defective units shipped |
| --- | --- | --- | --- | --- |
| 10% of the lot, c=0 | 20,000 | **12/12** | **70** | 543 |
| n=125 c=3 (AQL 1.0%) | 25,000 | 9/12 | 0 | **1,098** |
| n=125 c=0 | 25,000 | 12/12 | 86 | 474 |
| n=3 c=0 (matched risk) | 600 | 2/12 | 4 | 1,383 |
| Designed for 1% vs 4% | 37,800 | **10/12** | **1** | 1,066 |
| No inspection | 0 | 0/12 | 0 | 1,478 |

**The published plan inspects 25,000 units and ships three quarters of the defects.** It rejects no
good lot, which is what it was designed to do, and it misses a quarter of the excursions.

**The plan that catches every excursion does it by quarantining more than a third of good
production.** 70 good lots out of 188 on the percentage rule, 86 on `n=125 c=0`. Those plans are
not discriminating, they are harsh, and the difference is only visible with both columns in front of
you.

**Designing to both quality levels is the only row that is good at both**, and it costs the most
inspection: 37,800 units to catch 10 of 12 excursions while rejecting one good lot. That is the
trade, priced.

## Assumptions and limitations

- **The excursion counts are one realisation, the probabilities are exact.** "12/12" and "9/12"
  come from one seeded pass over 200 lots and would move on another; the acceptance probabilities
  in the tables above are computed, not simulated. Where the two disagree, believe the
  probabilities.
- **`average_outgoing_quality` assumes rejected lots are screened and made good.** That is
  *rectifying* inspection, and it is often not what happens: where rejected lots go back to the
  supplier, the figure does not describe what is shipped. The assumption is stated in the method
  because it is usually left implicit.
- **Every plan here is single sampling.** Double, multiple and sequential plans reach the same two
  risk points with a smaller average sample, which is their whole argument, and they are not
  implemented.
- **No switching rules.** Published schemes tighten after rejections and loosen after a clean run,
  and that switching — not the individual plan — is where most of their protection comes from.
  A single plan evaluated on its own curve is a fair description of a plan and an unfair
  description of a scheme.
- **Lots are assumed homogeneous and randomly sampled.** A lot where the defectives are the first
  hour of a shift, sampled from whatever is on top of the pallet, has no operating characteristic
  curve at all. This is the assumption most often violated in practice and the one the arithmetic
  cannot detect.
- **Defective is binary and correctly judged.** The measurement error of the inspection itself is
  not modelled here; [`dmaic.measure`](../measure/README.md) is upstream of this whole document,
  and an inspector with 90% agreement changes every figure in it.
- **Acceptance sampling is not process control.** A plan is an argument about material already
  made. What keeps the process in control is charted in the sibling `oplab.spc` package, and no
  sampling plan substitutes for it.

---

# `dmaic.control` — amostragem de aceitação: o que o plano garante

*[English](#dmaiccontrol--acceptance-sampling-what-the-plan-guarantees)*

## O problema de negócio

Um plano de amostragem é escrito como regra: *inspecione dez por cento do lote, rejeite com
qualquer defeituoso*, ou *AQL 1,0%*. É lido como limite e defendido como política. Não é nenhum dos
dois. Dois números — quantas unidades sortear e quantos defeituosos tolerar — fixam uma **curva**, e
quase toda discussão sobre amostragem é uma discussão sobre um ponto de uma curva que ninguém
desenhou.

## A decisão que ele habilita

1. **O que este plano de fato pega, e o que ele deixa passar?** Os dois, como probabilidades, em
   todo nível de qualidade e não apenas naquele que dá nome ao plano.
2. **Qual é o plano mais barato que atende aos dois níveis de qualidade que me interessam?** O que
   exige nomear os dois: o nível em que um lote deve passar e o nível em que deve reprovar. Um plano
   derivado de só um deles é meio plano.
3. **O que a inspeção comprou?** Em unidades defeituosas expedidas e lotes bons em quarentena,
   contra as unidades inspecionadas para chegar lá.

## Uso

```python
from dmaic.control import SamplingPlan, oc_curve, percentage_plan, plan_for

percentage_plan(lot_size=1000)  # o que "inspecionar 10%" realmente é: n=100, c=0
SamplingPlan(125, 3, lot_size=1000).verdict(0.01, 0.03)
plan_for(aql=0.01, rql=0.04, lot_size=1000)  # n=189 c=4, buscado e não consultado em tabela
oc_curve(plano, (0.005, 0.01, 0.02, 0.03))  # o plano, como a coisa que ele é
```

## Resultado: "inspecionar dez por cento" não controla nada

A regra é uma frase e é a mesma em todo lugar. O único número dela que importa — o tamanho da
amostra — é fixado pelo tamanho do lote, que é uma decisão de expedição. Lotes bons aqui são 0,5%
defeituosos e excursões são 4,0%.

| Tamanho do lote | Regra 10%, n | Aceita lotes bons | Aceita excursões | n=80 aceita bons | n=80 aceita excursões |
| --- | --- | --- | --- | --- | --- |
| 100 | 10 | 1,000000 | **0,651631** | 1,000000 | 0,001236 |
| 500 | 50 | 0,809820 | 0,116411 | 0,705331 | 0,028394 |
| 1.000 | 100 | 0,589832 | 0,013520 | 0,658507 | 0,033206 |
| 5.000 | 500 | 0,071311 | ~0 | 0,667502 | 0,037165 |
| 20.000 | 2.000 | **0,000026** | ~0 | 0,669115 | 0,037917 |

**A mesma regra escrita vai de aceitar duas excursões em três a rejeitar praticamente todo lote,
inclusive os bons.** Num lote de cem é formalidade; num lote de vinte mil ela rejeita 99,997% de
material perfeitamente bom, porque uma taxa de 0,5% põe dez defeituosos no lote e a regra sorteia
duas mil unidades sem tolerar nenhum. Nenhum dos dois níveis foi escolhido por alguém.

Uma amostra fixa de oitenta mantém os dois números estáveis em todo lote acima de quinhentos — 0,659
a 0,669 em lotes bons, 0,028 a 0,038 em excursões. Essa constância é a propriedade que normalmente
se atribui à regra percentual, e ela pertence ao plano fixo.

## Resultado: um nível de qualidade aceitável é risco do produtor

O plano publicado clássico, `n=125, c=3`, citado como AQL 1,0%, num lote de mil:

| Defeituoso de entrada | Aceito | Qualidade média de saída |
| --- | --- | --- |
| 0,500% | 0,9989 | 0,00437 |
| 1,000% | **0,9732** | 0,00852 |
| 2,000% | 0,7668 | 0,01342 |
| 3,000% | **0,4713** | 0,01237 |
| 4,000% | 0,2408 | 0,00843 |
| 5,000% | 0,1077 | 0,00471 |

**No 1% citado o plano faz exatamente o que o nome diz — rejeita 2,7% dos lotes bons. No triplo
desse nível é cara ou coroa.** O número no nome do plano é o ponto em que o *produtor* está
protegido; o que o cliente recebe em qualquer outro nível é outro ponto da mesma curva, e nada no
nome se refere a ele.

A coluna de qualidade média de saída diz a outra metade: ela tem um **máximo**, em 2% de entrada. Um
plano não deixa a qualidade de saída melhor que a de entrada; ele a limita, e o limite não é zero.
Amostragem separa lotes. Não muda o que tem dentro deles.

## Resultado: aceitar zero defeituoso não é a opção rígida

"Rejeitar com um único defeituoso" soa como a regra mais apertada disponível, e no mesmo tamanho de
amostra é. Mas planos existem para deixar material bom passar, então a comparação que importa mantém
fixo o risco do produtor:

| Plano | Amostra | Rejeita lotes bons (1%) | Aceita lotes de 3% | Aceita lotes de 4% |
| --- | --- | --- | --- | --- |
| `n=125, c=3` | 125 | 2,7% | 47,1% | 24,1% |
| `c=0` casado no nível de 1% | **3** | 3,0% | **91,3%** | **88,5%** |
| `c=0` no mesmo tamanho de amostra | 125 | **73,9%** | 1,7% | 0,4% |

**Casar o risco do produtor do plano publicado com aceitação zero exige uma amostra de três, e esse
plano aceita 88,5% dos lotes que ele existe para pegar.** Suba a amostra de volta para 125 e a mesma
regra rejeita três quartos da produção boa. Não existe plano `c=0` que seja simultaneamente
tolerável no nível de aceitação e discriminante acima dele: o número de aceitação não é um botão de
rigor, e a discriminação de um plano vem do **tamanho da amostra**.

## Resultado: o que cada plano comprou

Duzentos lotes de mil unidades, um em cada dez uma excursão, 1.478 unidades defeituosas no total.
Cada plano aplicado aos mesmos lotes, com a amostra sorteada dos defeituosos que cada lote de fato
contém.

| Plano | Unidades inspecionadas | Excursões pegas | Lotes bons rejeitados | Unidades defeituosas expedidas |
| --- | --- | --- | --- | --- |
| 10% do lote, c=0 | 20.000 | **12/12** | **70** | 543 |
| n=125 c=3 (AQL 1,0%) | 25.000 | 9/12 | 0 | **1.098** |
| n=125 c=0 | 25.000 | 12/12 | 86 | 474 |
| n=3 c=0 (risco casado) | 600 | 2/12 | 4 | 1.383 |
| Desenhado para 1% vs 4% | 37.800 | **10/12** | **1** | 1.066 |
| Sem inspeção | 0 | 0/12 | 0 | 1.478 |

**O plano publicado inspeciona 25.000 unidades e expede três quartos dos defeitos.** Ele não
rejeita nenhum lote bom, que é o que foi desenhado para fazer, e perde um quarto das excursões.

**O plano que pega todas as excursões faz isso pondo em quarentena mais de um terço da produção
boa.** 70 lotes bons de 188 na regra percentual, 86 no `n=125 c=0`. Esses planos não são
discriminantes, são duros, e a diferença só aparece com as duas colunas na frente.

**Desenhar para os dois níveis de qualidade é a única linha boa nos dois**, e é a que custa mais
inspeção: 37.800 unidades para pegar 10 de 12 excursões rejeitando um lote bom. Essa é a troca, com
preço.

## Premissas e limitações

- **As contagens de excursão são uma realização; as probabilidades são exatas.** "12/12" e "9/12"
  vêm de uma passada com semente sobre 200 lotes e se moveriam em outra; as probabilidades de
  aceitação das tabelas acima são calculadas, não simuladas. Onde as duas discordarem, acredite nas
  probabilidades.
- **O `average_outgoing_quality` assume que lotes rejeitados são triados e corrigidos.** É inspeção
  *retificadora*, e muitas vezes não é o que acontece: onde lotes rejeitados voltam ao fornecedor, a
  cifra não descreve o que é expedido. A premissa está declarada no método porque normalmente fica
  implícita.
- **Todo plano aqui é de amostragem simples.** Planos duplos, múltiplos e sequenciais atingem os
  mesmos dois pontos de risco com amostra média menor, que é o argumento inteiro deles, e não estão
  implementados.
- **Sem regras de comutação.** Os esquemas publicados apertam após rejeições e afrouxam após uma
  sequência limpa, e é nessa comutação — não no plano individual — que está a maior parte da
  proteção deles. Um plano avaliado na própria curva é descrição justa de um plano e injusta de um
  esquema.
- **Lotes são assumidos homogêneos e amostrados aleatoriamente.** Um lote em que os defeituosos são
  a primeira hora do turno, amostrado do que está em cima do palete, não tem curva característica
  alguma. Essa é a premissa mais violada na prática e a que a aritmética não consegue detectar.
- **Defeituoso é binário e julgado corretamente.** O erro de medição da própria inspeção não é
  modelado aqui; o [`dmaic.measure`](../measure/README.md) está a montante deste documento inteiro,
  e um inspetor com 90% de concordância muda toda cifra dele.
- **Amostragem de aceitação não é controle de processo.** Um plano é um argumento sobre material já
  produzido. O que mantém o processo sob controle é carteado no pacote irmão `oplab.spc`, e nenhum
  plano de amostragem substitui isso.
