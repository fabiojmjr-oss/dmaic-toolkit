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
| [`dmaic.define`](src/dmaic/define/README.md) | Define | Este gap é real, qual janela de histórico o produziu, e a decomposição dele fecha? |
| [`dmaic.measure`](src/dmaic/measure/README.md) | Measure | Este sistema de medição distingue as peças, ele está certo, quanto tempo isso dura, e quanto custa estar errado? |
| [`dmaic.analyze`](src/dmaic/analyze/README.md) | Analyze | De quanto dado este teste precisa, ele mantém a taxa de erro que alega, e o experimento consegue separar os efeitos sobre os quais está sendo perguntado? |
| [`dmaic.improve`](src/dmaic/improve/README.md) | Improve | Quanto desta melhoria é do projeto, alguma parte foi artefato de como os sites foram escolhidos, e quanto da economia é caixa? |
| [`dmaic.control`](src/dmaic/control/README.md) | Control | O que este plano de amostragem de fato pega, o que ele deixa passar, e o que a inspeção comprou? |

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

### Onda 3 — as premissas por trás do p-valor

Dois grupos sorteados com a mesma média, então **toda rejeição abaixo é erro tipo I** e a taxa
nominal é 5% por construção. 20.000 réplicas.

| Cenário | t agrupado | Welch | fluxograma | Mann-Whitney |
| --- | --- | --- | --- | --- |
| normal, dispersão igual, n 20 / 20 | 0,0479 | 0,0477 | 0,0478 | 0,0481 |
| normal, dispersão 1:3, n 10 / 30 | **0,0038** | 0,0478 | 0,0432 | 0,0150 |
| normal, dispersão 3:1, n 10 / 30 | **0,2130** | 0,0507 | **0,0628** | **0,1270** |
| assimétrica, dispersão 3:1, n 10 / 30 | **0,2331** | **0,1112** | **0,1454** | **0,2850** |

**O fluxograma ensinado — testar normalidade, testar variância, escolher conforme — é
mensuravelmente pior que pular os checks e usar Welch.** 6,28% contra 5,07% no caso que importa,
porque ele herda a inflação do teste agrupado sempre que o pré-teste de variância não dispara. Um
pré-teste não protege um procedimento, ele o lava.

**O t agrupado erra nas duas direções, e qual delas depende de contabilidade.** 21,30% com a
dispersão maior no grupo menor; 0,38% quando a mesma desigualdade está invertida. Nada no processo
muda — só qual grupo por acaso era o maior. O Welch mantém 4,77% a 5,07% em todo cenário normal e
não custa nada sob igualdade.

**Recorrer a um teste de postos piora.** Mann-Whitney roda a 12,70% aqui e 6,63% mesmo com grupos
balanceados: ele não é um teste t livre de distribuição, testa outra hipótese, e dispersão desigual
o quebra também.

**E o check de normalidade é menos informativo exatamente onde mais importa.** Em cinco por grupo
uma assimetria real é detectada 16,3% das vezes, então o check aprova — e é ali que o teste está
mais distorcido, a 2,40%. Em trezentos ela é detectada sempre, então o check reprova e manda o
projeto para um teste de postos — e ali o teste já está perfeito, a 5,22%. O veredito é
anticorrelacionado com a necessidade dele, porque as duas coisas são consequência de n pequeno.

**O diagnóstico não consegue ver o que quebra o teste.** A assimetria populacional é 3,2629; em dez
observações o teto algébrico de uma assimetria amostral é 2,667, então o estimador não consegue
reportar a verdade nem em princípio, e a sinalização dispara 39,8% das vezes. O diagnóstico de
dispersão falha do mesmo jeito: sorteada de uma razão real de exatamente 3,00, a razão amostral tem
90% central de 1,152 a 6,762. Juntos, a sinalização de regime pega o caso ruim **75,0% das vezes** —
um erro em quatro, e é por isso que o `compare_means` usa Welch sem condição e devolve os checks
como evidência, não como portão.

### Onda 4 — planejamento de experimentos

Um experimento sintético de forno de cura: quatro fatores, dezesseis corridas, resistência ao
cisalhamento em MPa. O gerador declara o que existe no processo, e **dois dos quatro fatores são
exatamente zero** — tempo de cura e lote de resina. As dezesseis corridas são medidas uma vez;
cada desenho abaixo lê as linhas que teria rodado, então nada varia entre eles além de quais das
mesmas corridas foram mantidas.

