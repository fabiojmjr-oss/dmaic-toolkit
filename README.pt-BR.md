# dmaic-toolkit

*[English](README.md)*

Um toolkit DMAIC, um módulo por fase. Não uma biblioteca de fórmulas estatísticas com vocabulário
Six Sigma colado — um conjunto de ferramentas que respondem cada uma a uma decisão que o projeto
tem de tomar, e que **se recusam a devolver um número quando as premissas por trás dele não
valem.**

Toda figura citada em qualquer README daqui é re-derivada pela suíte de testes. Uma mudança que
move um número publicado quebra o build em vez de deixar o texto silenciosamente errado.

**Nenhum dado de empregador, cliente ou terceiro é utilizado em qualquer parte deste
repositório.** Toda tabela é produzida por um gerador com semente cujos parâmetros estão
escritos. Ver [`DISCLAIMER.md`](DISCLAIMER.md).

## Fases

| Módulo | Fase | Decisão que habilita |
| --- | --- | --- |
| [`dmaic.measure`](src/dmaic/measure/README.md) | Measure | Este sistema de medição pode ser usado, o que o corrigiria, e ele sustenta a especificação? |

O [`docs/ROADMAP.md`](docs/ROADMAP.md) lista as fases ainda não construídas, e explica por que a
fase Control é deliberadamente mais estreita do que parece.

## Instalação

```bash
make install     # instalação editável com as ferramentas de desenvolvimento
make check       # lint, formatação, tipos e a suíte rápida - o que barra um push
make claims      # re-deriva todo número citado em um README
```

## O que a onda 1 encontrou

Uma análise de sistema de medição em três gages sintéticos, cada um um estudo cruzado de 10 peças
× 3 operadores × 3 réplicas, decomposto por ANOVA de dois fatores com efeitos aleatórios.

| Gage | % contribuição | % variação do estudo | % tolerância | ndc | veredito |
| --- | --- | --- | --- | --- | --- |
| `BALANCA-01` | 0,40 | 6,29 | 5,69 | 22 | aceitável |
| `PAQUIMETRO-02` | **2,64** | **16,24** | **63,58** | 8 | inaceitável |
| `INSPECAO-03` | 40,99 | 64,02 | 62,55 | 1 | inaceitável |

**`PAQUIMETRO-02` é um gage lido de três formas.** 2,64, 16,24 e 63,58 são o mesmo sistema de
medição. %contribuição é razão de variâncias, %variação do estudo é razão de desvios-padrão, e
%tolerância compara o gage à especificação em vez de às peças. As faixas de aceitação de 10% / 30%
foram escritas para a do meio — então ler contribuição contra elas transforma um gage inaceitável
em excelente, porque contribuição é a variação do estudo ao quadrado, e elevar uma fração ao
quadrado a empurra para zero.

**Agrupar a interação peça × operador inverte o diagnóstico.** A regra da AIAG descarta o termo
quando p > 0,25. Forçar o agrupamento no `PAQUIMETRO-02` quase não move o GRR — 16,24 para 14,63 —
enquanto manda a reprodutibilidade a exatamente zero e inverte a fonte dominante das pessoas para
o instrumento. A consequência cara não são os 1,6 pontos de GRR; é o investimento que o número
justifica.

**Separar o GRR é o que torna um estudo reprovado acionável.** `INSPECAO-03` reprova a 64%, com
reprodutibilidade 3,2× a repetibilidade. O instrumento não é o problema, e substituí-lo — a
resposta mais comum a um estudo reprovado, e a que vem com nota fiscal — mudaria quase nada.

## Exemplos

| Script | O que mostra |
| --- | --- |
| [`01_is_the_gage_good_enough.py`](examples/01_is_the_gage_good_enough.py) | Três gages, três vereditos, e os dois critérios de aceitação discordando em um deles |

## Verificação

**33 testes, 95% de cobertura de statements, separados por custo.** 28 deles rodam em cerca de
cinco segundos — e isso, com os linters e a checagem de tipos, é o que barra um push. Os 5
restantes re-derivam toda figura citada em um README e rodam todo script de exemplo.

A ANOVA do gage é verificada contra um desenho 2×2×2 cujas somas de quadrados são inteiras (242,
50, 2 e 8, fechando em 302), e não apenas contra a própria saída. Verificações independentes de
propriedade confirmam que réplicas idênticas dão repetibilidade exatamente zero, que operadores
idênticos dão reprodutibilidade zero, que %contribuição é exatamente %variação do estudo ao
quadrado, e que mudar o multiplicador sigma de 5,15 para 6,0 escala a %tolerância por exatamente
1,1650 sem tocar na %variação do estudo.

## Relacionado

Controle estatístico de processo — cartas de controle, regras de Nelson, capabilidade contra sigma
intra-subgrupo — vive num repositório irmão e não aqui. Dois repositórios com o mesmo código sob
um nome leriam como enchimento.

## Licença

MIT. Ver [`LICENSE`](LICENSE).
