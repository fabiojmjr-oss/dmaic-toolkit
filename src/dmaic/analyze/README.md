# `dmaic.analyze` — does the evidence support the conclusion?

*[Português](#dmaicanalyze--a-evidência-sustenta-a-conclusão)*

Three gates, and none of them is a p-value. Each has its own document because each answers a
different question and all three are worth reading in full.

| Gate | Question | Document |
| --- | --- | --- |
| Power and sample size | What could this test possibly find? | [`README-power.md`](README-power.md) |
| Assumptions | Does the test that was run hold the error rate it claims? | [`README-compare.md`](README-compare.md) |
| Design | Can this experiment separate the effects it is being asked about? | [`README-factorial.md`](README-factorial.md) |

**The first gate closes before any data is collected.** A study whose sample size was fixed by
what was convenient has already decided its own conclusion for every effect below its detection
limit. Three synthetic pilots demonstrate it: all three non-significant, all three with a real
effect planted, and one of them needing 1,568 units per arm against the 200 it ran.

**The second gate is about the procedure rather than the study.** The taught flowchart — check
normality, check variance, choose accordingly — is measurably worse than skipping the checks and
using Welch's test: 6.28% false positives against Welch's 5.07% in the case that matters, and the
pooled t-test it sometimes selects runs at 21.30% against a nominal 5%. Worse, the normality check
is least informative exactly where the violation does most damage, because both facts are
consequences of small n.

**The third gate closes before the runs are executed, and it is free to get wrong.** A half
fraction makes pairs of effects arithmetically identical, so its estimate is the exact sum of
both. Two half fractions of the same four factors cost the same eight runs and read off the same
experiment; one recovers the interaction to within 0.0895 of the full sixteen-run answer, and the
other reports **9.4067** for a factor whose effect is exactly zero — the second largest figure in
the study, at 2.63 times the smallest effect eight runs could detect. Only the generator differs.

## Assumptions and limitations

Each document carries its own, in detail. The three that span them:

- **Neither gate says whether a difference matters.** Holding a 5% error rate means the test will
  not manufacture findings; detecting an effect means it was large enough to see. Whether it is
  worth acting on is a commercial question, and the closest this package comes to it is the
  detectable difference read in the other direction.
- **Nothing here corrects for multiplicity.** Every sample size, power figure and error rate in
  all three documents is for one comparison. Five at 5% are not five independent 5% risks, and a
  factorial screening fifteen terms is not one comparison either.
- **A detection limit is about noise and says nothing about bias.** The same figure that correctly
  tells a project not to chase a spurious 1.5494 has no opinion at all about a 9.4067 that is a
  real effect sitting in the wrong column.

---

# `dmaic.analyze` — a evidência sustenta a conclusão?

*[English](#dmaicanalyze--does-the-evidence-support-the-conclusion)*

Três portões, e nenhum deles é um p-valor. Cada um tem seu documento porque cada um responde a uma
pergunta diferente e os três valem leitura integral.

| Portão | Pergunta | Documento |
| --- | --- | --- |
| Poder e tamanho de amostra | O que este teste poderia encontrar? | [`README-power.md`](README-power.md) |
| Premissas | O teste que foi rodado mantém a taxa de erro que alega? | [`README-compare.md`](README-compare.md) |
| Desenho | Este experimento consegue separar os efeitos sobre os quais está sendo perguntado? | [`README-factorial.md`](README-factorial.md) |

**O primeiro portão fecha antes de qualquer dado ser coletado.** Um estudo cujo tamanho de amostra
foi fixado pelo que era conveniente já decidiu a própria conclusão para todo efeito abaixo do seu
limite de detecção. Três pilotos sintéticos demonstram: os três não-significativos, os três com
efeito real plantado, e um deles precisando de 1.568 unidades por braço contra as 200 que rodou.

**O segundo portão é sobre o procedimento, não sobre o estudo.** O fluxograma ensinado — testar
normalidade, testar variância, escolher conforme — é mensuravelmente pior que pular os checks e
usar o teste de Welch: 6,28% de falsos positivos contra 5,07% do Welch no caso que importa, e o t
agrupado que ele às vezes seleciona roda a 21,30% contra um nominal de 5%. Pior, o check de
normalidade é menos informativo exatamente onde a violação faz mais dano, porque as duas coisas
são consequência de n pequeno.

**O terceiro portão fecha antes de as corridas serem executadas, e é de graça errar nele.** Uma
meia-fração torna pares de efeitos aritmeticamente idênticos, então a estimativa dela é a soma
exata dos dois. Duas meias-frações dos mesmos quatro fatores custam as mesmas oito corridas e leem
o mesmo experimento; uma recupera a interação dentro de 0,0895 da resposta completa de dezesseis
corridas, e a outra reporta **9,4067** para um fator cujo efeito é exatamente zero — a segunda
maior cifra do estudo, a 2,63 vezes o menor efeito que oito corridas conseguiriam detectar. Só o
gerador muda.

## Premissas e limitações

Cada documento carrega as suas, em detalhe. As três que valem para todos:

- **Nenhum dos portões diz se uma diferença importa.** Manter taxa de erro de 5% significa que o
  teste não vai fabricar achados; detectar um efeito significa que ele era grande o bastante para
  ser visto. Se vale ação é pergunta comercial, e o mais perto que este pacote chega dela é a
  diferença detectável lida na direção oposta.
- **Nada aqui corrige multiplicidade.** Todo tamanho de amostra, figura de poder e taxa de erro
  nos três documentos é para uma comparação. Cinco a 5% não são cinco riscos independentes de 5%, e
  um fatorial triando quinze termos também não é uma comparação.
- **Limite de detecção é sobre ruído e não diz nada sobre viés.** A mesma cifra que corretamente
  diz a um projeto para não ir atrás de um 1,5494 espúrio não tem opinião nenhuma sobre um 9,4067
  que é um efeito real sentado na coluna errada.