| Termo | Real | 2⁴ completo, 16 corridas | 2^(4-1) `D=ABC`, 8 corridas | 2^(4-1) `D=AB`, 8 corridas |
| --- | --- | --- | --- | --- |
| A temperatura | +12,00 | 12,5810 | 11,8174 | 13,1256 |
| B pressao | +5,00 | 4,9727 | 4,5785 | 5,8547 |
| C tempo de cura | 0,00 | 0,2853 | −0,3577 | −0,4082 |
| D lote de resina | 0,00 | 1,5494 | 0,5307 | **9,4067** |
| AB | +8,00 | 7,8573 | **7,7678** | 9,4067 |
| Resolução | | completo | IV | **III** |

**Um desenho resolução III não perde uma interação, ele a premia a um fator que não faz nada.** O
lote de resina tem efeito exatamente zero e volta em 9,4067 — a segunda maior cifra do estudo,
1,88 vez o efeito real da pressão, e 2,63 vezes o menor efeito que oito corridas conseguiriam
detectar. Não é marginal e não parece ruído. As duas frações custam as mesmas oito corridas, leem o
mesmo experimento, e ordenam os fatores de forma diferente: `D=ABC` dá A, B, D, C e `D=AB` dá A,
**D**, B, C. Só o gerador muda, e ele é de graça.

**Alias é uma soma exata, não ruído adicional.** A estimativa da fração é a soma aritmética das
estimativas que o desenho completo dá aos termos aliasados — `D + AB` é 1,5494 + 7,8573 = 9,4067,
reproduzindo a 5,3e-15 em todo par de alias das duas frações. É por isso que `D=ABC` funciona: ele
também soma dois números, e um deles por acaso é zero. Ele recupera a interação em 7,7678 contra
os 7,8573 do desenho completo, uma diferença de 0,0895 MPa num efeito de 8, com metade das
corridas.

**Limite de detecção protege contra ruído e não diz nada sobre viés.** Na dispersão corrida a
corrida deste processo, 1,5 MPa, oito corridas veem 3,5711 MPa e dezesseis veem 2,2600. A maior
estimativa puramente espúria do desenho completo é 1,5494, abaixo do limite, então um projeto
corretamente a deixaria em paz. O falso 9,4067 está a 2,63 vezes o limite, porque é um efeito real
na coluna errada e um limite de detecção não tem opinião sobre colunas.

**E a resolução vem da relação definidora, não dos geradores.** `D=ABC` e `E=BCD` são os dois
geradores de quatro letras; as palavras deles multiplicam para `AE`, então dois fatores
compartilham uma coluna e o desenho é resolução II. O `fractional_factorial` recusa construí-lo em
vez de devolver uma folha de corridas que parece correta.

### Onda 5 — exatidão: o estudo aprovou e o gage está errado

Os mesmos três gages, agora medidos contra cinco padrões calibrados cada, doze leituras por
padrão. O estudo cruzado da onda 1 **não consegue ver nada disso**: toda figura AIAG é calculada a
partir de diferenças entre leituras, então somar uma constante a todas não muda nada. Deslocar os
três gages em 1000 unidades move a maior entre `grr`, `pct_study`, `pct_contribution`,
`pct_tolerance` e `ndc` em no máximo **9,2e-12** — invariante, não pouco sensível.

| Gage | Estudo cruzado | Viés no nominal | p | % da tolerância | Inclinação | Amplitude do viés | Amplitude % da tolerância |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `BALANCA-01` | **aceitável**, 5,69% tol | **3,9076 g** | 0,0000 | **7,82** | 0,0011 | 0,0456 | 0,09 |
| `PAQUIMETRO-02` | inaceitável, 63,58% tol | 0,0058 mm | 0,7113 | 0,58 | **−0,2205** | **0,1764 mm** | **17,64** |
| `INSPECAO-03` | inaceitável, 62,55% tol | −0,0521 µm | 0,8721 | 0,13 | −0,0132 | 0,4231 | 1,06 |

**Precisão e exatidão são independentes, e cada gage prova um canto diferente disso.** O
`BALANCA-01` passou no estudo cruzado nos dois critérios e é o pior gage dos três: o viés dele é
7,82% da tolerância contra os 5,69% que o estudo de GRR inteiro mediu, então o erro que ninguém
procurou é maior que o erro que todos calcularam. O `PAQUIMETRO-02` **não tem viés nenhum no
nominal** — p = 0,71 — e a verificação em um ponto que todo procedimento prescreve aprova um gage
cujo desvio oscila 17,64% da tolerância ao longo da faixa, em direções opostas nos dois limites de
especificação. O `INSPECAO-03` reprova na precisão e é exato, então "recalibra" não mudaria nada.

