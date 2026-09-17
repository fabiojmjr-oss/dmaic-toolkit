# `dmaic.control` — holding a gain, and what the plan guarantees

*[Português](#dmaiccontrol--sustentar-um-ganho-e-o-que-o-plano-garante)*

Two questions, and both are usually answered with a document rather than a number.

| Question | What it decides | Document |
| --- | --- | --- |
| Did the gain hold? | Whether the project's benefit is still there, or only still being reported | [`README-sustain.md`](README-sustain.md) |
| What does this sampling plan catch? | Which lots ship and which get quarantined | [`README-sampling.md`](README-sampling.md) |

**The first has a trap built into its arithmetic.** A sustain check compares the current months to
the original baseline, which is the before-and-after [`dmaic.improve`](../improve/README.md) shows is
inflated by the trend — except that by now the trend has had twice as long to run. On the synthetic
panel the gain **halves** over a year while the report built against the old baseline goes from
−9.16 to **−11.58**. Both numbers are correct and they point in opposite directions.

**The second is a curve that nobody draws.** A plan quoted at "AQL 1.0%" rejects 2.7% of lots at 1%
defective, exactly as advertised, and accepts **47.1%** of lots at three times that level.

**Control charts are deliberately not here.** Charts, Nelson run rules and capability against
within-subgroup sigma live in the sibling `oplab.spc` package. Putting the same code in two
repositories under one name would read as padding to anyone who opens both, and the sampling module
says explicitly that acceptance sampling is not a substitute for process control.

## Assumptions and limitations

Each document carries its own, in detail. The two that span both:

- **Neither is a control plan.** A plan says who reacts to what, and this package computes the two
  things a plan is usually silent about: whether its sampling discriminates, and whether its audit
  could detect the decay it exists to catch.
- **Both assume the measurement is sound.** [`dmaic.measure`](../measure/README.md) is upstream of
  every figure here: an inspector with 90% agreement changes every acceptance probability, and a
  drifting gage changes every sustain estimate.

---

# `dmaic.control` — sustentar um ganho, e o que o plano garante

*[English](#dmaiccontrol--holding-a-gain-and-what-the-plan-guarantees)*

Duas perguntas, e as duas normalmente são respondidas com um documento em vez de um número.

| Pergunta | O que decide | Documento |
| --- | --- | --- |
| O ganho se sustentou? | Se o benefício do projeto ainda existe, ou apenas ainda é reportado | [`README-sustain.md`](README-sustain.md) |
| O que este plano de amostragem pega? | Quais lotes são expedidos e quais vão para quarentena | [`README-sampling.md`](README-sampling.md) |

**A primeira tem uma armadilha na própria aritmética.** Uma verificação de sustentação compara os
meses atuais ao baseline original, que é o antes-e-depois que o
[`dmaic.improve`](../improve/README.md) mostra ser inflado pela tendência — só que agora a tendência
teve o dobro do tempo para correr. No painel sintético o ganho **cai à metade** em um ano enquanto o
relatório construído sobre o baseline antigo vai de −9,16 a **−11,58**. As duas cifras estão certas e
apontam em direções opostas.

**A segunda é uma curva que ninguém desenha.** Um plano citado como "AQL 1,0%" rejeita 2,7% dos lotes
a 1% de defeituosos, exatamente como anunciado, e aceita **47,1%** dos lotes no triplo desse nível.

**Cartas de controle deliberadamente não estão aqui.** Cartas, regras de Nelson e capabilidade contra
sigma intra-subgrupo moram no pacote irmão `oplab.spc`. Pôr o mesmo código em dois repositórios sob
um nome leria como enchimento para quem abrisse os dois, e o módulo de amostragem diz explicitamente
que amostragem de aceitação não substitui controle de processo.

## Premissas e limitações

Cada documento carrega as suas, em detalhe. As duas que valem para ambos:

- **Nenhum dos dois é um plano de controle.** Um plano diz quem reage a quê, e este pacote calcula as
  duas coisas sobre as quais um plano normalmente se cala: se a amostragem dele discrimina, e se a
  auditoria dele conseguiria detectar a decadência que ela existe para pegar.
- **Os dois assumem medição confiável.** O [`dmaic.measure`](../measure/README.md) está a montante de
  toda cifra daqui: um inspetor com 90% de concordância muda toda probabilidade de aceitação, e um
  gage derivando muda toda estimativa de sustentação.
