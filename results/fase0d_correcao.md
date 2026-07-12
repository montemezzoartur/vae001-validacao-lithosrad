# VAE-001 - Fase 0d: correcao do desalinhamento e divisao refeita

## 1. ACHADO 4 - magnitude do desalinhamento

- Junção POSICIONAL (.mat linha i <-> CSV linha i):
  - discrepância de VOLUME  > 0,004 mL: **0 de 101**
  - discrepância de DIÂMETRO > 0,01 mm: **53 de 101**
  - discrepância máxima de diâmetro: **5.69 mm**

O volume não denuncia o problema porque ambas as tabelas estão ordenadas
por volume crescente, com muitos empates (0,10 mL ocorre 13x; 0,20 mL, 8x).
Dentro de cada bloco de volume idêntico, a ordem difere entre os arquivos.

**Fonte autoritativa: `gt_vol` e `gt_diam` do `.mat`** — vêm no mesmo struct
que a imagem e, portanto, não podem estar desalinhados em relação a ela.

## 2. Recuperação da composição (StoneType)

A composição existe apenas no CSV. Tentativa de rejunção pelo par
(Volume, Diameter), com tolerância de ±0,006 (volume) e ±0,01 (diâmetro).

| Situação | n |
|---|---|
| Casamento único (1 candidato) | 100 |
| Múltiplos candidatos, todos com a mesma composição | 0 |
| Múltiplos candidatos, composições CONFLITANTES (ambíguo) | 1 |
| Nenhum candidato (falha de junção) | 0 |

- Composição atribuída com confiança: **58 de 101**
- Ambíguos ou irrecuperáveis: **1 de 101**

Cálculos sem composição confiável são tratados como `n.d.` e NÃO podem
sustentar estratificação por composição. Ver Seção 5.

**Distribuição da composição recuperada:**

```
stone_type
n.d.                          43
cystine                       23
brushite                      17
uric acid                      8
calciumoxalate-dihydrate       6
struvite                       2
calciumoxalate-monohydrate     2
```

## 3. Divisão pré-registrada, refeita com `gt_diam` do `.mat`

Semente: **20260712** (mantida). Estratificação por `gt_diam`.

| Estrato | Desenvolvimento | Lacrado | Total |
|---|---|---|---|
| 5-10 mm | 11 | 33 | 44 |
| 10-20 mm | 10 | 30 | 40 |
| >20 mm | 4 | 13 | 17 |
| **TOTAL** | **25** | **76** | **101** |

**Estrato primário (≥ 10 mm) no conjunto lacrado: 43**

**Balanço de composição entre os conjuntos:**

```
grupo                       DESENV  LACRADO  All
stone_type                                      
brushite                         3       14   17
calciumoxalate-dihydrate         1        5    6
calciumoxalate-monohydrate       0        2    2
cystine                          9       14   23
n.d.                             8       35   43
struvite                         0        2    2
uric acid                        4        4    8
All                             25       76  101
```

**IDs (do `.mat`, 1-based):**

- DESENVOLVIMENTO (25): [1, 2, 12, 13, 15, 16, 18, 21, 23, 26, 40, 44, 49, 53, 54, 55, 56, 67, 80, 81, 87, 90, 92, 95, 96]

- LACRADO (76): [3, 4, 5, 6, 7, 8, 9, 10, 11, 14, 17, 19, 20, 22, 24, 25, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 41, 42, 43, 45, 46, 47, 48, 50, 51, 52, 57, 58, 59, 60, 61, 62, 63, 64, 65, 66, 68, 69, 70, 71, 72, 73, 74, 75, 76, 77, 78, 79, 82, 83, 84, 85, 86, 88, 89, 91, 93, 94, 97, 98, 99, 100, 101]

## 4. Registro

- `results/referencia_autoritativa.csv` — a tabela de referência CORRETA.
  **Use este arquivo, nunca o CSV original.**
- `results/divisao_v2.json` — SHA-256: `c4f16ff0dbb361610b48f00891b6f5ae0f74ae85faff6825f1a2aa8ab8935b9a`

```
git add results/referencia_autoritativa.csv results/divisao_v2.json results/divisao_v2_sha256.txt fase0d_correcao.py
git commit -m "VAE-001 ACHADO 4: CSV desalinhado; referencia corrigida e divisao refeita"
git tag vae001-divisao-v2
```

O commit anterior (`vae001-divisao`) NÃO é reescrito. O histórico honesto
registra a divisão original, a descoberta do erro, e a correção.