**O viés se converte em peças.** Com desvio-padrão de processo de 8,0 g contra uma tolerância de
50 g, 99,8222% da produção é conforme e o sigma do próprio gage é 0,4743:

| Caso | Viés | Banda de guarda | Peças boas refugadas | Peças ruins expedidas |
| --- | --- | --- | --- | --- |
| Calibrado | 0,0000 | — | 161 ppm | 128 ppm |
| **Como encontrado** | 3,9076 | — | **3.356 ppm** | **734 ppm** |
| Como encontrado, com banda | 3,9076 | 3,5890 | **13.618 ppm** | 128 ppm |

Refugo multiplicado por 20,8 e escapes por 5,7, num gage cujo estudo disse *aceitável*. E o
paliativo é pior que a correção: apertar a aceitação em 3,5890 g traz os escapes exatamente de
volta à taxa calibrada e paga com 13.618 ppm de peças conformes — **84,5 vezes** o refugo
calibrado, 1,36% de tudo que é produzido. Uma calibração não custa nenhum dos dois números.

**"O intervalo contém zero" não é regra de aceitação.** Mantenha o viés em 0,5 g — 1% da
tolerância, imaterial — e varie apenas a precisão do gage, em 4.000 estudos simulados de doze
leituras por linha:

| Repetibilidade do gage | 6σ como % da tolerância | Viés ÷ sd | Chamado significativo |
| --- | --- | --- | --- |
| 0,20 | 2,40 | 2,5000 | **1,0000** |
| 0,56 | 6,72 | 0,8929 | 0,7983 |
| 1,50 | 18,00 | 0,3333 | 0,1893 |
| 4,00 | 48,00 | 0,1250 | **0,0717** |

Quanto melhor o gage, mais certamente ele é reprovado por um desvio que não importa — e quanto
pior o gage, mais facilmente ele passa. O veredito acompanha a precisão do gage e não a
consequência, a mesma anticorrelação com a utilidade que a onda 3 achou no pré-teste de
normalidade, e é por isso que o `BiasStudy` reporta significância e materialidade como dois
achados separados.

### Onda 6 — a janela em que o estudo foi rodado, e o plano que vem depois

Duas perguntas que ninguém anota: **quanto tempo uma resposta de medição dura** e **o que um plano
de amostragem de fato garante**. As duas acabam sendo respondidas por um número para o qual o
formulário não tem campo.

**Um estudo de gage é um retrato e nada registra a data.** `BALANCA-01`, acompanhado desde o dia em
que foi calibrado — quatro leituras num padrão a cada cinco dias, por sessenta dias:

| Figura | Valor |
| --- | --- |
| Deriva recuperada | **+0,105428 g/dia** (embutida: +0,10) |
| Desvio deixado no dia 0 | −0,0932 g — a calibração em si estava boa |
| Desvio no dia 60 | **+6,2325 g**, 12,47% da tolerância |
| Intervalo até 5% da tolerância | **22,8 dias** |
| Dispersão residual em torno da reta | 0,5894 g, contra os 0,56 do próprio gage |

O desvio de 4 g que a onda 5 achou chega no **dia 37,9** nesta taxa. Um viés constante e uma deriva
medida tarde são a mesma leitura e não o mesmo problema: uma tara se remove uma vez, uma deriva
compra um intervalo.

**E a agenda de um estudo cruzado decide em que termo a deriva cai.** O mesmo estudo 10 × 3 × 3,
espalhado por duas semanas, com **leituras idênticas e dias idênticos** — só o mapeamento de dias
muda:

| Agenda | EV | AV | GRR | % estudo | ndc | Fonte dominante | Veredito |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Um operador por dia | **0,6430** | **1,0081** | 1,1957 | 12,68 | 11 | **reprodutibilidade** | condicional |
| Todo operador todo dia | 0,9161 | 0,3829 | 0,9929 | 10,56 | 13 | repetibilidade | condicional |
| Deriva removida | 0,6430 | 0,4010 | 0,7578 | 8,08 | 17 | repetibilidade | **aceitável** |

