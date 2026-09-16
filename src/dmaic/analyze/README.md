# `dmaic.analyze` — does the evidence support the conclusion?

*[Português](#dmaicanalyze--a-evidência-sustenta-a-conclusão)*

Two gates, and neither of them is a p-value. Each has its own document because each answers a
different question and both are worth reading in full.

| Gate | Question | Document |
| --- | --- | --- |
| Power and sample size | What could this test possibly find? | [`README-power.md`](README-power.md) |
| Assumptions | Does the test that was run hold the error rate it claims? | [`README-compare.md`](README-compare.md) |

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

## Assumptions and limitations

Each document carries its own, in detail. The two that span both:

- **Neither gate says whether a difference matters.** Holding a 5% error rate means the test will
  not manufacture findings; detecting an effect means it was large enough to see. Whether it is
  worth acting on is a commercial question, and the closest this package comes to it is the
  detectable difference read in the other direction.
- **Nothing here corrects for multiplicity.** Every sample size, power figure and error rate in
  both documents is for one comparison. Five at 5% are not five independent 5% risks.

---

# `dmaic.analyze` — a evidência sustenta a conclusão?

*[English](#dmaicanalyze--does-the-evidence-support-the-conclusion)*

Dois portões, e nenhum deles é um p-valor. Cada um tem seu documento porque cada um responde a uma
pergunta diferente e os dois valem leitura integral.

| Portão | Pergunta | Documento |
| --- | --- | --- |
| Poder e tamanho de amostra | O que este teste poderia encontrar? | [`README-power.md`](README-power.md) |
| Premissas | O teste que foi rodado mantém a taxa de erro que alega? | [`README-compare.md`](README-compare.md) |

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

## Premissas e limitações

Cada documento carrega as suas, em detalhe. As duas que valem para ambos:

- **Nenhum dos portões diz se uma diferença importa.** Manter taxa de erro de 5% significa que o
  teste não vai fabricar achados; detectar um efeito significa que ele era grande o bastante para
  ser visto. Se vale ação é pergunta comercial, e o mais perto que este pacote chega dela é a
  diferença detectável lida na direção oposta.
- **Nada aqui corrige multiplicidade.** Todo tamanho de amostra, figura de poder e taxa de erro nos
  dois documentos é para uma comparação. Cinco a 5% não são cinco riscos independentes de 5%.
