# VAE-001, Adendo P, item 4 — roteiro da inspeção descritiva

Fixado em 22/11/2026, antes de o responsável abrir as figuras dos oito cálculos nomeados.
Não altera o Adendo P: detalha como a inspeção do item 4 é feita.

Versão 2, de 22/11/2026. A versão 1 (commit 4807d4c, das 16:10) trazia quatro perguntas abertas. Esta traz as mesmas dimensões em cinco perguntas fechadas, as da planilha de respostas, e fixa a planilha como registro. A mudança foi feita antes de as figuras dos oito cálculos serem geradas.

## Limites

- Descrição apenas: número e tamanho das componentes, posição do diâmetro máximo e figura. Nenhuma estatística e nenhuma medida nova, nem com régua.
- Os oito foram nomeados por serem os casos extremos ou especiais. Não representam os 76.
- A inspeção não é cega: a figura traz a referência, a medida do dispositivo e o erro.
- A geometria da medida de referência não está na imagem. A descrição diz o que é compatível com o erro, não o que o causou.
- Quem olha as imagens é o responsável, radiologista. O modelo de linguagem escreveu o script e este roteiro, testou o script só em cálculos do desenvolvimento e em volumes sintéticos, e lê só o texto e a tabela de números.

## Como ler a figura

- Ciano: contorno de 200 UH, o limiar de detecção. Magenta tracejado: contorno de T = 0,225 × p95.
- Pontos vermelhos: a superfície que o dispositivo mediu. Linha e círculos amarelos: o diâmetro máximo e seus dois extremos.
- Com T abaixo de 200 UH, o magenta fica por fora do ciano. O que está entre os dois é material entre T e 200 UH, que o dispositivo deixa de fora (regra restrita à componente de 200 UH, R-17).
- Com T de 200 UH ou mais, o magenta fica por dentro do ciano. O que está entre os dois é a borda entre 200 UH e T, que a fração apara.
- As imagens públicas têm o fundo zerado abaixo de cerca de 101 UH: a borda visível mais externa é a da máscara do arquivo, não necessariamente a do cálculo.

## As mesmas cinco perguntas, para cada cálculo

Respostas fechadas, escolhidas numa lista. Cada lista tem também a opção "outro (ver observações)".

1. Forma: compacto; alongado; irregular; espiculado; laminar.
2. Estrutura: homogêneo; heterogêneo; núcleo denso e periferia tênue.
3. Os extremos do diâmetro caem em: duas faces largas; uma face larga e uma ponta fina; duas pontas finas; parte ligada por ponte estreita.
4. Além dos extremos, na direção do diâmetro: sobra cálculo visível (mediu a menos); a superfície passa do cálculo (mediu a mais); nem um nem outro.
5. Faixa entre os contornos ciano e magenta, nos extremos: não existe; cerca de um voxel; larga.

Depois, em texto livre: a resposta à pergunta específica do cálculo e as observações. Registrar também quando nada for encontrado.

## Pergunta específica de cada cálculo

Números de results/poshoc_lacrado.csv (execução única de 22/11/2026). Diâmetros em mm; entre parênteses, o erro contra a referência.