Dar a cada operador o seu dia infla a reprodutibilidade em **2,51×** e deixa a repetibilidade
intacta até a quarta decimal. O calendário, reportado como sendo das pessoas — e um projeto lendo
esse estudo retreinaria três operadores que não fizeram nada errado. Intercalar põe a mesma deriva
na repetibilidade (1,42×) e deixa a estimativa dos operadores intacta, que é o lugar certo dela e
ainda não é uma repetibilidade. As duas agendas com deriva voltam *condicional* onde o instrumento
em qualquer dia único é *aceitável*: o veredito do próprio estudo depende de quanto tempo ele levou.

**Um plano de amostragem é uma curva, e "inspecionar dez por cento" é o plano cujo tamanho de
amostra foi escolhido por uma decisão de expedição.** Lotes bons 0,5% defeituosos, excursões 4,0%:

| Tamanho do lote | Regra 10%, n | Aceita lotes bons | Aceita excursões | n=80 bons | n=80 excursões |
| --- | --- | --- | --- | --- | --- |
| 100 | 10 | 1,000000 | **0,651631** | 1,000000 | 0,001236 |
| 1.000 | 100 | 0,589832 | 0,013520 | 0,658507 | 0,033206 |
| 20.000 | 2.000 | **0,000026** | ~0 | 0,669115 | 0,037917 |

A mesma regra escrita vai de aceitar duas excursões em três a rejeitar 99,997% de material
perfeitamente bom. Uma amostra fixa de oitenta mantém as duas cifras estáveis.

**Um nível de qualidade aceitável é risco do produtor.** `n=125, c=3` citado como AQL 1,0% rejeita
2,7% dos lotes a 1% de defeituosos — exatamente como anunciado — e aceita **47,1%** dos lotes a 3%.
E aceitação zero não é a opção rígida: casada ao mesmo risco do produtor exige uma amostra de
**três** e aceita 88,5% dos lotes de 4%, enquanto no mesmo tamanho de amostra rejeita **73,9%** da
produção boa. A discriminação vem do tamanho da amostra, não do número de aceitação.

**O que cada plano comprou**, nos mesmos 200 lotes (1.478 unidades defeituosas no total):

| Plano | Unidades inspecionadas | Excursões pegas | Lotes bons rejeitados | Unidades defeituosas expedidas |
| --- | --- | --- | --- | --- |
| 10% do lote, c=0 | 20.000 | **12/12** | **70** | 543 |
| n=125 c=3 (AQL 1,0%) | 25.000 | 9/12 | 0 | **1.098** |
| Desenhado para 1% vs 4% | 37.800 | **10/12** | **1** | 1.066 |
| Sem inspeção | 0 | 0/12 | 0 | 1.478 |

O plano publicado inspeciona 25.000 unidades e expede três quartos dos defeitos. O plano que pega
todas as excursões faz isso pondo em quarentena mais de um terço da produção boa — não é
discriminante, é duro. Amostragem separa lotes; não muda o que tem dentro deles.

### Onda 7 — a economia foi sua, e é caixa?

Vinte sites ao longo de vinte e quatro meses, cinco melhorados a partir do mês treze. O gerador
declara o efeito que aplicou, **−5,00 BRL por pedido**, e a tendência que já estava correndo,
**−0,40 por período** — que move o mensurando −4,80 nos doze períodos após o corte, em sites
tratados e não tratados igualmente.

| Base | Estimativa | Sites de comparação | Atribuível | Vezes a verdade |
| --- | --- | --- | --- | --- |
| Antes e depois | **−10,0637** | 0 | não | **2,01×** |
| Diferença em diferenças | −4,2241 | 15 | sim | 0,84× |
| A verdade | −5,0000 | — | — | 1,00× |

**O projeto reporta o dobro do que entregou, e o excedente é o calendário.** Um número
antes-e-depois não é impreciso sobre o benefício; é sistematicamente errado numa direção, e a
direção é sempre lisonjeira. Um grupo de comparação resolve sem modelar nada: a diferença em
diferenças fica em −4,2241 com intervalo de **−5,2545 a −3,1938**, que contém a verdade. Está errada
por azar e não por construção, e o intervalo diz por quanto.

**E o que um projeto mostra quando não faz nada.** Sem efeito e sem tendência em nenhuma linha
abaixo — a única coisa acontecendo é quais sites entraram no charter, e sobre quantos períodos de
histórico essa escolha foi feita:

