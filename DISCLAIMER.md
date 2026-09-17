# Disclaimer

*[Português abaixo](#aviso)*

**No data from any employer, client or third party is used anywhere in this repository.**

Every table in every example, test and README figure is produced by `dmaic.synth`, a seeded
generator whose parameters are written down in `src/dmaic/synth/config.py`. Running
`generate_dataset()` on the default seed reproduces every published number exactly.

Gage names (`BALANCA-01`, `PAQUIMETRO-02`, `INSPECAO-03`), operator names (`OP-A`, `OP-B`,
`OP-C`), part numbers and specification limits are **invented labels**. So are the pilot names
(`PILOTO-CICLO`, `PILOTO-SETUP`, `PILOTO-REFUGO`), the group names in the comparisons (`TURNO-A`,
`TURNO-B`, `LINHA-1`, `LINHA-2`, `CELULA-X`, `CELULA-Y`, `FORN-X`, `FORN-Y`) and the experiment
(`FORNO-CURA`, with its factors and levels). The reference values the gages are measured against are invented too, and are exact by construction: a real calibrated master carries its own uncertainty, and that limitation is stated in the module documentation rather than hidden. The improvement panel's sites (`CD-01` to `CD-20`), its volumes, its cost per order and its project cost are invented too. None of these are references to any real instrument,
person, part, shift, line, cell, supplier, process or specification, and any resemblance to one
is coincidental.

Everything in the generator was designed to make a particular statistical situation visible — a
gage whose two acceptance criteria disagree, a gage whose failure is the operators rather than
the instrument, a pilot too small to find its own effect, an experiment where two factors do
exactly nothing — not to represent any real process. The effects, spreads and sample sizes were
chosen for what they demonstrate.

This repository is a portfolio of methods. It is not a report about any operation.

---

# Aviso

*[English above](#disclaimer)*

**Nenhum dado de empregador, cliente ou terceiro é utilizado em qualquer parte deste
repositório.**

Toda tabela em todo exemplo, teste e figura de README é produzida pelo `dmaic.synth`, um gerador
com semente cujos parâmetros estão escritos em `src/dmaic/synth/config.py`. Rodar
`generate_dataset()` na semente padrão reproduz exatamente todo número publicado.

Nomes de gage (`BALANCA-01`, `PAQUIMETRO-02`, `INSPECAO-03`), nomes de operador (`OP-A`, `OP-B`,
`OP-C`), números de peça e limites de especificação são **rótulos inventados**. Também são os
nomes dos pilotos (`PILOTO-CICLO`, `PILOTO-SETUP`, `PILOTO-REFUGO`), os nomes dos grupos nas
comparações (`TURNO-A`, `TURNO-B`, `LINHA-1`, `LINHA-2`, `CELULA-X`, `CELULA-Y`, `FORN-X`,
`FORN-Y`) e o experimento (`FORNO-CURA`, com seus fatores e níveis). Os valores de referência contra os quais os gages são medidos também são inventados, e são exatos por construção: um padrão calibrado real carrega incerteza própria, e essa limitação está declarada na documentação do módulo em vez de escondida. Os sites do painel de melhoria (`CD-01` a `CD-20`), os volumes, o custo por pedido e o custo do projeto também são inventados. Nada disso é referência a
nenhum instrumento, pessoa, peça, turno, linha, célula, fornecedor, processo ou especificação
real, e qualquer semelhança é coincidência.

Tudo no gerador foi desenhado para tornar visível uma situação estatística específica — um gage
cujos dois critérios de aceitação discordam, um gage cuja reprovação são os operadores e não o
instrumento, um piloto pequeno demais para achar o próprio efeito, um experimento em que dois
fatores não fazem absolutamente nada — e não para representar processo real algum. Os efeitos, as
dispersões e os tamanhos de amostra foram escolhidos pelo que demonstram.

Este repositório é um portfólio de métodos. Não é um relatório sobre operação alguma.
