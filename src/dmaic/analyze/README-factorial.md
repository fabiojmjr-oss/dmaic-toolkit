# `dmaic.analyze` — design of experiments

*[Português](#dmaicanalyze--planejamento-de-experimentos)*

## The business problem

A project has four suspects and budget for eight runs. Somebody produces a half fraction, the
runs are executed, the analysis comes back, and two factors are large. The design was orthogonal,
the arithmetic is right, the report is honest — and one of the two factors may have no effect at
all, with the number in its column belonging to an interaction between the other two.

Nothing in the output says which. The run sheet of a good design and a useless one look the same,
cost the same, and take the same eight runs.

## The decision it enables

Two, and they are asked at different times:

1. **Before the runs: which fraction, and what does it give up?** A fraction is not a smaller
   version of the full experiment. It makes pairs of effects arithmetically identical, and the
   choice of generator decides which pairs. That choice is free and it is the whole design.
2. **After the runs: what is this estimate actually an estimate of?** Every number a fraction
   returns is the sum of its own effect and the effects aliased with it. The alias structure is
   the only thing that says what was added to what, and it is computable before any data exists.

## Usage

```python
from dmaic.analyze import alias_structure, effects, fractional_factorial, full_factorial

full_factorial(("temperatura", "pressao", "tempo", "lote"))  # 16 runs, nothing aliased
good = fractional_factorial(("temperatura", "pressao", "tempo", "lote"), ("D=ABC",))
good.resolution_label  # 'IV' - main effects clear
bad = fractional_factorial(("temperatura", "pressao", "tempo", "lote"), ("D=AB",))
bad.resolution_label  # 'III'
bad.confounded_main_effects()  # {'A': ('BD',), 'B': ('AD',), 'D': ('AB',)}
effects(bad, response)  # estimates, each with what it is a sum of
```

## Result

One synthetic experiment on a curing oven: four factors, sixteen runs, shear strength in MPa. The
generator declares what is in the process, and two of the four factors are set to **exactly
zero** — cure time, because the oven is already past the point where longer helps, and resin
batch, because it was only in the experiment to settle a suspicion.

| Term | Factor | True effect |
| --- | --- | --- |
| A | temperatura | +12.00 |
| B | pressao | +5.00 |
| C | tempo de cura | **0.00** |
| D | lote de resina | **0.00** |
| AB | temperatura × pressao | +8.00 |

The sixteen runs are measured once. Each design below reads the rows it would have run, so
nothing varies between them except which of the same runs were kept — and between the two half
fractions, not even how many.

| Term | True | full 2⁴, 16 runs | 2^(4-1) `D=ABC`, 8 runs | 2^(4-1) `D=AB`, 8 runs |
| --- | --- | --- | --- | --- |
| A | +12.00 | 12.5810 | 11.8174 | 13.1256 |
| B | +5.00 | 4.9727 | 4.5785 | 5.8547 |
| C | 0.00 | 0.2853 | −0.3577 | −0.4082 |
| D | 0.00 | 1.5494 | 0.5307 | **9.4067** |
| AB | +8.00 | 7.8573 | **7.7678** | 9.4067 |
| Resolution | | full | IV | **III** |

**The resolution III design reports 9.4067 for a factor whose effect is exactly zero.** Resin
batch comes back as the second largest effect in the study — 1.88 times the size of the real
pressure effect, and 2.63 times the smallest effect eight runs could have detected. It is not
marginal, it does not look like noise, and it would survive any screening rule a project applies.
The number is the temperature-by-pressure interaction, arriving in the resin batch column because
the generator `D=AB` put it there.

**The ranking is what a project acts on, and the two fractions disagree about it.** Same eight
runs' worth of budget, same measured process:

| Design | Main effects, largest first |
| --- | --- |
| 2^(4-1) `D=ABC` | A +11.82, B +4.58, D +0.53, C −0.36 |
| 2^(4-1) `D=AB` | A +13.13, **D +9.41**, B +5.85, C −0.41 |

The first orders the factors correctly and puts both zeros at the bottom. The second promotes a
factor that does nothing above the one that does, and a project reading it would go and control
resin batch.

**The good fraction costs almost nothing.** `D=ABC` recovers the interaction at 7.7678 against
the full design's 7.8573 — a gap of 0.0895 MPa on an effect of 8 — using half the runs. The half
fraction is a bargain. It is a bargain *at the right generator*, and the same eight runs at the
wrong one buy a fiction.

## Aliasing is an exact addition, not extra noise

The usual phrasing — a fraction "cannot separate" two effects, or gives a "less certain"
estimate — suggests something statistical, as though more runs of the same fraction would resolve
it. They would not. The fraction's estimate is the **arithmetic sum** of the full design's
estimates of the aliased terms, exact to the last bit:

| Fraction | Estimate | Full design | Sum |
| --- | --- | --- | --- |
| `D=AB`: D = D + AB | 9.4067 | D 1.5494, AB 7.8573 | 9.4067 |
| `D=ABC`: AB = AB + CD | 7.7678 | AB 7.8573, CD −0.0895 | 7.7678 |

Every alias pair in both fractions reproduces to within 5.3e-15, which is floating-point noise
and not a statistical agreement. This is why `D=ABC` works here and `D=AB` does not: both add two
numbers, and `D=ABC` happens to add zero to the ones that matter. Resolution IV is not a design
that avoids aliasing, it is a design whose aliasing adds two-factor interactions to *each other*
and three-factor interactions to the main effects — which is a bet that the three-factor terms are
small, stated honestly rather than a guarantee.

## The resolution comes from the relation, not from the generators

`D=ABC` and `E=BCD` are both four-letter generators, so a run sheet built from them looks like a
resolution IV design. The defining relation closes under multiplication: `ABCD × BCDE = AE`, a
two-letter word, so factors A and E share a column outright. That design is resolution II —
A and E are not two factors of the experiment, they are one column with two names — and
`fractional_factorial` refuses to build it rather than returning something that looks fine.

Reading the resolution off the shortest *generator* rather than off the closed *relation* is the
mistake this guards against, and it is the reason the relation is computed here instead of being
taken from a table.

## What eight runs could have seen

The other half of the design decision, and the one wave 2 already answers. Each effect in a
two-level design is a comparison of two halves of the runs, so the detection limit is the
two-sample calculation with `n_runs / 2` per side. At this process's run-to-run standard
deviation of 1.5 MPa:

| Runs | Smallest effect detectable at 80% power |
| --- | --- |
| 8 | 3.5711 MPa |
| 16 | 2.2600 MPa |
| 32 | 1.5355 MPa |
| 64 | 1.0672 MPa |

It does its job against noise: the largest purely spurious estimate in the full design is D at
1.5494, comfortably below the 2.2600 limit, so a project reading the full sixteen runs would not
chase it. And it does nothing whatever against aliasing. The false 9.4067 sits at 2.63 times the
limit, because it is not noise — it is a real effect in the wrong column, and a detection limit
has no opinion about which column a real effect belongs to.

## Assumptions and limitations

- **No p-values, and that is not an omission.** An unreplicated factorial has no degrees of
  freedom left for error. Testing its effects means borrowing an error estimate from whichever
  high-order interactions the analyst decided to call noise, and that decision, not the data,
  then determines what comes out significant. `effects` returns estimates and their alias
  structure; `detectable_effect` answers what the design could have seen. Neither pretends to a
  significance test the runs cannot support.
- **Two levels only.** No centre points, so curvature is invisible: a factor with a maximum
  between its two settings reads as having no effect at all. No three-level factors, no response
  surface, no optimisation — this is screening and it stops where screening stops.
- **The estimate assumes the model.** An effect is a difference of averages, which is the right
  quantity only if the response is roughly additive in the coded factors over the range run.
  Extrapolating beyond the levels is not supported by anything here.
- **Randomisation and blocking are the caller's problem.** The runs come out in standard order
  because that is the readable order, not because it is the order to run them in. Running in
  standard order confounds every effect with anything that drifts over the session — tool wear,
  ambient temperature, the operator getting better at the job — and no analysis recovers it.
  Blocking a fraction into two halves is also not implemented; a block is an extra factor and it
  aliases like one.
- **The response is assumed to be measurable.** The effects here are 8 to 12 MPa on a measurement
  system nobody checked. Wave 1's gage study is upstream of this whole document: a design that
  resolves effects the gage cannot see produces exactly the table above with noise in every cell.
- **Nothing here corrects for multiplicity.** Fifteen effects at 5% each is not a 5% risk.
- **The comparison of the two fractions is on one experiment.** Which noise draw landed where
  moves the individual estimates; the finding that survives any draw is the exact-sum identity,
  because that is arithmetic rather than a measurement. The resolution III design reports
  `D + AB` whatever the data — 9.4067 here, something else next time, and never `D`.

---

# `dmaic.analyze` — planejamento de experimentos

*[English](#dmaicanalyze--design-of-experiments)*

## O problema de negócio

Um projeto tem quatro suspeitos e orçamento para oito corridas. Alguém monta uma meia-fração, as
corridas são executadas, a análise volta, e dois fatores aparecem grandes. O desenho era
ortogonal, a aritmética está certa, o relatório é honesto — e um dos dois fatores pode não ter
efeito nenhum, com o número da coluna dele pertencendo a uma interação entre os outros dois.

Nada na saída diz qual. A folha de corridas de um bom desenho e de um inútil é igual, custa igual
e leva as mesmas oito corridas.

## A decisão que ele habilita

Duas, e em momentos diferentes:

1. **Antes das corridas: qual fração, e o que ela abre mão?** Uma fração não é uma versão menor do
   experimento completo. Ela torna pares de efeitos aritmeticamente idênticos, e a escolha do
   gerador decide quais pares. Essa escolha é de graça e é o desenho inteiro.
2. **Depois das corridas: esta estimativa é estimativa de quê?** Todo número que uma fração
   devolve é a soma do efeito dele com os efeitos aliasados com ele. A estrutura de alias é a
   única coisa que diz o que foi somado a quê, e é calculável antes de existir qualquer dado.

## Uso

```python
from dmaic.analyze import alias_structure, effects, fractional_factorial, full_factorial

full_factorial(("temperatura", "pressao", "tempo", "lote"))  # 16 corridas, nada aliasado
bom = fractional_factorial(("temperatura", "pressao", "tempo", "lote"), ("D=ABC",))
bom.resolution_label  # 'IV' - efeitos principais limpos
ruim = fractional_factorial(("temperatura", "pressao", "tempo", "lote"), ("D=AB",))
ruim.resolution_label  # 'III'
ruim.confounded_main_effects()  # {'A': ('BD',), 'B': ('AD',), 'D': ('AB',)}
effects(ruim, resposta)  # estimativas, cada uma com o que ela é soma
```

## Resultado

Um experimento sintético num forno de cura: quatro fatores, dezesseis corridas, resistência ao
cisalhamento em MPa. O gerador declara o que existe no processo, e dois dos quatro fatores estão
em **exatamente zero** — o tempo de cura, porque o forno já passou do ponto em que mais tempo
ajuda, e o lote de resina, porque só entrou no experimento para encerrar uma suspeita.

| Termo | Fator | Efeito real |
| --- | --- | --- |
| A | temperatura | +12,00 |
| B | pressao | +5,00 |
| C | tempo de cura | **0,00** |
| D | lote de resina | **0,00** |
| AB | temperatura × pressao | +8,00 |

As dezesseis corridas são medidas uma vez. Cada desenho abaixo lê as linhas que teria rodado,
então nada varia entre eles além de quais das mesmas corridas foram mantidas — e, entre as duas
meias-frações, nem sequer quantas.

| Termo | Real | 2⁴ completo, 16 corridas | 2^(4-1) `D=ABC`, 8 corridas | 2^(4-1) `D=AB`, 8 corridas |
| --- | --- | --- | --- | --- |
| A | +12,00 | 12,5810 | 11,8174 | 13,1256 |
| B | +5,00 | 4,9727 | 4,5785 | 5,8547 |
| C | 0,00 | 0,2853 | −0,3577 | −0,4082 |
| D | 0,00 | 1,5494 | 0,5307 | **9,4067** |
| AB | +8,00 | 7,8573 | **7,7678** | 9,4067 |
| Resolução | | completo | IV | **III** |

**O desenho resolução III reporta 9,4067 para um fator cujo efeito é exatamente zero.** O lote de
resina volta como o segundo maior efeito do estudo — 1,88 vez o tamanho do efeito real da pressão,
e 2,63 vezes o menor efeito que oito corridas conseguiriam detectar. Não é marginal, não parece
ruído, e sobreviveria a qualquer regra de triagem que um projeto aplique. O número é a interação
temperatura × pressão, chegando na coluna do lote de resina porque o gerador `D=AB` a colocou lá.

**O ranking é o que um projeto usa para agir, e as duas frações discordam dele.** Mesmo orçamento
de oito corridas, mesmo processo medido:

| Desenho | Efeitos principais, do maior para o menor |
| --- | --- |
| 2^(4-1) `D=ABC` | A +11,82, B +4,58, D +0,53, C −0,36 |
| 2^(4-1) `D=AB` | A +13,13, **D +9,41**, B +5,85, C −0,41 |

O primeiro ordena os fatores corretamente e deixa os dois zeros no fim. O segundo promove um fator
que não faz nada acima do que faz, e um projeto lendo isso iria controlar lote de resina.

**A fração boa custa quase nada.** `D=ABC` recupera a interação em 7,7678 contra os 7,8573 do
desenho completo — uma diferença de 0,0895 MPa num efeito de 8 — com metade das corridas. A
meia-fração é uma barganha. É uma barganha *no gerador certo*, e as mesmas oito corridas no errado
compram uma ficção.

## Alias é uma soma exata, não ruído adicional

A frase usual — a fração "não consegue separar" dois efeitos, ou dá uma estimativa "menos
confiável" — sugere algo estatístico, como se mais corridas da mesma fração resolvessem. Não
resolveriam. A estimativa da fração é a **soma aritmética** das estimativas que o desenho completo
dá aos termos aliasados, exata até o último bit:

| Fração | Estimativa | Desenho completo | Soma |
| --- | --- | --- | --- |
| `D=AB`: D = D + AB | 9,4067 | D 1,5494, AB 7,8573 | 9,4067 |
| `D=ABC`: AB = AB + CD | 7,7678 | AB 7,8573, CD −0,0895 | 7,7678 |

Todo par de alias nas duas frações reproduz dentro de 5,3e-15, que é ruído de ponto flutuante e
não concordância estatística. É por isso que `D=ABC` funciona aqui e `D=AB` não: os dois somam
dois números, e o `D=ABC` por acaso soma zero aos que importam. Resolução IV não é um desenho que
evita alias, é um desenho cujo alias soma interações de dois fatores *entre si* e interações de
três fatores aos efeitos principais — o que é uma aposta de que os termos de três fatores são
pequenos, declarada honestamente em vez de garantida.

## A resolução vem da relação, não dos geradores

`D=ABC` e `E=BCD` são os dois geradores de quatro letras, então uma folha de corridas montada com
eles parece um desenho resolução IV. A relação definidora fecha sob multiplicação:
`ABCD × BCDE = AE`, uma palavra de duas letras, então os fatores A e E compartilham a coluna
inteira. Esse desenho é resolução II — A e E não são dois fatores do experimento, são uma coluna
com dois nomes — e o `fractional_factorial` recusa construí-lo em vez de devolver algo que parece
correto.

Ler a resolução do *gerador* mais curto em vez da *relação* fechada é o erro contra o qual isso
protege, e é a razão de a relação ser calculada aqui em vez de tirada de uma tabela.

## O que oito corridas conseguiriam ver

A outra metade da decisão de desenho, e a que a onda 2 já responde. Cada efeito de um desenho de
dois níveis é uma comparação entre duas metades das corridas, então o limite de detecção é o
cálculo de duas amostras com `n_runs / 2` de cada lado. No desvio-padrão corrida a corrida deste
processo, 1,5 MPa:

| Corridas | Menor efeito detectável a 80% de poder |
| --- | --- |
| 8 | 3,5711 MPa |
| 16 | 2,2600 MPa |
| 32 | 1,5355 MPa |
| 64 | 1,0672 MPa |

Ele cumpre o papel contra ruído: a maior estimativa puramente espúria do desenho completo é o D em
1,5494, confortavelmente abaixo do limite de 2,2600, então um projeto lendo as dezesseis corridas
não iria atrás dela. E não faz absolutamente nada contra alias. O falso 9,4067 está a 2,63 vezes o
limite, porque não é ruído — é um efeito real na coluna errada, e um limite de detecção não tem
opinião sobre a qual coluna um efeito real pertence.

## Premissas e limitações

- **Sem p-valores, e isso não é uma omissão.** Um fatorial sem réplica não tem graus de liberdade
  sobrando para erro. Testar os efeitos dele significa emprestar uma estimativa de erro das
  interações de ordem alta que o analista decidiu chamar de ruído, e é essa decisão, não o dado,
  que passa a determinar o que sai significativo. O `effects` devolve estimativas e a estrutura de
  alias; o `detectable_effect` responde o que o desenho conseguiria ver. Nenhum dos dois finge um
  teste de significância que as corridas não sustentam.
- **Só dois níveis.** Sem pontos centrais, curvatura é invisível: um fator com máximo entre as
  duas configurações lê como não tendo efeito nenhum. Sem fatores de três níveis, sem superfície
  de resposta, sem otimização — isto é triagem e para onde a triagem para.
- **A estimativa assume o modelo.** Um efeito é uma diferença de médias, o que é a quantidade
  certa só se a resposta for aproximadamente aditiva nos fatores codificados dentro da faixa
  rodada. Extrapolar além dos níveis não é sustentado por nada aqui.
- **Randomização e blocagem são problema de quem chama.** As corridas saem em ordem padrão porque
  é a ordem legível, não porque seja a ordem de rodar. Rodar em ordem padrão confunde todo efeito
  com qualquer coisa que derive ao longo da sessão — desgaste de ferramenta, temperatura ambiente,
  o operador ficando melhor na tarefa — e nenhuma análise recupera isso. Blocar uma fração em duas
  metades também não está implementado; um bloco é um fator a mais e aliasa como um.
- **A resposta é assumida como mensurável.** Os efeitos aqui são de 8 a 12 MPa num sistema de
  medição que ninguém verificou. O estudo de gage da onda 1 está a montante deste documento
  inteiro: um desenho que resolve efeitos que o gage não consegue ver produz exatamente a tabela
  acima com ruído em cada célula.
- **Nada aqui corrige multiplicidade.** Quinze efeitos a 5% cada não são um risco de 5%.
- **A comparação das duas frações é sobre um experimento.** Qual sorteio de ruído caiu onde move
  as estimativas individuais; o achado que sobrevive a qualquer sorteio é a identidade da soma
  exata, porque é aritmética e não medição. O desenho resolução III reporta `D + AB` seja qual for
  o dado — 9,4067 aqui, outra coisa na próxima vez, e nunca `D`.
