# `dmaic.measure` — can the readings carry the decision?

*[Português](#dmaicmeasure--as-leituras-sustentam-a-decisão)*

Three questions, and the standard study answers one of them. Each has its own document because
each is worth reading in full.

| Question | What it decides | Document |
| --- | --- | --- |
| Can the gage tell the parts apart? | Whether any later number means anything | [`README-msa.md`](README-msa.md) |
| Is the gage right? | Which parts get shipped and which get scrapped | [`README-accuracy.md`](README-accuracy.md) |
| How long does either answer last? | When it needs recalibrating, and whether the study's verdict is about the instrument or the calendar | [`README-stability.md`](README-stability.md) |

**The first is the gate every other number depends on.** A capability index, a hypothesis test and
a factorial effect are all computed on readings. Three synthetic gages show what the study
decides: the same gage reads 2.64, 16.24 and 63.58 depending on which ratio is quoted, and the
10% / 30% acceptance bands are written for only one of them.

**The second cannot be answered by the first study, and not because it is a weak test.** Every
AIAG figure is computed from differences between readings, so adding a constant to all of them
leaves percent study variation, percent contribution, percent tolerance, ndc and the verdict
**exactly** unchanged — measured at 1e-11 across all three gages, which is floating-point noise
rather than a small sensitivity. `BALANCA-01` passes the crossed study on both criteria at 5.69%
of tolerance and reads **7.82% of tolerance heavy**, and that error costs 3,356 ppm of conforming
parts scrapped against 161 ppm calibrated.

**The third is about the date, and both of the others are snapshots.** `BALANCA-01` drifts
0.105428 g a day, so five percent of its tolerance is spent in **22.8 days** and the 4 g offset
above is the same instrument seen on day 38. Worse, a crossed study spread over two weeks puts the
drift in whichever ANOVA term the schedule aligns it with: give each operator their own day and
reproducibility inflates **2.51×** while repeatability does not move at all. The calendar, reported
as the people.

## Assumptions and limitations

Each document carries its own, in detail. The two that span all three:

- **Neither study measures the operator's decision, only the reading.** A gage that resolves the
  part perfectly, read by an inspector applying a rule of thumb, produces a decision no study
  here describes.
- **Both assume the measurement error is normal and independent of the part.** A gage whose
  spread grows with the reading violates the first study's decomposition and the second's
  misclassification integral in the same way, and neither reports it.

---

# `dmaic.measure` — as leituras sustentam a decisão?

*[English](#dmaicmeasure--can-the-readings-carry-the-decision)*

Três perguntas, e o estudo padrão responde uma delas. Cada uma tem seu documento porque cada uma
vale leitura integral.

| Pergunta | O que decide | Documento |
| --- | --- | --- |
| O gage consegue distinguir as peças? | Se qualquer número posterior significa algo | [`README-msa.md`](README-msa.md) |
| O gage está certo? | Quais peças são expedidas e quais são refugadas | [`README-accuracy.md`](README-accuracy.md) |
| Quanto tempo cada resposta dura? | Quando recalibrar, e se o veredito do estudo é sobre o instrumento ou sobre o calendário | [`README-stability.md`](README-stability.md) |

**A primeira é o portão de que todo outro número depende.** Um índice de capabilidade, um teste de
hipótese e um efeito fatorial são todos calculados sobre leituras. Três gages sintéticos mostram o
que o estudo decide: o mesmo gage lê 2,64, 16,24 e 63,58 conforme a razão citada, e as faixas de
aceitação de 10% / 30% foram escritas para apenas uma delas.

**A segunda não pode ser respondida pelo primeiro estudo, e não por ele ser um teste fraco.** Toda
figura AIAG é calculada a partir de diferenças entre leituras, então somar uma constante a todas
deixa a %variação do estudo, a %contribuição, a %tolerância, o ndc e o veredito **exatamente**
inalterados — medido em 1e-11 nos três gages, que é ruído de ponto flutuante e não uma
sensibilidade pequena. O `BALANCA-01` passa no estudo cruzado nos dois critérios, a 5,69% da
tolerância, e lê **7,82% da tolerância acima**, e esse erro custa 3.356 ppm de peças conformes
refugadas contra 161 ppm calibrado.

**A terceira é sobre a data, e as outras duas são retratos.** O `BALANCA-01` deriva 0,105428 g por
dia, então cinco por cento da tolerância dele são gastos em **22,8 dias** e o desvio de 4 g acima é
o mesmo instrumento visto no dia 38. Pior, um estudo cruzado espalhado por duas semanas põe a deriva
no termo da ANOVA com o qual a agenda a alinhar: dê a cada operador o seu dia e a reprodutibilidade
infla **2,51×** enquanto a repetibilidade não se move. O calendário, reportado como sendo das
pessoas.

## Premissas e limitações

Cada documento carrega as suas, em detalhe. As duas que valem para as três:

- **Nenhum dos estudos mede a decisão do operador, apenas a leitura.** Um gage que resolve a peça
  perfeitamente, lido por um inspetor aplicando uma regra de bolso, produz uma decisão que nenhum
  estudo daqui descreve.
- **Os dois assumem erro de medição normal e independente da peça.** Um gage cuja dispersão cresce
  com a leitura viola a decomposição do primeiro estudo e a integral de má classificação do
  segundo do mesmo jeito, e nenhum dos dois reporta isso.