| Períodos de histórico | Piores desempenhos selecionados | Selecionados ao acaso |
| --- | --- | --- |
| 1 | **−4,3401** | −0,0524 |
| 3 | −1,6997 | −0,0262 |
| 12 | −0,4562 | +0,0005 |
| 24 | −0,2294 | −0,0022 |

Abrir projeto sobre um único mês ruim fabrica −4,34 do nada: **87% de uma melhoria real de cinco
unidades, em sites onde nada foi feito.** Seleção aleatória devolve zero em toda linha, e essa é a
verificação de controle — o artefato está na regra de seleção, não na aritmética. E o remédio é de
graça: um ano de histórico leva isso a −0,46.

**Então o dinheiro.** 60.000 pedidos por período nos sites tratados, doze períodos, 35% do custo
unitário evitável como caixa, um projeto que custou 250.000:

| Base | Efeito | Bruto | Caixa | Líquido | Payback |
| --- | --- | --- | --- | --- | --- |
| Contabilizado no antes e depois | −10,06 | **7.245.895** | 2.536.063 | 2.286.063 | 1,18 |
| Diferença em diferenças | −4,22 | 3.041.368 | 1.064.479 | 814.479 | 2,82 |
| A verdade | −5,00 | 3.600.000 | **1.260.000** | 1.010.000 | 2,38 |

**O charter contabiliza 7.245.895 e o projeto produziu 1.260.000 de caixa — 5,75×.** Esse
descasamento é um produto, não um mistério: **2,01× de atribuição e 2,86× da parcela que é caixa e
não capacidade**, e 2,01 × 2,86 = 5,75 exatamente. Dois fatores, nenhum escrito em lugar algum da
documentação do projeto. O `BenefitCase` reporta bruto e caixa separados e se recusa a somá-los.

### Onda 8 — o charter, como aritmética

A imagem espelhada da onda 7. Um projeto é aberto **a partir de** um baseline recente e **em direção
a** o desempenho observado do melhor site — e o pior desempenho de uma janela curta estava em parte
com azar e volta a subir, enquanto o melhor estava em parte com sorte e volta a descer. **Um charter
toma a estimativa mais inflada disponível nas duas pontas do gap, e os dois erros se somam.**

Os mesmos doze meses, lidos como quatro baselines:

| Janela | Média | Melhor | Pior | Gap ao melhor | Pior ao melhor |
| --- | --- | --- | --- | --- | --- |
| 1 | 94,7895 | **75,9952** | **120,3974** | **18,7943** | **44,4022** |
| 3 | 95,7523 | 81,8822 | 112,2490 | 13,8701 | 30,3668 |
| 12 | 96,9307 | 79,4887 | 109,9823 | 17,4420 | 30,4936 |

**Um charter pode citar um gap de 18,79 ou de 13,87 do mesmo dado**, dependendo de uma janela para a
qual nenhum template tem campo. E a dispersão entre sites — a cifra que justifica um programa de
harmonização — lê **46% maior em um período do que em doze**.

**Quanto de um gap de entitlement é o melhor site com um bom período**, simulado porque o nível real
de cada site é exatamente o que um charter não tem:

| Janela de histórico | Gap do charter | O gap que existe | Gap encolhido | Inflação |
| --- | --- | --- | --- | --- |
| 1 | **18,6274** | 14,8561 | 11,9215 | **3,7713** |
| 3 | 16,2542 | 14,9069 | 13,6878 | 1,3474 |
| 12 | 15,2783 | 14,9599 | 14,5942 | 0,3184 |
| 24 | 15,2348 | 15,0210 | 14,8859 | 0,2137 |

**Em um histórico de um período o charter alega 18,63 onde existem 14,86: 25% do gap não existe** —
não porque alguém mediu mal, mas porque o mínimo de vinte médias ruidosas fica abaixo do mínimo de
vinte níveis reais, sempre, e por uma quantidade previsível. Encolher o melhor site em direção à
média erra para o outro lado, e **a verdade fica entre as duas em toda janela testada**: cite uma e
você escolheu uma direção, cite as duas e você declarou uma faixa.

**E a árvore que explica o gap.** Sete folhas alegando 19,60 contra um gap de 17,44 — **1,12×**,
então a mesma economia está sob mais de um nome — e **22% da alegação está sob folhas que não nomeiam
mensurando**, que é a parcela impossível de verificar depois que o projeto encerra. O benefício do
charter é calculado pelo mesmo `BenefitCase` com que a fase Improve o audita, então a promessa e a
verificação não podem discordar de aritmética — só de realidade.