| Cálculo | Motivo no adendo | Referência | Dispositivo | Fração pura | 200 UH fixos | Máximo / p95 / T (UH) | Componentes ≥ 200 UH (voxels) | O que procurar |
|---|---|---|---|---|---|---|---|---|
| 29 | erro acima de 1 mm | 11,89 | 10,88 (−1,01) | 10,65 (−1,24) | 11,10 (−0,79) | 1231 / 1091 / 245 | 1 (418) | As três regras medem a menos. As pontas são tênues? Há cálculo visível além dos dois contornos, na direção do diâmetro? |
| 83 | erro acima de 1 mm; componentes múltiplas | 18,17 | 19,39 (+1,22) | 19,39 (+1,22) | 19,26 (+1,10) | 1217 / 747 / 168 | 2 (3028 e 1) | As três regras medem a mais: não é o limiar. A segunda componente é um voxel isolado: onde está? Os extremos caem em pontas finas ou em parte ligada por ponte? |
| 91 | erro acima de 1 mm | 22,58 | 24,04 (+1,46) | 24,04 (+1,46) | 23,73 (+1,15) | 756 / 615 / 138 | 1 (7869) | As três regras medem a mais. Os extremos caem em pontas finas, espículas ou halo de volume parcial? |
| 41 | estruvita | 13,85 | 12,87 (−0,99) | 12,87 (−0,99) | 12,60 (−1,25) | 671 / 620 / 140 | 1 (432) | As três regras medem a menos; dispositivo igual à fração pura. Há pontas tênues além do contorno magenta? Estrutura laminar ou heterogênea? |
| 88 | estruvita | 25,36 | 24,38 (−0,98) | 24,79 (−0,57) | 24,18 (−1,18) | 766 / 668 / 150 | 1 (6686) | O dispositivo mede 0,41 mm a menos que a fração pura. Nos extremos, o que há na faixa entre o ciano e o magenta? |
| 100 | componentes múltiplas | 46,03 | 45,29 (−0,75) | 45,18 (−0,86) | 45,75 (−0,29) | 1903 / 1698 / 382 | 2 (38650 e 17) | Onde está a componente de 17 voxels: além de um extremo do diâmetro, ou ao lado? Parece fragmento separado ou parte do mesmo cálculo? Como é a borda entre o ciano e o magenta nos extremos? |
| 28 | troca de categoria a 10 mm | 10,48 | 9,79 (−0,69) | 9,61 (−0,87) | 10,49 (+0,01) | 2023 / 1854 / 417 | 1 (610) | Cálculo denso: o limiar de 200 UH acerta a referência e a fração apara. A borda entre o ciano e o magenta nos extremos tem cerca de um voxel (volume parcial) ou é cálculo de fato? |
| 3 | troca de categoria a 5 mm; menor atenuação | 5,71 | 4,88 (−0,83) | 5,33 (−0,38) | 4,22 (−1,49) | 408 / 379 / 85 | 1 (35) | T fica abaixo do piso da máscara (104 UH). Só 35 voxels passam de 200 UH; a componente visível tem 75. Quanto do cálculo fica fora do contorno ciano? |

## Registro

O responsável preenche results/poshoc_item4_descricao.xlsx, uma linha por cálculo: as cinco respostas fechadas, a resposta à pergunta específica e as observações. A planilha em branco é commitada antes de as figuras dos oito serem geradas; a preenchida, depois. A linha de exemplo da planilha é do cálculo 56, do desenvolvimento, e foi escrita pelo modelo de linguagem só para mostrar o formato. O conteúdo entra no relatório dos resultados como descrição do radiologista, ao lado da tabela de results/poshoc_item4.md.

As saídas do teste no desenvolvimento que estão em results/ (poshoc_item4_desenv.*) foram geradas pelo modelo de linguagem no ambiente de teste, não pelo responsável.

## Esclarecimentos dados durante a inspeção

Não estavam no roteiro commitado antes da abertura das figuras (commit a0f6546, das 16:35). Foram dados pelo modelo de linguagem, sem ver as figuras, a pedido do responsável.

### 22/11/2026, 16:46 — o que conta como "cálculo visível" (pergunta 4 e perguntas específicas)

- Conta tudo o que não é preto. O fundo do arquivo público foi zerado abaixo de cerca de 101 UH; em água, o que resta é cálculo ou a borda borrada dele.
- O critério é contar voxels, não julgar o brilho: a janela de cinza de cada figura vai de 0 ao máximo daquele cálculo, então o mesmo valor em UH aparece mais claro num cálculo pouco atenuante e quase preto num denso.
- Uma borda de um voxel é esperada em qualquer cálculo (volume parcial) e não conta.
- Pergunta 4, olhando além de cada círculo amarelo, na direção da linha: nenhum ou um voxel não preto, "nem um nem outro"; dois ou mais, "sobra cálculo visível"; círculo no preto, fora do último voxel não preto, "a superfície passa do cálculo".
- Se os dois extremos derem respostas diferentes, vale a do extremo com mais sobra, e a diferença vai nas observações.

### 22/11/2026, 16:56 — a linha amarela nas projeções

- O diâmetro é um segmento em três dimensões. Cada projeção mostra só duas das três componentes, então a linha amarela pode parecer curta e pode não chegar à ponta da silhueta sem que haja erro. No cálculo 56, do desenvolvimento, o diâmetro de 12,46 mm tem 11,03 mm em x, 1,47 mm em y e 5,60 mm em z: a linha aparece com 5,79 mm na projeção ao longo de x, 11,13 mm ao longo de z e 12,37 mm ao longo de y.
- O comprimento não se julga na projeção: é o do título da figura, e as três componentes estão em results/poshoc_item4.md.
- Para a pergunta 4, "além do círculo, na direção da linha" inclui a fatia vizinha: olhar o voxel além do círculo na mesma fatia e também na fatia seguinte para fora (a de número menor, para o extremo que está na fatia de número menor; a de número maior, para o outro).

