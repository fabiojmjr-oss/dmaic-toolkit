# `dmaic.analyze.compare` — assumptions, measured instead of assumed

*[Português](#dmaicanalyzecompare--premissas-medidas-em-vez-de-assumidas)*

## The business problem

Every Six Sigma course teaches the same flowchart. Test for normality. Test for equal variance.
Pick a test from what the two checks said.

Simulated against the truth, **that procedure is worse than skipping it** — and the sample sizes
where it is worst are the sample sizes improvement projects actually collect.

## The decision it enables

Which test to run, and — more usefully — whether the p-value it produces can carry the claim
being made from it. Both answered from measured error rates rather than from a decision tree.

## Usage

```python
from dmaic.analyze import compare_means, type_one_error_rates

result = compare_means(baseline, improved)
print(result.p_value, result.diagnosis())

# What your intended procedure's false-positive rate actually is, at your sample sizes:
type_one_error_rates(n_first=10, n_second=30, sd_first=3.0, sd_second=1.0)
```

## Result: what each procedure's false-positive rate really is

Both groups drawn with the same mean, so **every rejection is a type I error** and the nominal
rate is 5% by construction. 20,000 replications; Monte Carlo standard error about 0.0015.

| Scenario | pooled t | Welch | flowchart | Mann-Whitney |
| --- | --- | --- | --- | --- |
| normal, equal spread, n 20 / 20 | 0.0479 | 0.0477 | 0.0478 | 0.0481 |
| normal, spread 1:3, n 20 / 20 | 0.0540 | 0.0500 | 0.0500 | **0.0663** |
| normal, spread 1:3, n 10 / 30 | **0.0038** | 0.0478 | 0.0432 | 0.0150 |
| normal, spread 3:1, n 10 / 30 | **0.2130** | 0.0507 | **0.0628** | **0.1270** |
| skewed, equal spread, n 20 / 20 | 0.0435 | 0.0411 | 0.0425 | 0.0481 |
| skewed, spread 3:1, n 10 / 30 | **0.2331** | **0.1112** | **0.1454** | **0.2850** |

**The pooled t-test is wrong in both directions, and which one depends on bookkeeping.** With the
wider spread on the smaller group it fires at **21.30%** against a nominal 5%. Reverse which group
is which — same violated assumption, same ratio — and it collapses to **0.38%**, which throws away
almost all its power. Nothing about the process changed; only which group happened to be larger.

**Welch holds its level everywhere the data are normal**: 4.77%, 5.00%, 4.78%, 5.07%. Under equal
spread it costs essentially nothing against the pooled test (4.77% against 4.79%). There is no
scenario in this table where the pooled test earns the exposure.

**The flowchart is strictly worse than always using Welch.** 6.28% against 5.07% in the case that
matters. It inherits the pooled test's inflation whenever the variance pre-test happens not to
fire, which is often — a pre-test does not protect a procedure, it launders it. And the flowchart
is not *nearly* right: it is 26% over its nominal level while the thing it was chosen over is at
1%.

**Reaching for a rank test makes it worse.** Mann-Whitney is not a distribution-free version of
the t-test, it tests a different hypothesis, and unequal spread breaks it too: **6.63%** with
balanced groups and **12.70%** without. The reflex "not normal, so use the non-parametric test"
addresses the assumption that was not the problem.

**And nothing holds in the last row.** Skew, unequal spread and unequal sizes together give
11.12%, 14.54%, 23.31% and 28.50%. Picking the least bad is not a solution; the fix is a
different design.

## The normality test is least informative exactly where it matters most

Detection rate of Shapiro-Wilk against a real skew, and the true type I error of Welch's test, at
the same sample size on the same distribution. 4,000 replications.

| n per group | Shapiro-Wilk detects the skew | Welch's actual type I error |
| --- | --- | --- |
| 5 | **0.1633** | **0.0240** |
| 10 | 0.4348 | 0.0390 |
| 20 | 0.8033 | 0.0440 |
| 50 | 0.9978 | 0.0483 |
| 100 | 1.0000 | 0.0467 |
| 300 | 1.0000 | 0.0522 |

**The two columns move in opposite directions.** At five per group the check passes 84% of the
time — and that is where the test is most distorted, at 2.40% against a nominal 5%. At three
hundred the check fails every single time and sends the project to a rank test — and there the
t-test is already fine, at 5.22%. **The verdict is anti-correlated with the need for it.**

On genuinely normal data the detection rate comes out at 4.8%, 5.2% and 4.7% for n of 10, 50 and
300, which is the control: the instrument is calibrated, and the problem is the question it is
being asked.

## The diagnostic cannot see the thing that breaks the test

The standardised lognormal used above has a population skewness of **3.2629**. At ten observations
per group the algebraic maximum a sample skewness can reach is `(n−2)/√(n−1)` = **2.667** — the
estimator cannot report the truth even in principle.

| n | Mean sample skewness | Threshold to flag | Detection rate |
| --- | --- | --- | --- |
| 10 | 1.2073 | 1.374 | **0.3975** |
| 20 | 1.5886 | 1.024 | 0.7326 |
| 30 | 1.8045 | 1.000 | 0.8443 |
| 100 | 2.3779 | 1.000 | 0.9907 |
| 300 | 2.7777 | 1.000 | 0.9999 |

**The diagnostic's blind spot and the test's failure region are the same place.** At ten against
thirty with unequal spread the pooled test runs at 23.31% — and that is exactly the sample size
where a population skewness of 3.26 is detected 39.8% of the time by an estimator that is bounded
below the true value. This is not a coincidence: both are consequences of small n.

**And the spread diagnostic fails in the same regime, for the same reason.** On a skewed
population the sample standard deviation is itself wild. Drawn from a true spread ratio of exactly
3.00 at ten against thirty observations, the *sample* ratio has a median of 2.601 and a middle 90%
running from **1.152 to 6.762** — so a real 3:1 inequality reads as near-parity about as often as
it reads as 6:1.

Both inputs to the regime flag are therefore unreliable precisely where the flag is needed, and
the flag itself recognises the bad regime **75.0% of the time**: the skew half fires on 90.0% of
draws, the spread half on 84.3%, and both together on 75.0%. It misses one case in four. That is
the honest limit of a diagnostic read off forty observations, and it is why `strict=True` is
documented below as a blunt instrument rather than a safeguard.

So `compare_means` runs Welch unconditionally, returns the checks as **evidence rather than as a
gate**, and flags the regime where nothing holds. Gating on a diagnostic that cannot see the
problem is the flowchart's mistake, not its implementation detail.

## Result: four comparisons, and the two the diagnostic gets wrong

Two are drawn under the null — identical group means — so a significant result on those is a
false positive that can be named rather than argued about.

| Comparison | True difference | Spread ratio | Size ratio | pooled p | Welch p | Ratio |
| --- | --- | --- | --- | --- | --- | --- |
| `TURNO-A vs TURNO-B` | 0.0 | 1.28 | 1.0 | 0.6306 | 0.6307 | 1.0× |
| `LINHA-1 vs LINHA-2` | 0.0 | 2.30 | 3.0 | 0.5724 | 0.7001 | 1.2× |
| `CELULA-X vs CELULA-Y` | 0.0 | 2.25 | 3.0 | 0.8357 | 0.7678 | 0.9× |
| `FORN-X vs FORN-Y` | −2.0 | 3.50 | 3.0 | **0.0019** | **0.0657** | **34.6×** |

**`FORN-X vs FORN-Y` is the case worth sitting with.** The pooled test returns `p = 0.0019` and
Welch returns `p = 0.0657` on the same forty observations — a factor of **34.6**. One declares a
highly significant result; the other declines to reject at 5%. And there *is* a real difference of
−2.0 days, so the pooled test reached the right answer.

It did not earn it. The simulation above puts that procedure at 23.31% false positives in this
exact regime, which means it would have been just as confident with no difference at all. A single
sample cannot distinguish a test that is right from a test that is loud, and that is the whole
reason the error rates are measured rather than reasoned about.

**And the diagnostic gets one false alarm and one miss out of four.** `LINHA-2` is drawn from a
normal population and its sample skewness came out at −1.267 on 36 observations, which clears the
threshold and flags the comparison as unreliable — a draw in the 1.4% tail, read correctly as
skew that is not there. `FORN-X` is drawn from a population with skewness 3.26 and its sample
skewness came out at 1.075 on 10 observations, which does not clear the threshold at that size —
the real thing, missed.

One in each direction, on a diagnostic doing its best with the data available. That is the
empirical case for not gating on it.

## Assumptions and limitations

- **The simulation answers about the distributions it draws from.** Normal and a standardised
  lognormal. Heavy tails without skew, bimodality, and rounding to a coarse gauge are all real
  and none are covered; a project whose data look like none of these should run
  `type_one_error_rates` with its own shape rather than reading this table.
- **`compare_means` compares means, and Welch's test is about means.** Where the interesting
  question is a median, a quantile or a rate of defectives, this is the wrong tool and a correct
  p-value from it answers something nobody asked.
- **Mann-Whitney is measured here but not offered as an API.** Wrapping it alongside
  `compare_means` would invite exactly the substitution the simulation argues against. Where the
  hypothesis genuinely is stochastic dominance, `scipy.stats.mannwhitneyu` is one import away and
  the caller should reach for it deliberately.
- **The regime flag is a heuristic read off two ratios and a bounded estimator.** It is not a
  test, it has no error rate of its own, and the four comparisons above show it failing in both
  directions. It is offered as a prompt to think, not as a gate — which is the same standard this
  module holds the flowchart to.
- **`strict=True` raises on the unreliable regime, and that is a blunt instrument.** It will
  refuse comparisons that would have been fine and permit some that will not be, for the reasons
  in the row above. The default returns the result with the flag set, because a caller who reads
  the flag is better served than one whose pipeline crashed.
- **None of this addresses multiplicity.** Four comparisons at 5% are not four independent 5%
  risks, and nothing here adjusts for how many were run.
- **A held error rate is not a correct conclusion.** Welch holding 5% says the test will not
  manufacture findings; it says nothing about whether the difference it finds is worth acting on.
  That is `detectable_difference` and the effect size, in the sibling module.

---

# `dmaic.analyze.compare` — premissas medidas em vez de assumidas

*[English](#dmaicanalyzecompare--assumptions-measured-instead-of-assumed)*

## O problema de negócio

Todo curso de Six Sigma ensina o mesmo fluxograma. Testar normalidade. Testar igualdade de
variâncias. Escolher o teste conforme o que os dois checks disseram.

Simulado contra a verdade, **esse procedimento é pior que pular os checks** — e os tamanhos de
amostra em que ele é pior são exatamente os que projetos de melhoria coletam.

## A decisão que ele habilita

Qual teste rodar e — mais útil — se o p-valor que ele produz sustenta a afirmação que está sendo
feita a partir dele. Ambas respondidas por taxas de erro medidas, não por árvore de decisão.

## Uso

```python
from dmaic.analyze import compare_means, type_one_error_rates

result = compare_means(baseline, improved)
print(result.p_value, result.diagnosis())

# Qual é de fato a taxa de falso positivo do procedimento pretendido, no seu tamanho de amostra:
type_one_error_rates(n_first=10, n_second=30, sd_first=3.0, sd_second=1.0)
```

## Resultado: a taxa real de falso positivo de cada procedimento

Os dois grupos sorteados com a mesma média, então **toda rejeição é erro tipo I** e a taxa nominal
é 5% por construção. 20.000 réplicas; erro padrão de Monte Carlo cerca de 0,0015.

| Cenário | t agrupado | Welch | fluxograma | Mann-Whitney |
| --- | --- | --- | --- | --- |
| normal, dispersão igual, n 20 / 20 | 0,0479 | 0,0477 | 0,0478 | 0,0481 |
| normal, dispersão 1:3, n 20 / 20 | 0,0540 | 0,0500 | 0,0500 | **0,0663** |
| normal, dispersão 1:3, n 10 / 30 | **0,0038** | 0,0478 | 0,0432 | 0,0150 |
| normal, dispersão 3:1, n 10 / 30 | **0,2130** | 0,0507 | **0,0628** | **0,1270** |
| assimétrica, dispersão igual, n 20 / 20 | 0,0435 | 0,0411 | 0,0425 | 0,0481 |
| assimétrica, dispersão 3:1, n 10 / 30 | **0,2331** | **0,1112** | **0,1454** | **0,2850** |

**O t agrupado erra nas duas direções, e qual delas depende de contabilidade.** Com a dispersão
maior no grupo menor, ele dispara a **21,30%** contra um nominal de 5%. Inverta qual grupo é qual
— mesma premissa violada, mesma razão — e ele desaba para **0,38%**, jogando fora quase todo o
poder. Nada no processo mudou; só qual grupo por acaso era o maior.

**O Welch mantém o nível em todo dado normal**: 4,77%, 5,00%, 4,78%, 5,07%. Sob dispersão igual
ele não custa praticamente nada contra o agrupado (4,77% contra 4,79%). Não há cenário nesta tabela
em que o teste agrupado valha a exposição.

**O fluxograma é estritamente pior que sempre usar Welch.** 6,28% contra 5,07% no caso que importa.
Ele herda a inflação do agrupado sempre que o pré-teste de variância não dispara, o que acontece
com frequência — um pré-teste não protege um procedimento, ele o lava. E o fluxograma não fica
*quase* certo: fica 26% acima do nível nominal enquanto a alternativa que ele preteriu fica a 1%.

**Recorrer a um teste de postos piora.** Mann-Whitney não é uma versão livre de distribuição do
teste t, ele testa outra hipótese, e dispersão desigual o quebra também: **6,63%** com grupos
balanceados e **12,70%** sem. O reflexo "não é normal, então use o não-paramétrico" trata a
premissa que não era o problema.

**E nada se sustenta na última linha.** Assimetria, dispersão desigual e tamanhos desiguais juntos
dão 11,12%, 14,54%, 23,31% e 28,50%. Escolher o menos ruim não é solução; a correção é outro
desenho.

## O teste de normalidade é menos informativo exatamente onde mais importa

Taxa de detecção do Shapiro-Wilk contra uma assimetria real, e o erro tipo I verdadeiro do teste
de Welch, no mesmo tamanho de amostra e na mesma distribuição. 4.000 réplicas.

| n por grupo | Shapiro-Wilk detecta a assimetria | Erro tipo I real do Welch |
| --- | --- | --- |
| 5 | **0,1633** | **0,0240** |
| 10 | 0,4348 | 0,0390 |
| 20 | 0,8033 | 0,0440 |
| 50 | 0,9978 | 0,0483 |
| 100 | 1,0000 | 0,0467 |
| 300 | 1,0000 | 0,0522 |

**As duas colunas andam em direções opostas.** Em cinco por grupo o check aprova 84% das vezes — e
é ali que o teste está mais distorcido, a 2,40% contra um nominal de 5%. Em trezentos o check
reprova todas as vezes e manda o projeto para um teste de postos — e ali o teste t já está perfeito,
a 5,22%. **O veredito é anticorrelacionado com a necessidade dele.**

Em dado genuinamente normal a taxa de detecção sai em 4,8%, 5,2% e 4,7% para n de 10, 50 e 300,
que é o controle: o instrumento está calibrado, e o problema é a pergunta que se faz a ele.

## O diagnóstico não consegue ver o que quebra o teste

A lognormal padronizada usada acima tem assimetria populacional de **3,2629**. Em dez observações
por grupo, o máximo algébrico que uma assimetria amostral pode atingir é `(n−2)/√(n−1)` =
**2,667** — o estimador não consegue reportar a verdade nem em princípio.

| n | Assimetria amostral média | Limiar para disparar | Taxa de detecção |
| --- | --- | --- | --- |
| 10 | 1,2073 | 1,374 | **0,3975** |
| 20 | 1,5886 | 1,024 | 0,7326 |
| 30 | 1,8045 | 1,000 | 0,8443 |
| 100 | 2,3779 | 1,000 | 0,9907 |
| 300 | 2,7777 | 1,000 | 0,9999 |

**O ponto cego do diagnóstico e a região de falha do teste são o mesmo lugar.** Em dez contra
trinta com dispersão desigual o teste agrupado roda a 23,31% — e é exatamente o tamanho de amostra
em que uma assimetria populacional de 3,26 é detectada 39,8% das vezes por um estimador limitado
abaixo do valor verdadeiro. Não é coincidência: as duas coisas são consequência de n pequeno.

**E o diagnóstico de dispersão falha no mesmo regime, pelo mesmo motivo.** Em população
assimétrica o desvio-padrão amostral é ele mesmo instável. Sorteado de uma razão populacional de
exatamente 3,00 em dez contra trinta observações, a razão *amostral* tem mediana 2,601 e 90%
central indo de **1,152 a 6,762** — ou seja, uma desigualdade real de 3:1 se lê como quase-paridade
com frequência parecida com a que se lê como 6:1.

Os dois insumos da sinalização de regime são portanto pouco confiáveis exatamente onde ela é
necessária, e a sinalização reconhece o regime ruim **75,0% das vezes**: a metade de assimetria
dispara em 90,0% dos sorteios, a de dispersão em 84,3%, e as duas juntas em 75,0%. Erra um caso em
quatro. Esse é o limite honesto de um diagnóstico lido sobre quarenta observações, e é por isso que
o `strict=True` está documentado abaixo como instrumento grosseiro e não como salvaguarda.

Por isso o `compare_means` roda Welch sem condição, devolve os checks como **evidência e não como
portão**, e sinaliza o regime em que nada se sustenta. Condicionar a decisão a um diagnóstico que
não consegue ver o problema é o erro do fluxograma, não um detalhe de implementação dele.

## Resultado: quatro comparações, e as duas que o diagnóstico erra

Duas são sorteadas sob a hipótese nula — médias de grupo idênticas — então resultado significativo
nelas é falso positivo que pode ser nomeado em vez de discutido.

| Comparação | Diferença real | Razão de dispersão | Razão de tamanho | p agrupado | p Welch | Razão |
| --- | --- | --- | --- | --- | --- | --- |
| `TURNO-A vs TURNO-B` | 0,0 | 1,28 | 1,0 | 0,6306 | 0,6307 | 1,0× |
| `LINHA-1 vs LINHA-2` | 0,0 | 2,30 | 3,0 | 0,5724 | 0,7001 | 1,2× |
| `CELULA-X vs CELULA-Y` | 0,0 | 2,25 | 3,0 | 0,8357 | 0,7678 | 0,9× |
| `FORN-X vs FORN-Y` | −2,0 | 3,50 | 3,0 | **0,0019** | **0,0657** | **34,6×** |

**O `FORN-X vs FORN-Y` é o caso para se demorar.** O teste agrupado devolve `p = 0,0019` e o Welch
devolve `p = 0,0657` nas mesmas quarenta observações — um fator de **34,6**. Um declara resultado
altamente significativo; o outro se recusa a rejeitar a 5%. E existe uma diferença real de −2,0
dias, então o teste agrupado chegou à resposta certa.

Ele não a mereceu. A simulação acima põe esse procedimento em 23,31% de falsos positivos neste
regime exato, o que significa que ele teria a mesma confiança sem diferença alguma. Uma amostra
única não distingue um teste que está certo de um teste que está alto, e é essa a razão inteira de
as taxas de erro serem medidas em vez de argumentadas.

**E o diagnóstico erra um falso alarme e uma omissão em quatro.** O `LINHA-2` vem de população
normal e sua assimetria amostral saiu em −1,267 sobre 36 observações, o que cruza o limiar e
sinaliza a comparação como não confiável — um sorteio na cauda de 1,4%, lido corretamente como
assimetria que não existe. O `FORN-X` vem de população com assimetria 3,26 e sua assimetria
amostral saiu em 1,075 sobre 10 observações, o que não cruza o limiar nesse tamanho — a coisa real,
perdida.

Uma em cada direção, num diagnóstico fazendo o melhor com o dado disponível. É esse o argumento
empírico para não condicionar a decisão a ele.

## Premissas e limitações

- **A simulação responde sobre as distribuições de que ela sorteia.** Normal e uma lognormal
  padronizada. Caudas pesadas sem assimetria, bimodalidade e arredondamento a um instrumento
  grosseiro são todos reais e nenhum está coberto; um projeto cujo dado não se parece com nenhum
  desses deve rodar o `type_one_error_rates` com a própria forma, não ler esta tabela.
- **O `compare_means` compara médias, e o teste de Welch é sobre médias.** Onde a pergunta
  interessante é uma mediana, um quantil ou uma taxa de defeituosos, esta é a ferramenta errada, e
  um p-valor correto dela responde algo que ninguém perguntou.
- **Mann-Whitney é medido aqui mas não oferecido como API.** Envolvê-lo ao lado do `compare_means`
  convidaria exatamente a substituição contra a qual a simulação argumenta. Onde a hipótese
  genuinamente é dominância estocástica, o `scipy.stats.mannwhitneyu` está a um import de distância
  e quem chama deve buscá-lo deliberadamente.
- **A sinalização de regime é heurística, lida de duas razões e de um estimador limitado.** Não é
  teste, não tem taxa de erro própria, e as quatro comparações acima mostram ela falhando nas duas
  direções. É oferecida como provocação para pensar, não como portão — que é o mesmo padrão com que
  este módulo cobra o fluxograma.
- **`strict=True` levanta erro no regime não confiável, e é instrumento grosseiro.** Vai recusar
  comparações que estariam bem e permitir algumas que não estarão, pelos motivos da linha acima. O
  padrão devolve o resultado com a sinalização marcada, porque quem lê a sinalização é melhor
  servido que quem teve o pipeline derrubado.
- **Nada disso trata multiplicidade.** Quatro comparações a 5% não são quatro riscos independentes
  de 5%, e nada aqui ajusta por quantas foram rodadas.
- **Nível de erro mantido não é conclusão correta.** O Welch manter 5% diz que o teste não vai
  fabricar achados; não diz nada sobre a diferença encontrada valer ação. Isso é a
  `detectable_difference` e o tamanho de efeito, no módulo irmão.