## Exemplos

| Script | O que mostra |
| --- | --- |
| [`01_is_the_gage_good_enough.py`](examples/01_is_the_gage_good_enough.py) | Três gages, três vereditos, e os dois critérios de aceitação discordando em um deles |
| [`02_could_the_pilot_have_found_it.py`](examples/02_could_the_pilot_have_found_it.py) | Três pilotos, três resultados não-significativos, três efeitos reais |
| [`03_which_test_and_can_it_be_trusted.py`](examples/03_which_test_and_can_it_be_trusted.py) | O fluxograma ensinado, medido contra sempre usar Welch. Ele perde |
| [`04_the_generator_decides_the_conclusion.py`](examples/04_the_generator_decides_the_conclusion.py) | Um experimento, três desenhos, e um fator que não faz nada reportado como o segundo maior |
| [`05_the_gage_passed_and_it_is_wrong.py`](examples/05_the_gage_passed_and_it_is_wrong.py) | O gage que o estudo aprovou, medido contra padrões, e quanto o viés dele custa em peças |
| [`06_the_study_took_two_weeks.py`](examples/06_the_study_took_two_weeks.py) | Um gage derivando: o intervalo de calibração, e a agenda que culpa os operadores pelo calendário |
| [`07_what_the_sampling_plan_guarantees.py`](examples/07_what_the_sampling_plan_guarantees.py) | Cinco planos de amostragem nos mesmos duzentos lotes, e o que cada um de fato comprou |
| [`08_was_the_saving_yours.py`](examples/08_was_the_saving_yours.py) | Um projeto que entregou 5,00 por pedido e reportou 10,06, e o dinheiro que vem disso |
| [`09_the_charter_that_computes.py`](examples/09_the_charter_that_computes.py) | Um charter medido da ponta errada do baseline, em direção à ponta errada da meta |

## Verificação

**233 testes, 96% de cobertura de statements, separados por custo.** 199 deles rodam em cerca de
nove segundos, e a sequência inteira do `make check` — linters, tipos, cobertura e tudo — em cerca de
onze. É isso que barra um push. Os 34 restantes re-derivam toda figura citada em um README e rodam
todo script de exemplo, em cerca de doze segundos.

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

A aritmética de exatidão é ancorada do mesmo jeito. A alegação de invariância é verificada como
igualdade dentro do ponto flutuante e não dentro de uma tolerância, porque é álgebra e não
medição. Uma reta ajustada a pontos que estão sobre uma reta tem de voltar exata, um gage perfeito
tem de não classificar nada errado, um processo centrado tem de errar simetricamente nas duas
direções de viés, e a banda de guarda tem de voltar por round-trip à taxa de escape para a qual
foi resolvida. A simulação de significância é ancorada no próprio controle: com viés zero a
estatística t não depende do desvio-padrão, então as quatro linhas têm de devolver a taxa de
rejeição **idêntica** — quatro números apenas parecidos significariam que as linhas não são
comparáveis.

A aritmética de desenho é conferida contra um 2² cujos efeitos se leem direto de quatro números
(respostas 10, 20, 30, 60 dão A = 30, B = 20, AB = 10), contra a ortogonalidade de toda coluna até
cinco fatores, e contra a identidade da soma exata: a estimativa de uma fração tem de igualar a
soma das estimativas que o desenho completo dá aos termos aliasados, e iguala a 5,3e-15 em vez de
a uma tolerância. As duas estimativas de um par aliasado são verificadas como **idênticas** e não
como próximas, porque são a mesma coluna e qualquer diferença significaria contraste errado.

As simulações são ancoradas nos próprios casos de controle, que é a única forma de testar um
resultado de Monte Carlo: onde toda premissa vale, cada um dos quatro procedimentos tem de devolver
os 5% nominais, e o check de normalidade em dado genuinamente normal tem de disparar exatamente no
próprio alfa. Se qualquer dos controles derivar, toda outra figura daquela tabela está errada na
mesma direção e nenhuma delas de forma detectável.

## Relacionado

Controle estatístico de processo — cartas de controle, regras de Nelson, capabilidade contra sigma
intra-subgrupo — vive num repositório irmão e não aqui. Dois repositórios com o mesmo código sob
um nome leriam como enchimento.

## Licença

MIT. Ver [`LICENSE`](LICENSE).
