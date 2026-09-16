# `dmaic.analyze` — power and sample size

*[Português](#dmaicanalyze--poder-e-tamanho-de-amostra)*

## The business problem

An improvement project runs a pilot, tests the result, gets `p = 0.23`, and is closed as "no
significant improvement". The write-up is honest, the arithmetic is correct, and the conclusion
can still be wrong — because a non-significant p-value looks exactly the same whether the effect
is absent or merely smaller than the study could ever have seen.

That failure is not detectable from the output. It is entirely predictable beforehand, and almost
never computed.

## The decision it enables

Two decisions, and the order matters:

1. **Before the pilot: how much data do I need?** Not "how much can I collect" — the sample size
   is what fixes the conclusion for every effect below the detection limit, so choosing it by
   convenience is choosing the answer.
2. **After a non-significant pilot: what did this study rule out?** The honest output is not the
   p-value, it is the **detectable difference**: the smallest effect the study could have found.
   Anything below it was never in reach.

## Usage

```python
from dmaic.analyze import detectable_difference, power_two_means, sample_size_two_means

power_two_means(n_per_group=30, delta=4.0, sd=12.0)  # 0.2456 - it will miss 3 times in 4
detectable_difference(n_per_group=30, sd=12.0)  # 8.83 - nothing smaller was in reach
sample_size_two_means(delta=4.0, sd=12.0)  # n=143 per group, power 0.8021
```

## Result

Three pilots from the synthetic dataset, each sized the way projects are actually sized — from
what was convenient to collect. The generator declares the effect it put in, which is the whole
advantage of synthetic data here: a real project cannot tell a missed effect from an absent one.

| Trial | Observed effect | True effect | p-value | Power for the true effect | n run | n needed |
| --- | --- | --- | --- | --- | --- | --- |
| `PILOTO-CICLO` | −0.29 min | −4.00 min | 0.9234 | **0.2456** | 30 | 143 |
| `PILOTO-SETUP` | −2.77 min | −6.00 min | 0.2345 | 0.7905 | 5 | 6 |
| `PILOTO-REFUGO` | −3.50 pts | −2.50 pts | 0.2152 | **0.1702** | 200 | **1,568** |

**All three are non-significant. All three had a real effect.** Three type II errors in a row,
and every one of them would be written up as "no improvement demonstrated". What makes them worth
reading together is that each fails for a different reason.

**`PILOTO-CICLO` was hopelessly underpowered and then unlucky on top.** At 30 per arm it had a
24.6% chance of finding its own 4-minute effect, and it happened to observe −0.29. A p-value of
0.9234 reads as overwhelming evidence of no effect and is nothing of the kind: the study's
detectable difference was **8.83 minutes**, so a 4-minute improvement was outside its reach from
the moment the sample size was fixed. Reporting "no difference" here is a statement about the
study, not about the process.

**`PILOTO-SETUP` was almost properly designed, and still missed.** Five parts per arm against an
effect of two standard deviations gives 79.1% power — near enough to the conventional 80% that
nobody would object. It observed −2.77 against a true −6.00 and returned `p = 0.2345`. This is the
one-in-five case, and it is what 80% power *means*: a well-designed study fails to detect a real
effect one time in five, by construction. A project that treats a single non-significant pilot as
settled has misread the guarantee it bought.

**`PILOTO-REFUGO` observed a larger improvement than the one that existed, and still could not
prove it.** Scrap fell from 8.0% to 4.5% in the data — 3.5 points against a true 2.5 — and the
test returned `p = 0.2152`. A proportion near 8% carries so little information that detecting a
2.5-point reduction needs **1,568 units per arm**, and the pilot ran 200. This is the case that
kills the intuition that a non-significant result implies a small effect: here the measured effect
was *bigger* than the truth and the sample size was still short by a factor of eight.

## The textbook formula, and when the shortcut costs something

`n = 2(z_{1−α/2} + z_{1−β})² s² / d²` is the formula on the wall of every training room. It
substitutes normal quantiles for t quantiles, so it always understates the sample size. Measured
against the exact noncentral-t calculation at 80% power and α = 0.05:

| Effect size (Cohen's d) | Exact n per group | Formula's n | Power the formula delivers |
| --- | --- | --- | --- |
| 2.00 | 6 | 4 | **0.6569** |
| 1.50 | 9 | 7 | **0.7313** |
| 1.00 | 17 | 16 | 0.7814 |
| 0.50 | 64 | 63 | 0.7952 |
| 0.33 | 146 | 145 | 0.7997 |
| 0.10 | 1,571 | 1,570 | 0.7998 |

**The honest summary is that the shortcut is harmless for most studies.** Across the whole
practical range it is off by one observation per group, and the power it delivers rounds to the
power it was asked for. Saying otherwise would be overstating a real but small effect, which is
the error this module is about.

Where it stops being harmless is the small confirmation run — the case where the expected effect
is large, so the study is tiny, and the relative error is not. At two standard deviations the
formula asks for 4 per group against the 6 required and delivers **66% power**. `PILOTO-SETUP` is
exactly that case: the formula would have sized it at 4, which is not "almost right" for a study
that then gets one shot.

## Post-hoc power is arithmetic on the p-value

After a non-significant result, the reflex is to compute power from the effect that was observed
and report it as the reason. It is not a reason, because the two quantities are locked together:

| Observed effect (n = 30, sd = 12) | p-value | Observed power |
| --- | --- | --- |
| 2.00 | 0.5212 | 0.0973 |
| 4.00 | 0.2018 | 0.2456 |
| 6.00 | 0.0577 | 0.4779 |
| **6.20** | **0.0501** | **0.5032** |
| 8.00 | 0.0124 | 0.7187 |
| 12.00 | 0.0003 | 0.9677 |

Observed power is a strictly monotone function of the p-value, so it carries no information the
p-value did not. At the boundary the correspondence is essentially exact: where `p = α = 0.05` the
observed power is **0.5035**, and it converges on one half as the study grows — 0.5114 at n = 10,
0.5035 at n = 30, 0.5010 at n = 100, 0.5002 at n = 500.

So "we only had 48% power" is another way of writing "p was just above 0.05". It is the same
finding in different units, and citing it as the explanation for the first finding is circular.

What a non-significant result *does* support is the detectable difference, which uses the sample
size and the spread but **not** the observed effect — and therefore says something the p-value
does not. `observed_power_is_circular` returns the power and the p-value together, and only
together, for exactly this reason.

## Assumptions and limitations

- **Power is computed for a difference you supply, not discovered from the data.** The input is a
  difference worth detecting — a decision about what matters commercially — and the module cannot
  supply it. A project that does not know what size of effect would change its mind has not
  finished defining itself.
- **The two-sample calculation assumes equal group sizes and a common standard deviation.**
  Unequal allocation and unequal variances both change the answer, and neither is implemented.
  The Welch case is not a refinement of this one; it is a different calculation.
- **`sd` is treated as known.** In practice it is estimated, usually from a small pilot, and a
  sample size computed from an under-estimated standard deviation is optimistic in exactly the
  way this module warns about elsewhere. Sizing from the upper confidence bound on `sd` rather
  than its point estimate is the conservative move, and it is the caller's to make.
- **The proportion calculation uses the arcsine transformation**, which stabilises the variance
  but is still an approximation. It is unreliable when `n·p` is very small — the regime where
  exact binomial methods are needed and where, in any case, the sample size is enormous.
- **80% is a convention, exposed as `DEFAULT_POWER`.** It is not a property of anything. A test
  whose miss would close a programme deserves more; a screening run that will be followed by a
  confirmation deserves less.
- **Nothing here corrects for multiplicity.** Five comparisons at α = 0.05 are not five
  independent 5% risks, and the sample sizes computed here take no account of how many tests the
  project intends to run.
- **Power says nothing about whether the effect matters.** A study large enough to detect anything
  will detect things worth nothing, and the detectable difference is the tool for that end of the
  problem too — read in the other direction.

---

# `dmaic.analyze` — poder e tamanho de amostra

*[English](#dmaicanalyze--power-and-sample-size)*

## O problema de negócio

Um projeto de melhoria roda um piloto, testa o resultado, obtém `p = 0,23` e é encerrado como
"sem melhoria significativa". O relatório é honesto, a aritmética está correta, e a conclusão pode
ainda assim estar errada — porque um p-valor não-significativo tem exatamente a mesma aparência
quer o efeito seja ausente, quer seja apenas menor do que o estudo jamais poderia ver.

Essa falha não é detectável na saída. É inteiramente previsível de antemão, e quase nunca
calculada.

## A decisão que ele habilita

Duas decisões, e a ordem importa:

1. **Antes do piloto: de quanto dado eu preciso?** Não "quanto consigo coletar" — o tamanho de
   amostra é o que fixa a conclusão para todo efeito abaixo do limite de detecção, então
   escolhê-lo por conveniência é escolher a resposta.
2. **Depois de um piloto não-significativo: o que este estudo descartou?** A saída honesta não é o
   p-valor, é a **diferença detectável**: o menor efeito que o estudo poderia ter encontrado.
   Qualquer coisa abaixo dela nunca estava ao alcance.

## Uso

```python
from dmaic.analyze import detectable_difference, power_two_means, sample_size_two_means

power_two_means(n_per_group=30, delta=4.0, sd=12.0)  # 0,2456 - erra 3 vezes em 4
detectable_difference(n_per_group=30, sd=12.0)  # 8,83 - nada menor estava ao alcance
sample_size_two_means(delta=4.0, sd=12.0)  # n=143 por grupo, poder 0,8021
```

## Resultado

Três pilotos do conjunto sintético, cada um dimensionado como projetos são de fato dimensionados —
pelo que era conveniente coletar. O gerador declara o efeito que colocou, o que é toda a vantagem
de dado sintético aqui: um projeto real não distingue efeito perdido de efeito ausente.

| Ensaio | Efeito observado | Efeito real | p-valor | Poder p/ o efeito real | n rodado | n necessário |
| --- | --- | --- | --- | --- | --- | --- |
| `PILOTO-CICLO` | −0,29 min | −4,00 min | 0,9234 | **0,2456** | 30 | 143 |
| `PILOTO-SETUP` | −2,77 min | −6,00 min | 0,2345 | 0,7905 | 5 | 6 |
| `PILOTO-REFUGO` | −3,50 pts | −2,50 pts | 0,2152 | **0,1702** | 200 | **1.568** |

**Os três são não-significativos. Os três tinham efeito real.** Três erros tipo II em sequência, e
todos seriam relatados como "melhoria não demonstrada". O que os torna valiosos em conjunto é que
cada um falha por um motivo diferente.

**O `PILOTO-CICLO` estava sem poder nenhum e ainda teve azar.** Com 30 por braço, tinha 24,6% de
chance de encontrar o próprio efeito de 4 minutos, e observou −0,29. Um p-valor de 0,9234 se lê
como evidência esmagadora de ausência de efeito e não é nada disso: a diferença detectável do
estudo era **8,83 minutos**, então uma melhoria de 4 minutos estava fora de alcance desde o momento
em que o tamanho de amostra foi fixado. Reportar "sem diferença" aqui é afirmação sobre o estudo,
não sobre o processo.

**O `PILOTO-SETUP` estava quase bem desenhado, e errou de todo jeito.** Cinco peças por braço
contra um efeito de dois desvios-padrão dá 79,1% de poder — perto o bastante dos 80% convencionais
para ninguém objetar. Observou −2,77 contra um real de −6,00 e devolveu `p = 0,2345`. Este é o caso
de um em cinco, e é o que 80% de poder *significa*: um estudo bem desenhado deixa de detectar um
efeito real uma vez em cada cinco, por construção. Um projeto que trata um único piloto
não-significativo como encerrado leu errado a garantia que comprou.

**O `PILOTO-REFUGO` observou melhoria maior que a que existia, e ainda assim não conseguiu
prová-la.** O refugo caiu de 8,0% para 4,5% nos dados — 3,5 pontos contra um real de 2,5 — e o
teste devolveu `p = 0,2152`. Uma proporção perto de 8% carrega tão pouca informação que detectar
uma redução de 2,5 pontos exige **1.568 unidades por braço**, e o piloto rodou 200. Este é o caso
que mata a intuição de que resultado não-significativo implica efeito pequeno: aqui o efeito medido
era *maior* que a verdade e o tamanho de amostra ainda estava curto por um fator de oito.

## A fórmula do quadro, e quando o atalho custa algo

`n = 2(z_{1−α/2} + z_{1−β})² s² / d²` é a fórmula na parede de toda sala de treinamento. Ela
substitui quantis t por quantis normais, então sempre subestima o tamanho de amostra. Medida contra
o cálculo exato com t não-central, a 80% de poder e α = 0,05:

| Tamanho de efeito (d de Cohen) | n exato por grupo | n da fórmula | Poder que a fórmula entrega |
| --- | --- | --- | --- |
| 2,00 | 6 | 4 | **0,6569** |
| 1,50 | 9 | 7 | **0,7313** |
| 1,00 | 17 | 16 | 0,7814 |
| 0,50 | 64 | 63 | 0,7952 |
| 0,33 | 146 | 145 | 0,7997 |
| 0,10 | 1.571 | 1.570 | 0,7998 |

**O resumo honesto é que o atalho é inofensivo para a maioria dos estudos.** Em toda a faixa
prática ele erra por uma observação por grupo, e o poder que entrega arredonda para o poder pedido.
Dizer o contrário seria exagerar um efeito real mas pequeno, que é justamente o erro de que este
módulo trata.

Onde ele deixa de ser inofensivo é a corrida de confirmação pequena — o caso em que o efeito
esperado é grande, então o estudo é minúsculo, e o erro relativo não é. Em dois desvios-padrão a
fórmula pede 4 por grupo contra os 6 necessários e entrega **66% de poder**. O `PILOTO-SETUP` é
exatamente esse caso: a fórmula o teria dimensionado em 4, o que não é "quase certo" para um estudo
que depois tem uma única chance.

## Poder post-hoc é aritmética sobre o p-valor

Depois de um resultado não-significativo, o reflexo é calcular o poder a partir do efeito observado
e reportá-lo como a razão. Não é razão, porque as duas grandezas estão travadas uma à outra:

| Efeito observado (n = 30, sd = 12) | p-valor | Poder observado |
| --- | --- | --- |
| 2,00 | 0,5212 | 0,0973 |
| 4,00 | 0,2018 | 0,2456 |
| 6,00 | 0,0577 | 0,4779 |
| **6,20** | **0,0501** | **0,5032** |
| 8,00 | 0,0124 | 0,7187 |
| 12,00 | 0,0003 | 0,9677 |

O poder observado é função estritamente monótona do p-valor, então não carrega informação que o
p-valor já não tivesse. Na fronteira a correspondência é praticamente exata: onde `p = α = 0,05`, o
poder observado é **0,5035**, e converge para um meio conforme o estudo cresce — 0,5114 em n = 10,
0,5035 em n = 30, 0,5010 em n = 100, 0,5002 em n = 500.

Então "tivemos só 48% de poder" é outra forma de escrever "p ficou pouco acima de 0,05". É o mesmo
achado em outra unidade, e citá-lo como explicação do primeiro é circular.

O que um resultado não-significativo *sustenta* é a diferença detectável, que usa o tamanho de
amostra e a dispersão mas **não** o efeito observado — e portanto diz algo que o p-valor não diz. O
`observed_power_is_circular` devolve o poder e o p-valor juntos, e só juntos, exatamente por isso.

## Premissas e limitações

- **O poder é calculado para uma diferença que você fornece, não descoberta nos dados.** A entrada
  é uma diferença que vale a pena detectar — decisão sobre o que importa comercialmente — e o
  módulo não pode fornecê-la. Um projeto que não sabe que tamanho de efeito mudaria sua decisão não
  terminou de se definir.
- **O cálculo de duas amostras assume grupos de tamanho igual e desvio-padrão comum.** Alocação
  desigual e variâncias desiguais mudam a resposta, e nenhuma das duas está implementada. O caso de
  Welch não é um refinamento deste; é outro cálculo.
- **`sd` é tratado como conhecido.** Na prática é estimado, normalmente de um piloto pequeno, e um
  tamanho de amostra calculado sobre desvio-padrão subestimado é otimista exatamente do jeito que
  este módulo alerta em outros pontos. Dimensionar pelo limite superior do intervalo de confiança
  do `sd`, e não pela estimativa pontual, é a escolha conservadora — e é de quem chama.
- **O cálculo de proporções usa a transformação arco-seno**, que estabiliza a variância mas ainda é
  aproximação. Não é confiável quando `n·p` é muito pequeno — o regime em que métodos binomiais
  exatos são necessários e em que, de todo modo, o tamanho de amostra é enorme.
- **80% é convenção, exposta como `DEFAULT_POWER`.** Não é propriedade de nada. Um teste cuja falha
  encerraria um programa merece mais; uma triagem que será seguida de confirmação merece menos.
- **Nada aqui corrige multiplicidade.** Cinco comparações a α = 0,05 não são cinco riscos
  independentes de 5%, e os tamanhos de amostra calculados aqui não levam em conta quantos testes o
  projeto pretende rodar.
- **Poder não diz nada sobre o efeito importar.** Um estudo grande o bastante para detectar
  qualquer coisa vai detectar coisas que não valem nada, e a diferença detectável é a ferramenta
  também para essa ponta do problema — lida na direção oposta.
