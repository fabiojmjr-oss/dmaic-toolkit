# `dmaic.measure` — accuracy: is the gage right?

*[Português](#dmaicmeasure--exatidão-o-gage-está-certo)*

## The business problem

A gage study passes. Percent study variation is 6.29, percent tolerance 5.69, ndc is 22, and the
report says *acceptable*. Every later number in the project is computed on that gage's readings,
and the gage weighs **4 g heavy on every part**.

Nothing in the study was done wrong. The study is incapable of seeing it.

## Why it cannot

Repeatability, reproducibility and part variation are all computed from differences between
readings. Adding a constant to every reading in a study leaves every difference untouched, so
every figure the study produces is **invariant to bias** — not insensitive, invariant. Shifting
all three synthetic gages by 1000 units moves the largest of `grr`, `pct_study`,
`pct_contribution`, `pct_tolerance` and `ndc` by at most **9.2e-12**, which is floating-point
noise rather than a small effect.

That is a property of the question, not a flaw in the method. "Can this gage tell the parts
apart?" and "is this gage right?" are different questions, and the second needs a value from
outside the study: a calibrated master.

## The decision it enables

1. **Can this gage be used as it stands, or does it need calibrating first?** A bias is cheap to
   remove and expensive to leave. The study that passed the gage does not distinguish the two
   states.
2. **Can a check at one point stand in for the range?** Only if the offset is the same
   everywhere, which is exactly what a one-point check cannot establish.
3. **If it cannot be fixed now, what does using it cost?** In conforming parts scrapped and
   nonconforming parts shipped, which is the only form of the answer a plant can act on.

## Usage

```python
from dmaic.measure import bias_study, guard_band, linearity_study, misclassification

bias = bias_study(readings_at_nominal, reference=500.0, tolerance=50.0)
bias.bias, bias.pct_tolerance, bias.significant, bias.material  # two findings, not one
bias.detectable_bias  # what a study this size could have found

linearity_study(all_readings, tolerance=50.0).pct_tolerance_span  # 17.64 on PAQUIMETRO-02

misclassification(
    bias=3.9076, gage_sd=0.4743, part_sd=8.0, nominal=500.0, lsl=475.0, usl=525.0
).verdict()
```

## Result

The same three gages as the crossed study, now measured against five calibrated masters each,
twelve readings per master. The generator declares the offset it built in, so a study that finds
nothing on `INSPECAO-03` is a correct answer rather than a miss.

| Gage | Crossed study | Bias at nominal | p | % of tolerance | Linearity slope | Bias span | Span % of tolerance |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `BALANCA-01` | **acceptable**, 5.69% tol | **3.9076 g** | 0.0000 | **7.82** | 0.0011 | 0.0456 | 0.09 |
| `PAQUIMETRO-02` | unacceptable, 63.58% tol | 0.0058 mm | 0.7113 | 0.58 | **−0.2205** | **0.1764 mm** | **17.64** |
| `INSPECAO-03` | unacceptable, 62.55% tol | −0.0521 µm | 0.8721 | 0.13 | −0.0132 | 0.4231 | 1.06 |

**Precision and accuracy are independent, and all three gages prove a different corner of it.**

- `BALANCA-01` **passes the crossed study and is the worst gage of the three**. Its bias is 7.82%
  of the tolerance against the 5.69% the whole GRR study measured — the error nobody looked for is
  larger than the error everybody computed.
- `PAQUIMETRO-02` has **no bias at nominal at all** — 0.58% of tolerance, p = 0.71, and the
  one-point check that every procedure prescribes passes it. Across the range the offset runs from
  one end to the other by 0.1764 mm, **17.64% of the tolerance**, in opposite directions at the
  two specification limits. Averaging bias over a range is how a gage with two large errors
  reports none.
- `INSPECAO-03` **fails the crossed study and is accurate**. Bias 0.13% of tolerance, no slope.
  "The gage is bad, recalibrate it" — the commonest response to a failed study — would change
  nothing here, which is what wave 1's split of GRR into repeatability and reproducibility already
  said in different units.

## What the bias costs

`BALANCA-01` again: process standard deviation 8.0 g against a 50 g tolerance, so 99.8222% of
production genuinely conforms, and the gage's own sigma is 0.4743.

| Case | Bias | Guard band | Good parts scrapped | Bad parts shipped |
| --- | --- | --- | --- | --- |
| Calibrated | 0.0000 | — | 161 ppm | 128 ppm |
| **As found** | 3.9076 | — | **3,356 ppm** | **734 ppm** |
| As found, guard banded | 3.9076 | 3.5890 | **13,618 ppm** | 128 ppm |

**The bias multiplies scrap by 20.8 and escapes by 5.7**, on a gage whose study said *acceptable*.

**And the workaround is far worse than the fix.** Tightening the acceptance limits by 3.5890 g
brings the escape rate exactly back to where a calibrated gage would put it — and pays for it by
discarding 13,618 ppm of conforming parts, **84.5 times** the calibrated scrap rate, or 1.36% of
everything produced. A calibration removes the bias and costs neither number. That comparison is
the argument for measuring bias at all: without it, the guard band looks like diligence.

## "The interval contains zero" is not an acceptance rule

The standard criterion is that the confidence interval on the bias should contain zero. What that
criterion actually tests is the ratio of the bias to the gage's own repeatability, and nothing
else. Hold the bias fixed at 0.5 g — 1% of a 50 g tolerance, below any materiality convention —
and vary only the gage's precision, over 4,000 simulated twelve-reading studies per row:

| Gage repeatability | 6σ as % of tolerance | Bias ÷ sd | Called significant | Actually material |
| --- | --- | --- | --- | --- |
| 0.20 | 2.40 | 2.5000 | **1.0000** | no |
| 0.56 | 6.72 | 0.8929 | 0.7983 | no |
| 1.50 | 18.00 | 0.3333 | 0.1893 | no |
| 4.00 | 48.00 | 0.1250 | **0.0717** | no |

**The better the gage, the more certainly it is rejected for an offset that does not matter — and
the worse the gage, the more easily it passes.** The verdict is driven by the gage's precision
rather than by the consequence of the bias, which is the wrong way round for an acceptance rule,
and the same anti-correlation with usefulness that
[`dmaic.analyze`](../analyze/README-compare.md) measures in the normality pre-test.

`BiasStudy` therefore reports `significant` and `material` as two separate findings and its
`verdict()` names both, including the uncomfortable combination: an offset that matters and a
study too small to establish it.

## Assumptions and limitations

- **The masters are exact here and are not anywhere else.** A reference study measures the
  difference between two measurement systems and attributes all of it to the one being studied.
  A master with its own uncertainty puts a floor under the bias you can claim, and nothing in
  this module knows about that floor. In practice the master should be several times better than
  the gage, and "several times" is the assumption doing the work.
- **`misclassification` assumes one constant bias.** For `BALANCA-01` that is exactly right and
  for `PAQUIMETRO-02` it is not: a non-linear gage has a different offset at each specification
  limit, so it has to be evaluated at each limit separately rather than with an average. Feeding
  a mean bias to this function is the same averaging error the linearity study exists to catch.
- **It also assumes a normal process and a normal measurement error, and that the two are
  independent.** A gage whose spread grows with the reading breaks the integral, and a skewed
  process moves both rates - the escape rate especially, since it is a statement about the tails.
- **The ppm figures are rates, not costs.** A scrapped good part and a shipped bad one are not
  worth the same, and almost never within an order of magnitude of each other. Multiplying the
  two rates by their own consequences is the caller's decision and this module does not hide one
  inside the other.
- **Bias, linearity and stability are three properties and only two are here.** A gage that is
  accurate today and drifts is not covered: a reference study run inside one session cannot see
  drift, and its repeatability then understates what the gage will do over a month. The duration
  of a study is a parameter of its answer and appears nowhere on the form.
- **A one-point bias study is well powered for its own repeatability and that is not the same as
  being adequate.** Twelve readings on `BALANCA-01` detect 0.3646 g, 0.73% of tolerance. The
  study's problem was never power; it was that it only looked at one point.
- **Nothing here corrects a reading.** Knowing the bias is 3.9076 g means subtracting 3.9076 is
  tempting, and subtracting an *estimate* from every future reading adds that estimate's own
  uncertainty to every one of them. Calibration and correction are different actions.

---

# `dmaic.measure` — exatidão: o gage está certo?

*[English](#dmaicmeasure--accuracy-is-the-gage-right)*

## O problema de negócio

Um estudo de gage aprova. A variação do estudo é 6,29%, a %tolerância 5,69, o ndc é 22, e o
relatório diz *aceitável*. Todo número posterior do projeto é calculado sobre as leituras desse
gage, e o gage pesa **4 g acima em toda peça**.

Nada no estudo foi feito errado. O estudo é incapaz de ver isso.

## Por que não consegue

Repetibilidade, reprodutibilidade e variação das peças são todas calculadas a partir de diferenças
entre leituras. Somar uma constante a toda leitura de um estudo deixa toda diferença intacta,
então toda figura que o estudo produz é **invariante ao viés** — não pouco sensível, invariante.
Deslocar os três gages sintéticos em 1000 unidades move a maior entre `grr`, `pct_study`,
`pct_contribution`, `pct_tolerance` e `ndc` em no máximo **9,2e-12**, que é ruído de ponto
flutuante e não um efeito pequeno.

Isso é propriedade da pergunta, não falha do método. "Este gage consegue distinguir as peças?" e
"este gage está certo?" são perguntas diferentes, e a segunda precisa de um valor de fora do
estudo: um padrão calibrado.

## A decisão que ele habilita

1. **Este gage pode ser usado como está, ou precisa ser calibrado antes?** Um viés é barato de
   remover e caro de deixar. O estudo que aprovou o gage não distingue os dois estados.
2. **Uma verificação em um ponto substitui a faixa?** Só se o desvio for o mesmo em todo lugar, o
   que é exatamente o que uma verificação em um ponto não consegue estabelecer.
3. **Se não der para consertar agora, quanto custa usar?** Em peças conformes refugadas e peças
   não conformes expedidas, que é a única forma da resposta sobre a qual uma planta age.

## Uso

```python
from dmaic.measure import bias_study, guard_band, linearity_study, misclassification

vies = bias_study(leituras_no_nominal, reference=500.0, tolerance=50.0)
vies.bias, vies.pct_tolerance, vies.significant, vies.material  # dois achados, não um
vies.detectable_bias  # o que um estudo deste tamanho conseguiria achar

linearity_study(todas_as_leituras, tolerance=50.0).pct_tolerance_span  # 17,64 no PAQUIMETRO-02

misclassification(
    bias=3.9076, gage_sd=0.4743, part_sd=8.0, nominal=500.0, lsl=475.0, usl=525.0
).verdict()
```

## Resultado

Os mesmos três gages do estudo cruzado, agora medidos contra cinco padrões calibrados cada, doze
leituras por padrão. O gerador declara o desvio que embutiu, então um estudo que não acha nada no
`INSPECAO-03` é resposta correta e não falha.

| Gage | Estudo cruzado | Viés no nominal | p | % da tolerância | Inclinação | Amplitude do viés | Amplitude % da tolerância |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `BALANCA-01` | **aceitável**, 5,69% tol | **3,9076 g** | 0,0000 | **7,82** | 0,0011 | 0,0456 | 0,09 |
| `PAQUIMETRO-02` | inaceitável, 63,58% tol | 0,0058 mm | 0,7113 | 0,58 | **−0,2205** | **0,1764 mm** | **17,64** |
| `INSPECAO-03` | inaceitável, 62,55% tol | −0,0521 µm | 0,8721 | 0,13 | −0,0132 | 0,4231 | 1,06 |

**Precisão e exatidão são independentes, e cada um dos três gages prova um canto diferente
disso.**

- O `BALANCA-01` **passa no estudo cruzado e é o pior gage dos três**. O viés dele é 7,82% da
  tolerância contra os 5,69% que o estudo de GRR inteiro mediu — o erro que ninguém procurou é
  maior que o erro que todos calcularam.
- O `PAQUIMETRO-02` **não tem viés nenhum no nominal** — 0,58% da tolerância, p = 0,71, e a
  verificação em um ponto que todo procedimento prescreve o aprova. Ao longo da faixa o desvio
  corre de uma ponta à outra em 0,1764 mm, **17,64% da tolerância**, em direções opostas nos dois
  limites de especificação. Tirar média de viés ao longo de uma faixa é como um gage com dois
  erros grandes reporta nenhum.
- O `INSPECAO-03` **reprova no estudo cruzado e é exato**. Viés de 0,13% da tolerância, sem
  inclinação. "O gage é ruim, recalibra" — a resposta mais comum a um estudo reprovado — não
  mudaria nada aqui, que é o que a separação do GRR em repetibilidade e reprodutibilidade da onda
  1 já dizia em outras unidades.

## Quanto o viés custa

`BALANCA-01` de novo: desvio-padrão do processo de 8,0 g contra uma tolerância de 50 g, então
99,8222% da produção é genuinamente conforme, e o sigma do próprio gage é 0,4743.

| Caso | Viés | Banda de guarda | Peças boas refugadas | Peças ruins expedidas |
| --- | --- | --- | --- | --- |
| Calibrado | 0,0000 | — | 161 ppm | 128 ppm |
| **Como encontrado** | 3,9076 | — | **3.356 ppm** | **734 ppm** |
| Como encontrado, com banda | 3,9076 | 3,5890 | **13.618 ppm** | 128 ppm |

**O viés multiplica o refugo por 20,8 e os escapes por 5,7**, num gage cujo estudo disse
*aceitável*.

**E o paliativo é muito pior que a correção.** Apertar os limites de aceitação em 3,5890 g traz a
taxa de escape exatamente de volta ao que um gage calibrado daria — e paga por isso descartando
13.618 ppm de peças conformes, **84,5 vezes** a taxa de refugo calibrada, ou 1,36% de tudo que é
produzido. Uma calibração remove o viés e não custa nenhum dos dois números. Essa comparação é o
argumento para medir viés: sem ela, a banda de guarda parece diligência.

## "O intervalo contém zero" não é regra de aceitação

O critério padrão é que o intervalo de confiança do viés contenha zero. O que esse critério de
fato testa é a razão entre o viés e a repetibilidade do próprio gage, e nada mais. Mantenha o viés
fixo em 0,5 g — 1% de uma tolerância de 50 g, abaixo de qualquer convenção de materialidade — e
varie apenas a precisão do gage, em 4.000 estudos simulados de doze leituras por linha:

| Repetibilidade do gage | 6σ como % da tolerância | Viés ÷ sd | Chamado significativo | Material de fato |
| --- | --- | --- | --- | --- |
| 0,20 | 2,40 | 2,5000 | **1,0000** | não |
| 0,56 | 6,72 | 0,8929 | 0,7983 | não |
| 1,50 | 18,00 | 0,3333 | 0,1893 | não |
| 4,00 | 48,00 | 0,1250 | **0,0717** | não |

**Quanto melhor o gage, mais certamente ele é reprovado por um desvio que não importa — e quanto
pior o gage, mais facilmente ele passa.** O veredito é conduzido pela precisão do gage e não pela
consequência do viés, o que é o inverso do que uma regra de aceitação precisa, e é a mesma
anticorrelação com a utilidade que o [`dmaic.analyze`](../analyze/README-compare.md) mede no
pré-teste de normalidade.

Por isso o `BiasStudy` reporta `significant` e `material` como os dois achados separados que são,
e o `verdict()` nomeia os dois, inclusive a combinação incômoda: um desvio que importa e um estudo
pequeno demais para estabelecê-lo.

## Premissas e limitações

- **Os padrões aqui são exatos e em nenhum outro lugar são.** Um estudo de referência mede a
  diferença entre dois sistemas de medição e atribui tudo ao que está sendo estudado. Um padrão
  com incerteza própria põe um piso no viés que se pode alegar, e nada neste módulo conhece esse
  piso. Na prática o padrão deve ser várias vezes melhor que o gage, e "várias vezes" é a premissa
  que faz o trabalho.
- **O `misclassification` assume um viés constante.** Para o `BALANCA-01` isso é exatamente certo
  e para o `PAQUIMETRO-02` não é: um gage não linear tem desvio diferente em cada limite de
  especificação, então tem de ser avaliado limite por limite em vez de com uma média. Alimentar
  esta função com um viés médio é o mesmo erro de média que o estudo de linearidade existe para
  pegar.
- **Ele também assume processo normal, erro de medição normal e independência entre os dois.** Um
  gage cuja dispersão cresce com a leitura quebra a integral, e um processo assimétrico move as
  duas taxas — a de escape especialmente, porque é uma afirmação sobre as caudas.
- **As cifras em ppm são taxas, não custos.** Uma peça boa refugada e uma ruim expedida não valem
  o mesmo, e quase nunca estão na mesma ordem de grandeza. Multiplicar cada taxa pela consequência
  dela é decisão de quem chama, e este módulo não esconde uma dentro da outra.
- **Viés, linearidade e estabilidade são três propriedades e só duas estão aqui.** Um gage exato
  hoje que deriva não está coberto: um estudo de referência rodado dentro de uma sessão não vê
  deriva, e a repetibilidade dele passa a subestimar o que o gage fará ao longo de um mês. A
  duração de um estudo é parâmetro da resposta dele e não aparece em lugar nenhum do formulário.
- **Um estudo de viés em um ponto tem poder de sobra para a própria repetibilidade, e isso não é o
  mesmo que ser adequado.** Doze leituras no `BALANCA-01` detectam 0,3646 g, 0,73% da tolerância.
  O problema do estudo nunca foi poder; foi olhar só um ponto.
- **Nada aqui corrige uma leitura.** Saber que o viés é 3,9076 g torna tentador subtrair 3,9076, e
  subtrair uma *estimativa* de toda leitura futura adiciona a incerteza dessa estimativa a cada
  uma delas. Calibrar e corrigir são ações diferentes.
