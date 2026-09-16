# Disclaimer

*[Português abaixo](#aviso)*

**No data from any employer, client or third party is used anywhere in this repository.**

Every table in every example, test and README figure is produced by `dmaic.synth`, a seeded
generator whose parameters are written down in `src/dmaic/synth/config.py`. Running
`generate_dataset()` on the default seed reproduces every published number exactly.

Gage names (`BALANCA-01`, `PAQUIMETRO-02`, `INSPECAO-03`), operator names (`OP-A`, `OP-B`,
`OP-C`), part numbers and specification limits are **invented labels**. They are not references
to any real instrument, person, part or specification, and any resemblance to one is
coincidental.

The measurement systems in the generator were designed to make particular statistical situations
visible — a gage whose two acceptance criteria disagree, a gage whose failure is the operators
rather than the instrument — not to represent any real process.

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
`OP-C`), números de peça e limites de especificação são **rótulos inventados**. Não são
referências a nenhum instrumento, pessoa, peça ou especificação real, e qualquer semelhança é
coincidência.

Os sistemas de medição do gerador foram desenhados para tornar visíveis situações estatísticas
específicas — um gage cujos dois critérios de aceitação discordam, um gage cuja reprovação são os
operadores e não o instrumento — e não para representar processo real algum.

Este repositório é um portfólio de métodos. Não é um relatório sobre operação alguma.
