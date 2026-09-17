# `dmaic.control` — sustain: did the gain hold?

*[Português](#dmaiccontrol--sustentação-o-ganho-se-sustentou)*

## The business problem

A project closes with a verified improvement and a control plan. A year later somebody checks, and
the check takes the form everybody's template uses: current months against the original baseline.

That is the same before-and-after [`dmaic.improve`](../improve/README.md) shows is inflated by the
trend — except the trend has now had twice as long to run. So **a decaying gain reports as a growing
one**, and the report is arithmetically correct.

## The decision it enables

1. **Is the benefit still there?** Which needs a comparison group, exactly as it did at closure.
2. **Could this audit have told me if it wasn't?** Almost always no, and that is answerable when the
   project closes rather than a year later when the answer is due.

## Usage

```python
from dmaic.control import decay_detection, reported_gain, retention_path, sustain_audit

reported_gain(panel, split=12, windows=((13, 18), (31, 36)))  # what the pack shows
retention_path(panel, split=12, windows=((13, 24), (25, 36)))  # with a comparison group
audit = sustain_audit(panel, split=12, close=(13, 24), audit=(25, 36))
audit.retention, audit.intervals_overlap, audit.detectable_decay
decay_detection((1.0, 2.0, 3.0), units=12, change_sd=audit.change_sd)
```

## Result: the report gets better as the gain gets worse

Twenty-four sites over thirty-six periods, twelve improved from period thirteen with an effect of
−5.00 decaying on a **one-year half-life**, and a trend of −0.40 a period running throughout. The
true effect averages −3.7119 over the first post-year and −1.8560 over the second: exactly half, by
construction.

| Window | Reported gain | True effect | Attributable |
| --- | --- | --- | --- |
| 13–18 | −9.1599 | −4.3488 | no |
| 19–24 | −9.5392 | −3.0750 | no |
| 25–30 | −11.0472 | −2.1744 | no |
| 31–36 | **−11.5753** | **−1.5375** | no |

**The reported gain grows by 2.42 while the real effect falls by 2.81.** Nobody fabricated anything:
the baseline is the agreed baseline, the current months are the current months, and every period
between them is another period of trend inside the figure. The flattering number is the one the
template produces, which is why it is the one in the pack.

## Result: a comparison group fixes the direction

| Window | True effect | Estimate | Interval |
| --- | --- | --- | --- |
| 13–24 | −3.7119 | −4.1721 | −5.7224 to −2.6219 |
| 25–36 | −1.8560 | −1.7827 | −3.6341 to **+0.0687** |

Both intervals contain the effect that was there, and the direction is right: the estimate falls
where the report rose.

## Result: and what the audit can establish, which is less

| Figure | Measured | True |
| --- | --- | --- |
| Retention | 42.73% | 50.00% |
| Decay | 2.3895 | 1.8560 |
| Smallest decay this audit could resolve | **2.5604** | — |
| Site-level change spread | 2.1394 | — |
| Intervals overlap | **yes** | — |

**The two intervals overlap completely, so the audit cannot establish that the gain decayed at all.**
It would need a decay of 2.5604 to say so, and the decay that happened is 1.8560. Even the audit's
own (over-)estimate of 2.3895 is below its resolution.

That is the honest conclusion of a correctly conducted sustain audit here: *it cannot tell.* Which is
not the same as concluding that the gain held, and it is what the report claiming −11.58 has replaced.

| Decay | Detectable at 80% | Power against this decay |
| --- | --- | --- |
| 0.5000 | 2.5604 | 0.0850 |
| 1.0000 | 2.5604 | 0.1948 |
| **1.8560** | 2.5604 | **0.5287** |
| 3.0000 | 2.5604 | 0.9068 |
| 5.0000 | 2.5604 | 0.9998 |

Against the decay that actually happened the audit is a coin flip. **This is not an argument against
auditing.** It is an argument for sizing the audit when the project closes — while there is still
somebody to argue with about how many sites it gets — rather than a year later when the answer is
due. The arithmetic is [`dmaic.analyze.power`](../analyze/README-power.md)'s, unchanged, applied a
year earlier than anybody applies it.

## Assumptions and limitations

- **Exponential decay is a model, not a law.** A gain can fall off a cliff when one person leaves, or
  hold for two years and then go. The half-life here is declared so the estimates have something to
  be checked against; nothing in the module fits or assumes a decay shape.
- **The comparison group has to still be comparable a year later.** Everything
  [`dmaic.improve`](../improve/README.md) says about parallel trends applies with more force over a
  longer horizon, and the longer the audit waits the more likely something else has happened to one
  group and not the other.
- **A decay and a spreading improvement look alike.** If the practice leaks to the untreated sites —
  which is what usually happens to a good idea — the difference in differences shrinks while nothing
  decays at all. This module cannot distinguish the two, and the distinction matters: one is a
  failure to sustain and the other is the best outcome available.
- **The audit's power is computed against its own observed spread.** That spread already includes
  whatever happened during the window, so it is an honest figure for this audit and not a planning
  figure for the next one. Sizing the next audit wants the spread from a period nobody intervened in.
- **One decay, one audit, two windows.** No sequential monitoring, which would need a stopping rule
  and would spend its alpha differently, and no allowance for the audit being run because somebody
  suspected a problem — a selection effect of exactly the kind
  [`dmaic.define`](../define/README.md) prices.
- **Nothing here is a control plan.** A plan names who reacts to what and when. This module computes
  the one thing a plan is usually silent about: whether the check it prescribes could see the failure
  it is meant to catch.

---

# `dmaic.control` — sustentação: o ganho se sustentou?

*[English](#dmaiccontrol--sustain-did-the-gain-hold)*

## O problema de negócio

Um projeto encerra com melhoria verificada e plano de controle. Um ano depois alguém verifica, e a
verificação toma a forma que o template de todo mundo usa: meses atuais contra o baseline original.

É o mesmo antes-e-depois que o [`dmaic.improve`](../improve/README.md) mostra ser inflado pela
tendência — só que a tendência já teve o dobro do tempo para correr. Então **um ganho em decadência é
reportado como um ganho crescente**, e o relatório está aritmeticamente correto.

## A decisão que ele habilita

1. **O benefício ainda existe?** O que exige um grupo de comparação, exatamente como no encerramento.
2. **Esta auditoria conseguiria me dizer se não existisse?** Quase sempre não, e isso é respondível
   quando o projeto encerra, não um ano depois quando a resposta é devida.

## Uso

```python
from dmaic.control import decay_detection, reported_gain, retention_path, sustain_audit

reported_gain(painel, split=12, windows=((13, 18), (31, 36)))  # o que o pacote mostra
retention_path(painel, split=12, windows=((13, 24), (25, 36)))  # com grupo de comparação
auditoria = sustain_audit(painel, split=12, close=(13, 24), audit=(25, 36))
auditoria.retention, auditoria.intervals_overlap, auditoria.detectable_decay
decay_detection((1.0, 2.0, 3.0), units=12, change_sd=auditoria.change_sd)
```

## Resultado: o relatório melhora conforme o ganho piora

Vinte e quatro sites ao longo de trinta e seis períodos, doze melhorados a partir do período treze
com efeito de −5,00 decaindo com **meia-vida de um ano**, e uma tendência de −0,40 por período
correndo todo o tempo. O efeito real média −3,7119 no primeiro ano pós-projeto e −1,8560 no segundo:
exatamente a metade, por construção.

| Janela | Ganho reportado | Efeito real | Atribuível |
| --- | --- | --- | --- |
| 13–18 | −9,1599 | −4,3488 | não |
| 19–24 | −9,5392 | −3,0750 | não |
| 25–30 | −11,0472 | −2,1744 | não |
| 31–36 | **−11,5753** | **−1,5375** | não |

**O ganho reportado cresce 2,42 enquanto o efeito real cai 2,81.** Ninguém fabricou nada: o baseline
é o baseline acordado, os meses atuais são os meses atuais, e cada período entre eles é mais um
período de tendência dentro da cifra. A cifra lisonjeira é a que o template produz, e é por isso que
é a que está no pacote.

## Resultado: um grupo de comparação corrige a direção

| Janela | Efeito real | Estimativa | Intervalo |
| --- | --- | --- | --- |
| 13–24 | −3,7119 | −4,1721 | −5,7224 a −2,6219 |
| 25–36 | −1,8560 | −1,7827 | −3,6341 a **+0,0687** |

Os dois intervalos contêm o efeito que existia, e a direção está certa: a estimativa cai onde o
relatório subiu.

## Resultado: e o que a auditoria consegue estabelecer, que é menos

| Figura | Medido | Real |
| --- | --- | --- |
| Retenção | 42,73% | 50,00% |
| Decadência | 2,3895 | 1,8560 |
| Menor decadência que esta auditoria resolveria | **2,5604** | — |
| Dispersão da mudança por site | 2,1394 | — |
| Intervalos se sobrepõem | **sim** | — |

**Os dois intervalos se sobrepõem completamente, então a auditoria não consegue estabelecer que o
ganho decaiu.** Precisaria de uma decadência de 2,5604 para dizer isso, e a que aconteceu é 1,8560.
Até a própria (super)estimativa da auditoria, 2,3895, está abaixo da resolução dela.

Essa é a conclusão honesta de uma auditoria de sustentação bem conduzida aqui: *ela não consegue
dizer.* O que não é o mesmo que concluir que o ganho se sustentou, e é o que o relatório de −11,58
substituiu.

| Decadência | Detectável a 80% | Poder contra esta decadência |
| --- | --- | --- |
| 0,5000 | 2,5604 | 0,0850 |
| 1,0000 | 2,5604 | 0,1948 |
| **1,8560** | 2,5604 | **0,5287** |
| 3,0000 | 2,5604 | 0,9068 |
| 5,0000 | 2,5604 | 0,9998 |

Contra a decadência que de fato aconteceu a auditoria é cara ou coroa. **Isso não é argumento contra
auditar.** É argumento para dimensionar a auditoria quando o projeto encerra — enquanto ainda há
alguém com quem discutir quantos sites ela recebe — e não um ano depois quando a resposta é devida. A
aritmética é a do [`dmaic.analyze.power`](../analyze/README-power.md), inalterada, aplicada um ano
antes do que todo mundo aplica.

## Premissas e limitações

- **Decaimento exponencial é modelo, não lei.** Um ganho pode cair de um penhasco quando uma pessoa
  sai, ou se sustentar por dois anos e então ir. A meia-vida aqui é declarada para que as estimativas
  tenham contra o que ser conferidas; nada no módulo ajusta ou assume forma de decaimento.
- **O grupo de comparação tem de continuar comparável um ano depois.** Tudo o que o
  [`dmaic.improve`](../improve/README.md) diz sobre tendências paralelas vale com mais força num
  horizonte mais longo, e quanto mais a auditoria espera, mais provável que algo tenha acontecido a
  um grupo e não ao outro.
- **Uma decadência e uma melhoria que se espalha se parecem.** Se a prática vaza para os sites não
  tratados — o que normalmente acontece com uma boa ideia — a diferença em diferenças encolhe sem que
  nada decaia. Este módulo não distingue os dois, e a distinção importa: um é falha de sustentação e o
  outro é o melhor resultado possível.
- **O poder da auditoria é calculado contra a dispersão observada dela.** Essa dispersão já inclui o
  que aconteceu durante a janela, então é cifra honesta para esta auditoria e não cifra de
  planejamento para a próxima. Dimensionar a próxima quer a dispersão de um período em que ninguém
  interveio.
- **Uma decadência, uma auditoria, duas janelas.** Sem monitoramento sequencial, que exigiria regra de
  parada e gastaria o alfa de outra forma, e sem previsão para a auditoria ter sido feita porque
  alguém suspeitou de um problema — um efeito de seleção exatamente do tipo que o
  [`dmaic.define`](../define/README.md) precifica.
- **Nada aqui é um plano de controle.** Um plano nomeia quem reage a quê e quando. Este módulo calcula
  a única coisa sobre a qual um plano normalmente se cala: se a verificação que ele prescreve
  conseguiria ver a falha que ela deveria pegar.
