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
| [`dmaic.analyze`](src/dmaic/analyze/README.md) | Analyze | De quanto dado este teste precisa, e o que um resultado não-significativo de fato descartou? |

O [`docs/ROADMAP.md`](docs/ROADMAP.md) lista as fases ainda não construídas, e explica por que a
fase Control é deliberadamente mais estreita do que parece.

## Instalação

```bash
make install     # instalação editável com as ferramentas de desenvolvimento
make check       # lint, formatação, tipos e a suíte rápida - o que barra um push
make claims      # re-deriva todo número citado em um README
```

## O que as ondas encontraram

### Onda 1 — análise do sistema de medição

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

### Onda 2 — poder e tamanho de amostra

Três pilotos, cada um dimensionado como projetos são de fato dimensionados: pelo que era
conveniente coletar. O gerador declara o efeito que plantou, o que é a vantagem do dado sintético
aqui — um projeto real não distingue efeito perdido de efeito ausente.

| Ensaio | Efeito observado | Efeito real | p-valor | Poder p/ o efeito real | n rodado | n necessário |
| --- | --- | --- | --- | --- | --- | --- |
| `PILOTO-CICLO` | −0,29 min | −4,00 min | 0,9234 | **0,2456** | 30 | 143 |
| `PILOTO-SETUP` | −2,77 min | −6,00 min | 0,2345 | 0,7905 | 5 | 6 |
| `PILOTO-REFUGO` | −3,50 pts | −2,50 pts | 0,2152 | **0,1702** | 200 | **1.568** |

**Os três são não-significativos. Os três tinham efeito real.** Três erros tipo II, cada um
falhando por um motivo diferente. O `PILOTO-CICLO` tinha 24,6% de chance de achar o próprio efeito
e uma diferença detectável de 8,83 minutos contra uma verdade de 4 minutos. O `PILOTO-SETUP` estava
bem desenhado, com 79,1% de poder, e errou de todo jeito — que é o que 80% de poder *significa*,
uma falha em cada cinco por construção. E o `PILOTO-REFUGO` observou melhoria **maior** que a que
existia e ainda assim não conseguiu prová-la, porque detectar 2,5 pontos sobre uma taxa de refugo
de 8% exige 1.568 unidades por braço.

**A fórmula de tamanho de amostra do livro é inofensiva para a maioria dos estudos.** Medida contra
o cálculo exato com t não-central, ela erra por uma observação por grupo em toda a faixa prática.
Onde morde é a corrida de confirmação pequena: em um efeito de dois desvios-padrão ela pede 4 por
grupo contra os 6 necessários e entrega 66% de poder.

**Poder post-hoc é aritmética sobre o p-valor.** O poder observado é função estritamente monótona
dele, e em `p = α = 0,05` o poder observado é 0,5035 — convergindo para um meio conforme o estudo
cresce (0,5114 em n=10, 0,5002 em n=500). Então "tivemos só 48% de poder" é outra forma de escrever
"p ficou pouco acima de 0,05", e citar um para explicar o outro é circular.

## Exemplos

| Script | O que mostra |
| --- | --- |
| [`01_is_the_gage_good_enough.py`](examples/01_is_the_gage_good_enough.py) | Três gages, três vereditos, e os dois critérios de aceitação discordando em um deles |
| [`02_could_the_pilot_have_found_it.py`](examples/02_could_the_pilot_have_found_it.py) | Três pilotos, três resultados não-significativos, três efeitos reais |

## Verificação

**74 testes, 93% de cobertura de statements, separados por custo.** 66 deles rodam em cerca de
quatro segundos e meio, e a sequência inteira do `make check` — linters, tipos, cobertura e tudo —
em menos de seis. É isso que barra um push. Os 8 restantes re-derivam toda figura citada em um
README e rodam todo script de exemplo, em menos de dois segundos.

A ANOVA do gage é verificada contra um desenho 2×2×2 cujas somas de quadrados são inteiras (242,
50, 2 e 8, fechando em 302), e não apenas contra a própria saída. Verificações independentes de
propriedade confirmam que réplicas idênticas dão repetibilidade exatamente zero, que operadores
idênticos dão reprodutibilidade zero, que %contribuição é exatamente %variação do estudo ao
quadrado, e que mudar o multiplicador sigma de 5,15 para 6,0 escala a %tolerância por exatamente
1,1650 sem tocar na %variação do estudo.

A aritmética de poder é ancorada do mesmo jeito: o poder em efeito zero iguala exatamente o nível
de significância, a diferença detectável volta por round-trip ao poder para o qual foi resolvida, e
o resultado da t não-central é conferido contra um recálculo a partir das primitivas do scipy, não
contra a própria saída do wrapper. Toda tabela do gerador também é fixada — adicionar a onda 2
deixou o estudo de gage da onda 1 byte a byte idêntico, que é para isso que serve a disciplina de
ordem de fluxo.

## Relacionado

Controle estatístico de processo — cartas de controle, regras de Nelson, capabilidade contra sigma
intra-subgrupo — vive num repositório irmão e não aqui. Dois repositórios com o mesmo código sob
um nome leriam como enchimento.

## Licença

MIT. Ver [`LICENSE`](LICENSE).
