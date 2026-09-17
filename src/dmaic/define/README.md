# `dmaic.define` — the charter, as arithmetic

*[Português](#dmaicdefine--o-charter-como-aritmética)*

## The business problem

A charter says the cost per order is 18% above entitlement and the prize is 50 million gross. Every
figure in that sentence is a decision: which measurand, how long a baseline, whose performance is
the target, and how much of a modelled cost is cash. Written as prose they read as description.
Written as arithmetic, they disagree with each other.

The worst of it is structural. A project is chartered **from** a recent baseline — recent because
that is what triggered it — and **towards** the best site's observed performance. The worst
performer of a short window was partly unlucky and comes back up on its own; the best performer of
the same window was partly lucky and goes back down. **A charter takes the most inflated estimate
available at both ends of its gap, and the two errors add.**

## The decision it enables

1. **Is this gap real, and how much of it?** Both ends have to be read before the answer means
   anything, and the honest output is a range rather than a number.
2. **Which baseline window, and does it matter?** It does, in a direction that always flatters.
3. **Does the decomposition add up?** A tree whose leaves claim more than the gap has counted a
   saving twice, and a portfolio built from it promises more than the process contains.

## Usage

```python
from dmaic.define import Charter, entitlement, entitlement_inflation, gap_by_window

gap_by_window(panel, last_period=12, windows=(1, 3, 6, 12))  # the same data, four gaps
reference = entitlement(site_averages, noise_sd=6.0, window=12)
reference.charter_gap, reference.shrunk_gap  # 17.4420 and 16.6681
Charter(
    measurand="cost per order",
    unit="BRL",
    baseline=96.9307,
    baseline_window=12,
    target=79.4887,
    target_basis="entitlement",
    volume_per_period=240_000,
    periods=12,
    variable_share=0.35,
).benefit_case().cash  # audited by the Improve phase's class
```

## Result: the same data, read as four baselines

Twelve months of twenty sites, and four ways to describe where they are.

| Window | Mean | Best | Worst | Gap to best | Worst to best |
| --- | --- | --- | --- | --- | --- |
| 1 | 94.7895 | **75.9952** | **120.3974** | **18.7943** | **44.4022** |
| 3 | 95.7523 | 81.8822 | 112.2490 | 13.8701 | 30.3668 |
| 6 | 96.3559 | 80.8312 | 111.9404 | 15.5247 | 31.1092 |
| 12 | 96.9307 | 79.4887 | 109.9823 | 17.4420 | 30.4936 |

**A charter can quote a gap to the best site of 18.79 or 13.87 from the same twelve months**,
depending on a window that no charter template has a field for.

**And the spread between sites — the figure that justifies a harmonisation programme — reads 44.40
on one period against 30.49 on twelve.** 46% larger, from the window alone. "Our sites vary
enormously" is partly a statement about how recently you looked.

The gaps above are not monotone in the window, and that is honest rather than tidy: the trend of
−0.40 a period is inside every one of these windows too, so on real data the window's effect on the
artefact cannot be separated from the trend it also changes. Which is exactly why the artefact is
priced by simulation below, the way [`dmaic.improve`](../improve/README.md) prices regression to the
mean.

## Result: how much of an entitlement gap is the best site having a good run

Simulated, because the true level of each site is exactly what a charter does not have. Twenty
sites, the panel's spreads, no trend and no effect — only the order statistic.

| Baseline window | Charter's gap | The gap that is there | Shrunk gap | Inflation |
| --- | --- | --- | --- | --- |
| 1 | **18.6274** | 14.8561 | 11.9215 | **3.7713** |
| 3 | 16.2542 | 14.9069 | 13.6878 | 1.3474 |
| 6 | 15.6095 | 14.9185 | 14.2716 | 0.6910 |
| 12 | 15.2783 | 14.9599 | 14.5942 | 0.3184 |
| 24 | 15.2348 | 15.0210 | 14.8859 | 0.2137 |

**On a one-period baseline the charter claims 18.63 where 14.86 is there: 25% of the gap does not
exist.** Not because anybody measured badly — the arithmetic is right — but because the minimum of
twenty noisy averages is below the minimum of twenty true levels, always, and by a predictable
amount.

**Shrinking the best site's estimate toward the average errs the other way**, at 11.92, because the
minimum of shrunk values is pulled toward the mean too. That is not a failed fix, it is the useful
one: **the truth sits between the two in every window tried.** Quote the charter's figure and you
have chosen a direction. Quote both and you have stated a range, which is what the evidence
supports.

The bracket narrows as the baseline lengthens — 11.92 to 18.63 on one period, 14.89 to 15.23 on
twenty-four — so the cost of a short baseline is not a bias to be corrected but an interval that is
five times too wide to act on.

## Result: the charter this panel would produce

| Figure | Value |
| --- | --- |
| Baseline (12 periods, 20 sites) | 96.9307 BRL per order |
| Target (entitlement, best observed) | 79.4887 |
| Gap | **17.4420**, 18.0% |
| Entitlement gap as a range | 16.6681 to 17.4420 |
| Real share of the spread between sites | 96% |
| Gross benefit | 50,233,061 |
| Cash benefit | **17,581,571** |
| Capacity | 32,651,489 |
| Net of a 250,000 project | 17,331,571 |

The benefit is computed by the same class the Improve phase audits it with —
[`BenefitCase`](../improve/README.md). That is deliberate: a promise computed differently from the
way it will be verified has a discrepancy built into it that somebody will later have to explain,
and the explanation is always that the charter was optimistic.

## Result: and the tree that explains the gap

A decomposition as a project team would present it: three branches, seven leaves, contributions in
BRL per order.

| Path | Measurand | Contribution | Measurable |
| --- | --- | --- | --- |
| gap por pedido | | 19.60 | **no** |
| … / separacao | | 8.30 | yes |
| … / separacao / caminhamento | metros por linha | 5.20 | yes |
| … / separacao / conferencia | segundos por linha | 3.10 | yes |
| … / embalagem | | 4.20 | **no** |
| … / embalagem / material | BRL por caixa | 2.40 | yes |
| … / embalagem / retrabalho | | 1.80 | **no** |
| … / transporte | | 7.10 | **no** |
| … / transporte / ocupacao | m3 por veiculo | 4.50 | yes |
| … / transporte / cultura de servico | | 2.60 | **no** |

**The leaves claim 19.60 against a gap of 17.44: 1.12×.** The same saving is under more than one
name, and a portfolio built from this tree would promise 12% more than the process contains. That is
mild as these things go, and it is only visible because the tree was made to add up.

**And 4.40 of the claim — 22% of the tree — sits under leaves that name no measurand.** "Retrabalho"
and "cultura de servico" are real things and neither is a measurement, so that share of the benefit
cannot be verified after the project closes. It will be claimed anyway, because by then the only
figure anybody has is the total.

## Assumptions and limitations

- **The inflation figure is a property of the simulation's assumptions.** Normal site levels, normal
  noise, independent periods. A process whose sites differ by more than the noise has almost no
  inflation, and one where they barely differ has almost all of it — the reliability column of
  `entitlement` is the figure that says which case you are in, and it is estimable from the same
  averages.
- **Shrinkage assumes the sites are exchangeable.** Pulling a site toward the grand mean is only
  reasonable if, before seeing the data, it could as easily have been any of the others. A site
  running different equipment or a different product mix is not exchangeable with the rest, and
  shrinking it toward them is then the wrong correction rather than a conservative one.
- **Nothing here says the entitlement is achievable.** The best site's sustainable level is an upper
  bound on what the others can reach *by becoming like it*, and only if what makes it better is
  transferable. Where it is better because of its building, its labour market or its volume, the gap
  is real and the project cannot close it.
- **A CTQ tree's contributions are inputs.** This module checks that they add up and that each leaf
  names a measurand. It cannot check that a contribution is right, and the over-attribution multiple
  is only as good as the estimates in the leaves.
- **Disjointness is assumed, not verified.** Two leaves under different branches can be the same
  cost described twice, and no arithmetic here detects it: `overattribution` catches the case where
  the double counting pushes the total over the gap, and misses the case where it does not.
- **The target basis is recorded rather than evaluated.** A benchmark from an industry study and a
  number chosen in a meeting both go in as `"benchmark"` and `"absolute"`; the field exists so that
  the difference is on the page, not so that this module can rule on it.

---

# `dmaic.define` — o charter, como aritmética

*[English](#dmaicdefine--the-charter-as-arithmetic)*

## O problema de negócio

Um charter diz que o custo por pedido está 18% acima do entitlement e que o prêmio é 50 milhões
brutos. Toda cifra dessa frase é uma decisão: qual mensurando, quantos períodos de histórico, o
desempenho de quem é a meta, e quanto de um custo modelado é caixa. Escritas como prosa, parecem
descrição. Escritas como aritmética, discordam entre si.

O pior é estrutural. Um projeto é aberto **a partir de** um baseline recente — recente porque foi o
que disparou o projeto — e **em direção a** o desempenho observado do melhor site. O pior desempenho
de uma janela curta estava em parte com azar e volta a subir por conta própria; o melhor desempenho
da mesma janela estava em parte com sorte e volta a descer. **Um charter toma a estimativa mais
inflada disponível nas duas pontas do gap, e os dois erros se somam.**

## A decisão que ele habilita

1. **Este gap é real, e quanto dele?** As duas pontas têm de ser lidas antes de a resposta
   significar algo, e a saída honesta é uma faixa e não um número.
2. **Qual janela de histórico, e isso importa?** Importa, numa direção que sempre lisonjeia.
3. **A decomposição fecha?** Uma árvore cujas folhas alegam mais que o gap contou uma economia duas
   vezes, e um portfólio construído sobre ela promete mais do que o processo contém.

## Uso

```python
from dmaic.define import Charter, entitlement, entitlement_inflation, gap_by_window

gap_by_window(painel, last_period=12, windows=(1, 3, 6, 12))  # o mesmo dado, quatro gaps
referencia = entitlement(medias_por_site, noise_sd=6.0, window=12)
referencia.charter_gap, referencia.shrunk_gap  # 17,4420 e 16,6681
Charter(
    measurand="custo por pedido",
    unit="BRL",
    baseline=96.9307,
    baseline_window=12,
    target=79.4887,
    target_basis="entitlement",
    volume_per_period=240_000,
    periods=12,
    variable_share=0.35,
).benefit_case().cash  # auditado pela classe da fase Improve
```

## Resultado: o mesmo dado, lido como quatro baselines

Doze meses de vinte sites, e quatro formas de descrever onde eles estão.

| Janela | Média | Melhor | Pior | Gap ao melhor | Pior ao melhor |
| --- | --- | --- | --- | --- | --- |
| 1 | 94,7895 | **75,9952** | **120,3974** | **18,7943** | **44,4022** |
| 3 | 95,7523 | 81,8822 | 112,2490 | 13,8701 | 30,3668 |
| 6 | 96,3559 | 80,8312 | 111,9404 | 15,5247 | 31,1092 |
| 12 | 96,9307 | 79,4887 | 109,9823 | 17,4420 | 30,4936 |

**Um charter pode citar um gap ao melhor site de 18,79 ou de 13,87 dos mesmos doze meses**,
dependendo de uma janela para a qual nenhum template de charter tem campo.

**E a dispersão entre sites — a cifra que justifica um programa de harmonização — lê 44,40 em um
período contra 30,49 em doze.** 46% maior, apenas pela janela. "Nossos sites variam enormemente" é
em parte uma afirmação sobre quão recentemente você olhou.

Os gaps acima não são monótonos na janela, e isso é honesto e não organizado: a tendência de −0,40
por período está dentro de cada uma dessas janelas também, então em dado real o efeito da janela
sobre o artefato não se separa da tendência que ela também muda. É exatamente por isso que o
artefato é precificado por simulação abaixo, do jeito que o
[`dmaic.improve`](../improve/README.md) precifica regressão à média.

## Resultado: quanto de um gap de entitlement é o melhor site com um bom período

Simulado, porque o nível real de cada site é exatamente o que um charter não tem. Vinte sites, as
dispersões do painel, sem tendência e sem efeito — só a estatística de ordem.

| Janela de histórico | Gap do charter | O gap que existe | Gap encolhido | Inflação |
| --- | --- | --- | --- | --- |
| 1 | **18,6274** | 14,8561 | 11,9215 | **3,7713** |
| 3 | 16,2542 | 14,9069 | 13,6878 | 1,3474 |
| 6 | 15,6095 | 14,9185 | 14,2716 | 0,6910 |
| 12 | 15,2783 | 14,9599 | 14,5942 | 0,3184 |
| 24 | 15,2348 | 15,0210 | 14,8859 | 0,2137 |

**Em um histórico de um período o charter alega 18,63 onde existem 14,86: 25% do gap não existe.**
Não porque alguém mediu mal — a aritmética está certa — mas porque o mínimo de vinte médias ruidosas
fica abaixo do mínimo de vinte níveis reais, sempre, e por uma quantidade previsível.

**Encolher a estimativa do melhor site em direção à média erra para o outro lado**, em 11,92, porque
o mínimo dos valores encolhidos também é puxado para a média. Isso não é uma correção falha, é a
correção útil: **a verdade fica entre as duas em toda janela testada.** Cite a cifra do charter e
você escolheu uma direção. Cite as duas e você declarou uma faixa, que é o que a evidência sustenta.

A faixa estreita conforme o histórico se alonga — 11,92 a 18,63 em um período, 14,89 a 15,23 em
vinte e quatro — então o custo de um histórico curto não é um viés a corrigir, é um intervalo cinco
vezes largo demais para agir sobre.

## Resultado: o charter que este painel produziria

| Figura | Valor |
| --- | --- |
| Baseline (12 períodos, 20 sites) | 96,9307 BRL por pedido |
| Meta (entitlement, melhor observado) | 79,4887 |
| Gap | **17,4420**, 18,0% |
| Gap de entitlement como faixa | 16,6681 a 17,4420 |
| Parcela real da dispersão entre sites | 96% |
| Benefício bruto | 50.233.061 |
| Benefício em caixa | **17.581.571** |
| Capacidade | 32.651.489 |
| Líquido de um projeto de 250.000 | 17.331.571 |

O benefício é calculado pela mesma classe com que a fase Improve o audita —
[`BenefitCase`](../improve/README.md). É deliberado: uma promessa calculada de forma diferente de
como será verificada traz embutida uma discrepância que alguém depois terá de explicar, e a
explicação é sempre que o charter foi otimista.

## Resultado: e a árvore que explica o gap

Uma decomposição como um time de projeto apresentaria: três ramos, sete folhas, contribuições em BRL
por pedido.

| Caminho | Mensurando | Contribuição | Mensurável |
| --- | --- | --- | --- |
| gap por pedido | | 19,60 | **não** |
| … / separacao | | 8,30 | sim |
| … / separacao / caminhamento | metros por linha | 5,20 | sim |
| … / separacao / conferencia | segundos por linha | 3,10 | sim |
| … / embalagem | | 4,20 | **não** |
| … / embalagem / material | BRL por caixa | 2,40 | sim |
| … / embalagem / retrabalho | | 1,80 | **não** |
| … / transporte | | 7,10 | **não** |
| … / transporte / ocupacao | m3 por veiculo | 4,50 | sim |
| … / transporte / cultura de servico | | 2,60 | **não** |

**As folhas alegam 19,60 contra um gap de 17,44: 1,12×.** A mesma economia está sob mais de um nome,
e um portfólio construído sobre esta árvore prometeria 12% mais do que o processo contém. É brando
para o padrão dessas coisas, e só é visível porque a árvore foi feita para fechar.

**E 4,40 da alegação — 22% da árvore — está sob folhas que não nomeiam mensurando.** "Retrabalho" e
"cultura de servico" são coisas reais e nenhuma das duas é uma medição, então essa parcela do
benefício não pode ser verificada depois que o projeto encerra. Vai ser alegada de todo jeito,
porque a essa altura a única cifra que alguém tem é o total.

## Premissas e limitações

- **A cifra de inflação é propriedade das premissas da simulação.** Níveis de site normais, ruído
  normal, períodos independentes. Um processo cujos sites diferem muito mais que o ruído quase não
  tem inflação, e um em que eles quase não diferem tem quase toda ela — a coluna de confiabilidade
  do `entitlement` é a cifra que diz em qual caso você está, e ela é estimável das mesmas médias.
- **Encolhimento assume sites intercambiáveis.** Puxar um site para a média geral só é razoável se,
  antes de ver o dado, ele poderia igualmente ser qualquer um dos outros. Um site com equipamento
  diferente ou mix diferente não é intercambiável com os demais, e encolhê-lo para eles é a correção
  errada em vez de uma correção conservadora.
- **Nada aqui diz que o entitlement é alcançável.** O nível sustentável do melhor site é um limite
  superior do que os outros podem atingir *tornando-se como ele*, e só se o que o torna melhor for
  transferível. Onde ele é melhor por causa do prédio, do mercado de trabalho ou do volume, o gap é
  real e o projeto não consegue fechá-lo.
- **As contribuições de uma árvore CTQ são entrada.** Este módulo verifica que elas fecham e que
  cada folha nomeia um mensurando. Não consegue verificar que uma contribuição está certa, e o
  múltiplo de sobreatribuição é tão bom quanto as estimativas nas folhas.
- **Disjunção é assumida, não verificada.** Duas folhas em ramos diferentes podem ser o mesmo custo
  descrito duas vezes, e nenhuma aritmética daqui detecta: o `overattribution` pega o caso em que a
  dupla contagem empurra o total acima do gap, e perde o caso em que não empurra.
- **A base da meta é registrada, não avaliada.** Um benchmark de estudo setorial e um número
  escolhido numa reunião entram como `"benchmark"` e `"absolute"`; o campo existe para que a
  diferença esteja na página, não para que este módulo julgue.
