/**
 * vae001_v2_1.js — PROTOCOLO VAE-001, EMENDA v2.1
 * Gera: PROTOCOLO_VAE-001_v2.1_EMENDA.docx
 *
 *   node vae001_v2_1.js
 */
const E = require("./estilo_hxbs");
const { TextRun, AlignmentType } = E;

const b = E.b, i = E.i, t = E.t, cod = E.codigo;

// ---------------------------------------------------------------- CORPO --
const corpo = [];

// ======================================================================= 0
corpo.push(E.h1("0. Natureza desta emenda"));

corpo.push(E.p([
  t("Esta emenda altera o Protocolo VAE-001 v2.0, assinado em 12/07/2026 "),
  t("(SHA-256 E358FAF8D9EA9333CA400C35BF4B074F9717F0EA3846F00C37C4CB8EF659AD32). "),
  b("O conjunto lacrado (n = 76) permanece INTACTO. "),
  t("Nenhum desfecho do conjunto lacrado foi computado ou visualizado."),
]));

corpo.push(E.p([
  t("Todas as alterações aqui registradas derivam EXCLUSIVAMENTE do conjunto de "),
  t("desenvolvimento (n = 25) e de fantomas sintéticos, conforme autorizado pela "),
  b("Regra de alteração da Seção 3.2 do v2.0"),
  t(": “O ponto de operação pode ser alterado com base no CONJUNTO DE DESENVOLVIMENTO "),
  t("e apenas nele. Qualquer alteração deve ser registrada com data e justificativa, "),
  t("e o novo valor congelado ANTES de qualquer acesso ao conjunto lacrado.”"),
]));

corpo.push(E.desvio([
  new TextRun({ text:
    "Esta emenda é o registro exigido por aquela regra. O LithosRad foi congelado " +
    "em 13/07/2026, commit e71787de4aae17389ded23a284d2d3df518a58e0, tag " +
    "vae001-congelado, ANTES de qualquer acesso ao conjunto lacrado.", size: 20 }),
], "Conformidade com a Regra de Alteração"));

corpo.push(E.p([t("")]));

corpo.push(...E.tabela({
  titulo: "Quadro 0. Sumário das alterações.",
  cabecalho: ["#", "Seção do v2.0", "Natureza", "Gravidade"],
  linhas: [
    ["E-1", "3.2 — Congelamento", "CORREÇÃO DE FATO. “Preenchimento de cavidades: Ativo” é falso.", "Alta"],
    ["E-2", "3.2 — Congelamento", "Preenchimento dos campos (versão, commit, data).", "—"],
    ["E-3", "8.2 — Desfechos secundários", "ALTERAÇÃO DO DISPOSITIVO. Estimador de diâmetro substituído.", "Alta"],
    ["E-4", "4 — Conjunto de dados", "ACHADO 4 (novo): CSV desalinhado com o .mat em 53/101.", "Média"],
    ["E-5", "10 — Critérios de aceitação", "REFUTAÇÃO. A “Nota sobre o viés de composição” está errada.", "Alta"],
    ["E-6", "8.2 — Desfechos secundários", "SHI/VCSD: redundância com a atenuação de pico (r² = 0,97).", "Média"],
    ["E-7", "8 — Desfechos", "Estratificação por MORFOLOGIA (t_eq) passa a ser obrigatória.", "Alta"],
    ["E-8", "13 — Registro de desvios", "Preenchimento.", "—"],
  ],
  larguras: [7, 24, 55, 14],
}));

// ======================================================================= 1
corpo.push(E.h1("E-1. Correção de fato — o LithosRad NÃO preenche cavidades"));

corpo.push(E.p([
  t("A Seção 3.2 do v2.0 registra, no quadro de congelamento: "),
  b("“Preenchimento de cavidades — Ativo (binary fill holes, 3D)”"),
  t(". "),
  b("Esta afirmação é falsa. "),
  t("O LithosRad não executa preenchimento de cavidades em nenhum ponto do "),
  t("pipeline de segmentação."),
]));

corpo.push(E.p([
  t("O erro foi descoberto na Fase 1, quando uma reimplementação independente do "),
  t("motor de volume — escrita a partir da especificação do protocolo — divergiu do "),
  t("LithosRad em 2 dos 25 cálculos de desenvolvimento (ids 92 e 95). São exatamente "),
  t("os dois únicos cálculos do conjunto de desenvolvimento que possuem cavidades "),
  t("internas abaixo de 200 UH. Com o "), cod("fill_holes"), t(" desativado, a "),
  t("reimplementação passou a reproduzir o LithosRad com erro máximo de 0,000000 mm³ "),
  t("nos 25."),
]));

corpo.push(E.p([
  b("Correção: "),
  t("a linha do quadro de congelamento passa a ler "),
  b("“Preenchimento de cavidades — NÃO EXECUTADO”"),
  t("."),
]));

corpo.push(E.p([
  b("Impacto declarado sobre os desfechos: "),
  t("nenhum. O protocolo descrevia incorretamente o dispositivo; o dispositivo "),
  t("não mudou. A especificação foi corrigida para descrever o software que "),
  t("efetivamente será executado. Não houve alteração de código motivada por este achado."),
]));

corpo.push(E.ressalva([
  new TextRun({ text:
    "Consequência conceitual, registrada para o relatório: um índice de " +
    "heterogeneidade computado sobre uma máscara que EXCLUI as cavidades internas " +
    "(por estarem abaixo do limiar) descarta precisamente a heterogeneidade " +
    "estrutural real. Este ponto é retomado em E-6.", size: 20 }),
], "Observação"));

// ======================================================================= 2
corpo.push(E.h1("E-2. Congelamento — preenchimento dos campos"));

corpo.push(...E.tabela({
  cabecalho: ["Item", "Registro"],
  linhas: [
    ["Versão do LithosRad", "Commit e71787de4aae17389ded23a284d2d3df518a58e0, tag vae001-congelado"],
    ["Limiar de segmentação (DETECÇÃO)", "200 UH — INALTERADO"],
    ["Conectividade", "26-conectividade, 3D — INALTERADA"],
    ["Preenchimento de cavidades", "NÃO EXECUTADO (corrigido — ver E-1)"],
    ["Componente mínimo", "≥ 3 voxels conexos — INALTERADO"],
    ["Volume", "N × voxvol_mL, por cálculo — INALTERADO"],
    ["Estimador de diâmetro", "Marching cubes, isosuperfície a 0,225 × p95 (ALTERADO — ver E-3)"],
    ["Data/hora do congelamento", "13 / 07 / 2026"],
    ["Responsável", "Artur Montemezzo"],
    ["SHA-256 desta emenda", "ver protocol/protocol_v2_1_sha256.txt"],
  ],
  larguras: [32, 68],
}));

// ======================================================================= 3
corpo.push(E.h1("E-3. Alteração do dispositivo — estimador de diâmetro"));

corpo.push(E.h2("E-3.1. O defeito do estimador anterior"));

corpo.push(E.p([
  t("O estimador de diâmetro anterior computava o casco convexo sobre os "),
  b("oito cantos"),
  t(" de cada voxel do componente (± metade do espaçamento em cada eixo). Sua "),
  t("docstring registra a motivação: “para que um cálculo de ~1 voxel tenha diâmetro "),
  t("não-nulo”. Trata-se de um remendo de borda, jamais calibrado contra padrão de "),
  t("referência algum — busca no repositório não localizou menção a fantoma, "),
  t("calibração ou comparação com outro software."),
]));

corpo.push(E.p([
  t("Contra a referência de paquímetro (n = 25, conjunto de desenvolvimento), o "),
  t("método apresentava viés de "), b("+0,83 mm"),
  t(". Mais grave: o acréscimo era "), b("ANISOTRÓPICO"),
  t(", variando de 0,94 a 1,24 mm — valores que encerram a diagonal do voxel "),
  t("(1,25 mm)."),
]));

corpo.push(E.desvio([
  new TextRun({ text:
    "O diâmetro reportado dependia da ORIENTAÇÃO do cálculo na grade de voxels. " +
    "Um mesmo cálculo, no mesmo paciente, mediria diferente conforme o " +
    "posicionamento no tomógrafo. Isto é indefensável em um dispositivo médico, " +
    "independentemente de qualquer conjunto de dados, e a correção não é " +
    "opcional.", size: 20 }),
], "Defeito estrutural"));

corpo.push(E.h2("E-3.2. Por que o limiar não pode ser fixo"));

corpo.push(E.p([
  t("A substituição por marching cubes (isosuperfície com resolução sub-voxel) "),
  t("corrige o viés e a anisotropia. Porém, com limiar "), b("FIXO"),
  t(" de 200 UH, o corte relativo varia com a densidade do cálculo: em um cálculo de "),
  t("ácido úrico (pico ≈ 650 UH), 200 UH corresponde a 31% do pico — próximo da "),
  t("meia-altura; em uma brushita (pico ≈ 2100 UH), a 9,5% do pico — na cauda da "),
  t("função de espalhamento de ponto, onde a borda é empurrada para fora."),
]));

corpo.push(E.p([
  t("O resultado é um viés dependente de composição: ρ(pico, erro) = "), b("+0,84"),
  t(", com amplitude de "), b("1,8 mm"),
  t(" entre ácido úrico e brushita. As diretrizes decidem conduta em 10, 15 e 20 mm."),
]));

corpo.push(E.p([
  t("Um corte a "), b("fração constante do pico"),
  t(" remove essa dependência "), i("por construção"),
  t(". A forma do estimador é justificada fisicamente; apenas o valor da fração é "),
  t("empírico."),
]));

corpo.push(E.h2("E-3.3. Desempenho — conjunto de desenvolvimento (n = 25)"));

corpo.push(...E.tabela({
  titulo: "Quadro E-3. Diâmetro contra referência de paquímetro.",
  cabecalho: ["Estimador", "Viés (mm)", "DP (mm)", "Pior (mm)", "LoA 95% (mm)", "ρ(pico)", "Reclass."],
  linhas: [
    ["Cantos de voxel (v2.0)", "+0,83", "0,45", "1,62", "—", "+0,82", "1/25"],
    ["Marching cubes @ 200 UH fixo", "+0,04", "0,46", "1,05", "± 0,90", "+0,84", "1/25"],
    ["Marching cubes @ 0,225 × p95", "+0,04", "0,35", "0,76", "± 0,68", "+0,04", "1/25"],
  ],
  larguras: [30, 12, 10, 11, 15, 11, 11],
  legenda: "ρ(pico) = correlação de Spearman entre a atenuação de pico do cálculo e o erro " +
           "do diâmetro. Reclass. = cálculos que mudam de faixa de conduta (10/15/20 mm). " +
           "LoA = limites de concordância de Bland-Altman.",
}));

corpo.push(E.p([
  b("O estimador adotado é o marching cubes com isosuperfície em T = 0,225 × p95"),
  t(", onde p95 é o percentil 95 das unidades Hounsfield dos voxels do componente. "),
  t("Viés idêntico ao limiar fixo; desvio-padrão 24% menor; pior caso 28% menor; e a "),
  t("dependência de composição — de 1,8 mm — é eliminada (ρ de +0,84 para +0,04)."),
]));

corpo.push(E.h2("E-3.4. Robustez do parâmetro — a fração não é sobreajustada"));

corpo.push(E.p([
  t("O desempenho é estável para frações entre "), b("0,200 e 0,275"),
  t(" — quatro valores consecutivos testados, todos com |viés| < 0,20 mm, DP ≈ 0,35 mm, "),
  t("ρ(pico) ≈ 0 e reclassificação 1/25. O valor 0,225 situa-se no centro do platô."),
]));

corpo.push(E.p([
  t("Testou-se ainda a sensibilidade ao "), b("estimador de pico"),
  t(". O platô desloca-se exatamente pela razão entre os estimadores, de modo que os "),
  t("limiares "), b("ABSOLUTOS"), t(" resultantes coincidem:"),
]));

corpo.push(...E.tabela({
  cabecalho: ["Estimador de pico", "Razão vs. máximo", "Fração ótima", "Limiar absoluto (UH)"],
  linhas: [
    ["máximo", "1,000×", "0,200", "128 – 429"],
    ["percentil 99", "0,967×", "0,225", "138 – 464"],
    ["percentil 95 (adotado)", "0,932×", "0,225", "131 – 451"],
  ],
  larguras: [30, 20, 20, 30],
  legenda: "0,200 × (1 / 0,932) = 0,215 ≈ 0,225. Os estimadores convergem para o mesmo " +
           "corte físico. Esta é a assinatura de um método que estima uma grandeza real, " +
           "e não de um parâmetro ajustado a ruído.",
}));

corpo.push(E.p([
  t("Adota-se o percentil 95, e não o máximo, porque o máximo é enviesado para cima "),
  t("pelo ruído: um único voxel espúrio deslocaria o limiar do cálculo inteiro."),
]));

corpo.push(E.h2("E-3.5. A alteração é PURAMENTE DE MEDIÇÃO"));

corpo.push(E.p([
  t("Para um componente de um único voxel, o diâmetro resultante é:"),
]));

corpo.push(E.p([cod("    d = 2 × (1 − f) × espaçamento = 2 × 0,775 × 0,7363 = 1,14 mm")],
  { alignment: AlignmentType.LEFT }));

corpo.push(E.p([
  b("O pico cancela. "),
  t("O diâmetro de um objeto sub-voxel deixa de depender de sua densidade, e "),
  t("permanece acima do filtro "), cod("diametro_min_reportar_mm = 1,0"),
  t(" em qualquer densidade."),
]));

corpo.push(E.desvio([
  new TextRun({ text:
    "Esta propriedade é a razão pela qual o limiar fracionário não é apenas melhor, " +
    "mas NECESSÁRIO. Com marching cubes a limiar FIXO, um componente de um voxel " +
    "mediria 0,74 mm a 400 UH e 1,29 mm a 1600 UH. O filtro de 1,0 mm passaria a " +
    "operar como um corte de DETECÇÃO dependente de densidade (~623 UH). O limiar " +
    "fracionário restitui a inércia do filtro, e a alteração fica confinada à " +
    "MEDIÇÃO.", size: 20 }),
], "Por que o limiar fracionário é obrigatório"));

corpo.push(E.p([
  b("Não alterados: "),
  t("o limiar de DETECÇÃO (200 UH), o cálculo de volume, o SHI, a conectividade e os "),
  t("filtros de reporte e de densidade. O comportamento de detecção do LithosRad é "),
  t("bit-a-bit idêntico ao do v2.0."),
]));

corpo.push(E.h2("E-3.6. Limitação declarada — o viés depende da MORFOLOGIA"));

corpo.push(E.p([
  t("O viés do diâmetro não é constante. Ele resulta do cancelamento parcial de dois "),
  t("efeitos de sinais opostos:"),
]));

corpo.push(E.bullet([
  b("Bloom"),
  t(" — o corte a 22,5% do pico posiciona a isosuperfície ≈ 0,28 mm além da borda "),
  t("verdadeira. Contribuição: "), b("+0,55 mm"), t(" no diâmetro."),
]));
corpo.push(E.bullet([
  b("Truncamento de ponta"),
  t(" — pontas afiadas são sub-voxel e a função de espalhamento de ponto as destrói. "),
  t("Contribuição: "), b("≈ −0,50 mm"), t("."),
]));

corpo.push(...E.tabela({
  titulo: "Quadro E-4. Viés do diâmetro por morfologia (n = 25).",
  cabecalho: ["Morfologia", "n", "Viés (mm)", "Faixa (mm)"],
  linhas: [
    ["Espiculado — t_eq < 2 mm", "13", "−0,10", "[−0,73, +0,52]"],
    ["Intermediário — 2 ≤ t_eq < 4 mm", "5", "+0,04", "—"],
    ["Compacto — t_eq ≥ 4 mm", "7", "+0,36", "[+0,16, +0,76]"],
    ["Esfera lisa (fantoma sintético com PSF)", "—", "+0,73", "TETO do viés"],
    ["GLOBAL", "25", "+0,04", "DP 0,35"],
  ],
  larguras: [42, 8, 18, 32],
  legenda: "t_eq = espessura equivalente = V_ref / (π × (d_ref/2)²). ρ(t_eq, erro) = +0,59 " +
           "(p = 0,0018). O fantoma sintético emprega esfera supersampleada, gaussiana de " +
           "0,7 mm FWHM e média de caixa até a grade de voxels.",
}));

corpo.push(E.desvio([
  new TextRun({ text:
    "O viés global de +0,04 mm é uma propriedade da MISTURA DE FORMAS do conjunto " +
    "de desenvolvimento (13 espiculados, 7 compactos), e NÃO uma propriedade do " +
    "método. O viés no conjunto lacrado dependerá de sua composição morfológica. " +
    "Por esta razão, o resultado do diâmetro DEVE ser reportado ESTRATIFICADO POR " +
    "MORFOLOGIA (ver E-7). Um viés global único seria enganoso.", size: 20 }),
], "Limitação declarada — implicação para o reporte"));

corpo.push(E.p([
  b("Impacto declarado sobre os desfechos: "),
  t("o desfecho PRIMÁRIO (volume) não é afetado — o motor de volume não foi tocado. "),
  t("O desfecho SECUNDÁRIO de concordância do diâmetro (§8.2) passa a avaliar o "),
  t("estimador novo, com os valores do Quadro E-3 como referência de desempenho "),
  t("esperado."),
]));

// ======================================================================= 4
corpo.push(E.h1("E-4. ACHADO 4 — o CSV está desalinhado com o arquivo .mat"));

corpo.push(E.p([
  t("O v2.0 registra três achados da Fase 0 (Seções 4.2 a 4.4). Um quarto foi "),
  t("identificado posteriormente, ainda sobre a ESTRUTURA do conjunto de dados e sem "),
  t("acesso a desfechos do conjunto lacrado."),
]));

corpo.push(E.p([
  t("Os campos "), cod("gt_diam"), t(" e "), cod("gt_vol"),
  t(" do arquivo "), cod("ct-uroliths_matlab.mat"),
  t(" e as colunas correspondentes de "), cod("ct-uroliths_table.csv"),
  t(" "), b("divergem em 53 dos 101 cálculos"),
  t(". As duas fontes não estão na mesma ordem."),
]));

corpo.push(E.p([
  b("Resolução: o arquivo .mat é a fonte AUTORITATIVA "),
  t("de "), cod("gt_diam"), t(" e "), cod("gt_vol"),
  t(". A composição (StoneType), presente apenas no CSV, é recuperada por junção "),
  t("sobre os pares (gt_diam, gt_vol); 100 dos 101 cálculos casaram unicamente. A "),
  t("tabela de referência reconciliada é commitada em "),
  cod("results/referencia_autoritativa.csv"), t("."),
]));

corpo.push(E.p([
  b("Impacto declarado: "),
  t("nenhum sobre os desfechos, desde que o .mat seja usado. O uso do CSV como fonte "),
  t("de referência teria produzido erro grosseiro em metade da amostra. O achado "),
  t("reforça o registro do v2.0 (§4.4) de que a tabela de referência não foi objeto "),
  t("de revisão rigorosa."),
]));

// ======================================================================= 5
corpo.push(E.h1("E-5. REFUTAÇÃO — o viés de volume é governado pela FORMA, não pela densidade"));

corpo.push(E.p([
  t("A Seção 10 do v2.0, em sua “Nota sobre o viés de composição”, afirma: “Um limiar "),
  t("fixo produz viés dependente da densidade do cálculo... A superestimação é, "),
  t("portanto, maior nos cálculos mais densos. Este efeito... será caracterizado pela "),
  b("estratificação por composição"), t(".”"),
]));

corpo.push(E.desvio([
  new TextRun({ text:
    "Esta hipótese foi REFUTADA no conjunto de desenvolvimento. O determinante " +
    "dominante do erro volumétrico é a razão SUPERFÍCIE/VOLUME do cálculo — isto é, " +
    "sua MORFOLOGIA — e não sua densidade. A correlação observada com a densidade é " +
    "um CONFUNDIMENTO.", size: 20 }),
], "Refutação"));

corpo.push(E.h2("E-5.1. A evidência"));

corpo.push(...E.tabela({
  titulo: "Quadro E-5. Preditores do erro volumétrico (n = 25, Spearman).",
  cabecalho: ["Preditor", "ρ", "p"],
  linhas: [
    ["Espessura equivalente — t_eq = V / (π(d/2)²)", "−0,757", "< 0,0001"],
    ["Compacidade — V / V_esfera(d)", "−0,744", "< 0,0001"],
    ["Densidade (atenuação de pico)", "+0,441", "0,027"],
  ],
  larguras: [58, 20, 22],
}));

corpo.push(E.p([
  b("O controle decisivo: "),
  t("isolando-se apenas os cálculos densos (pico > 1600 UH, n = 8), nos quais a "),
  t("densidade é aproximadamente constante, a correlação entre compacidade e erro é "),
  b("ρ = −0,952 (p = 0,0003)"),
  t(". Cálculos densos e compactos erram +3,5% e +22,6%; cálculos densos e finos erram "),
  t("de +236% a +308%. "),
  b("A densidade não explica o erro dentro de um estrato de densidade constante; a "),
  b("forma explica."),
]));

corpo.push(E.h2("E-5.2. A física"));

corpo.push(E.p([
  t("O erro da segmentação por limiar é um efeito de "), b("casca"),
  t(": o deslocamento da borda (Δr) aplica-se à superfície do objeto. Portanto:"),
]));

corpo.push(E.p([cod("    erro relativo ≈ Δr × (S/V)")], { alignment: AlignmentType.LEFT }));

corpo.push(E.p([
  t("Neste conjunto, S/V varia por um fator de ≈ 20×, enquanto Δr — que a densidade "),
  t("modula — varia por ≈ 3×. "),
  b("A forma domina por uma ordem de grandeza. "),
  t("Cálculos de 0,4 a 0,9 mm de espessura equivalente são sub-voxel: cada voxel que "),
  t("ocupam é voxel de volume parcial. Eles não possuem interior."),
]));

corpo.push(E.h2("E-5.3. Nenhum limiar corrige o efeito"));

corpo.push(E.p([
  t("Nove regras de segmentação foram testadas nos mesmos 25 cálculos: limiares fixos "),
  t("(130, 200, 200 + fill_holes, 272, 400 UH), meia-altura em três variantes de "),
  t("estimador, e fracionário sobre a casca. "),
  b("Todas apresentam ρ(compacidade, erro) entre −0,58 e −0,79. "),
  t("A meia-altura reduz o viés de +76% para +4% — e não altera a dependência de forma."),
]));

corpo.push(E.p([
  t("A razão é estrutural: alterar o limiar altera Δr. "),
  b("A razão S/V é propriedade do cálculo. "),
  t("Encolhe-se o erro uniformemente; a correlação com a forma permanece intacta."),
]));

corpo.push(E.h2("E-5.4. Alterações ao protocolo"));

corpo.push(E.bullet([
  b("A “Nota sobre o viés de composição” da Seção 10 é RETIRADA "),
  t("e substituída pelo conteúdo desta seção."),
]));
corpo.push(E.bullet([
  b("A estratificação por COMPOSIÇÃO deixa de ser o eixo primário de caracterização "),
  b("do viés"),
  t(", passando a exploratória. O eixo primário é a "), b("MORFOLOGIA (t_eq)"),
  t(" — ver E-7."),
]));
corpo.push(E.bullet([
  b("O ponto de operação do volume permanece INALTERADO "),
  t("(200 UH, contagem de voxels). Justificativa em E-5.5."),
]));

corpo.push(E.h2("E-5.5. Por que o motor de volume NÃO foi alterado"));

corpo.push(E.p([
  t("Quatro razões, registradas para auditoria:"),
]));

corpo.push(E.bullet([
  b("O padrão de referência é suspeito na faixa crítica. "),
  t("Os quatro piores cálculos do estrato ≥ 10 mm possuem gt_vol entre 0,09 e "),
  t("0,20 mL — exatamente a faixa em que o artigo original relata artefato de troca "),
  t("de proveta (~0,1 mL). O conjunto contém 13 cálculos com volume exatamente "),
  t("0,10 mL e 8 com exatamente 0,20 mL, assinatura de leitura grosseira. "),
  b("Não é possível separar erro do LithosRad de erro da referência. "),
  t("Calibrar contra uma referência enviesada assaria o viés dela no produto."),
]));
corpo.push(E.bullet([
  b("n = 25 é insuficiente "),
  t("para escolher entre variantes de meia-altura cujas diferenças são de poucos "),
  t("pontos percentuais. Seria sobreajuste."),
]));
corpo.push(E.bullet([
  b("Um limiar adaptativo quebraria a detecção validada. "),
  t("Os limiares resultantes (292 a 1073 UH) reintroduziriam, em TC clínica, o "),
  t("problema que os 200 UH resolveram."),
]));
corpo.push(E.bullet([
  b("Nenhum método corrige a dependência de forma. "),
  t("É física (Δr × S/V), não implementação."),
]));

corpo.push(E.ressalva([
  new TextRun({ text:
    "Consequência esperada: o CA-1 (semi-amplitude dos limites de concordância ≤ 25 " +
    "pontos percentuais) provavelmente NÃO será atingido no conjunto lacrado. No " +
    "conjunto de desenvolvimento, o estrato de 10–20 mm apresenta LoA de [−131, " +
    "+305]%. Este é um RESULTADO VÁLIDO do estudo, e não uma falha de execução. A " +
    "caracterização do viés por S/V é registrada como achado primário de " +
    "caracterização, e a limitação será declarada nas Instruções de Uso conforme o " +
    "CA-4 do v2.0.", size: 20 }),
], "Expectativa registrada ANTES da abertura do lacre"));

// ======================================================================= 6
corpo.push(E.h1("E-6. SHI e VCSD — redundância com a atenuação de pico"));

corpo.push(E.p([
  t("O LithosRad reporta o SHI (desvio-padrão populacional das unidades Hounsfield "),
  t("dos voxels ≥ 200 UH do componente) e o VCSD (SHI / HU_média × 100). No conjunto "),
  t("de desenvolvimento, o SHI é predito pela atenuação de pico com:"),
]));

corpo.push(E.p([cod("    SHI ≈ 0,283 × (pico − 200 UH)        r² = 0,968        p = 10⁻¹⁸")],
  { alignment: AlignmentType.LEFT }));

corpo.push(E.p([
  t("E o coeficiente 0,283 aproxima "), cod("1/√12 = 0,2887"),
  t(" — o desvio-padrão de uma distribuição "), b("UNIFORME"),
  t(". Isto indica que a distribuição de unidades Hounsfield no interior da máscara é, "),
  t("essencialmente, "), b("a rampa de volume parcial da borda"),
  t(", e não heterogeneidade estrutural."),
]));

corpo.push(E.h2("E-6.1. Comparabilidade com a literatura"));

corpo.push(E.p([
  t("Simulou-se o método da literatura (ROI elíptica manual em corte axial único, "),
  t("Lee 2016; Yamashita 2017). O resultado é "), b("equivalente"),
  t(" ao da segmentação volumétrica completa: razão de "), b("0,93×"),
  t(" para o SHI e 0,82× para o VCSD."),
]));

corpo.push(E.p([
  t("A explicação é geométrica: o radiologista inscreve a elipse no contorno "),
  b("visível"), t(" do cálculo — que já é a borda inflada pelo volume parcial. "),
  b("A ROI da literatura mede a mesma rampa."),
]));

corpo.push(E.h2("E-6.2. Decisão e declaração"));

corpo.push(E.bullet([
  b("O código do SHI e do VCSD permanece INALTERADO. "),
  t("O método atual é comparável ao da literatura (0,93×), preservando a "),
  t("transferibilidade dos cortes publicados. Um método alternativo (núcleo erodido) "),
  t("produz SHI três vezes menor, e nenhum dos 25 cálculos cruzaria o único corte "),
  t("publicado de VCSD (51,3%; Yamashita 2017) — o que orfanaria a métrica de toda "),
  t("referência existente, sem nada para colocar no lugar."),
]));
corpo.push(E.bullet([
  b("O SHI é definido como desvio-padrão POPULACIONAL (ddof = 0). "),
  t("Registrado para reprodutibilidade."),
]));
corpo.push(E.bullet([
  b("SHI e VCSD são reportados como métricas DESCRITIVAS, "),
  t("jamais como preditores de desfecho terapêutico. A evidência de valor preditivo "),
  t("na literatura é limitada (AUC 0,60 na maior série publicada; métrica ausente das "),
  t("diretrizes da EAU)."),
]));
corpo.push(E.bullet([
  b("Declara-se a redundância "),
  t("com a atenuação de pico (r² = 0,97), já reportada pelo produto como HU_máx."),
]));

corpo.push(E.ressalva([
  new TextRun({ text:
    "Limitações não mensuráveis neste conjunto, registradas para o VAE-002: " +
    "(a) todos os cálculos são de composição PURA — a heterogeneidade verdadeira é " +
    "baixa e homogênea, de modo que o r² = 0,97 é um LIMITE SUPERIOR da redundância; " +
    "(b) o SHI incorpora o ruído de aquisição (σ²_medido = σ²_heterogeneidade + " +
    "σ²_ruído + σ²_volume parcial), não separável com uma única aquisição por " +
    "cálculo e com o fundo mascarado em ~101 UH.", size: 20 }),
], "Limitações declaradas"));

// ======================================================================= 7
corpo.push(E.h1("E-7. Estratificação por MORFOLOGIA — obrigatória"));

corpo.push(E.p([
  t("Em decorrência de E-3.6 e E-5, o reporte dos desfechos de "),
  b("volume"), t(" e de "), b("diâmetro"),
  t(" no conjunto lacrado passa a ser OBRIGATORIAMENTE estratificado por morfologia, "),
  t("além da estratificação por tamanho já prevista no v2.0."),
]));

corpo.push(...E.tabela({
  titulo: "Quadro E-6. Estratos de morfologia.",
  cabecalho: ["Estrato", "Definição", "n no desenvolvimento"],
  linhas: [
    ["Espiculado", "t_eq < 2 mm", "13"],
    ["Intermediário", "2 mm ≤ t_eq < 4 mm", "5"],
    ["Compacto", "t_eq ≥ 4 mm", "7"],
  ],
  larguras: [22, 46, 32],
  legenda: "t_eq = V_ref / (π × (d_ref/2)²), calculada EXCLUSIVAMENTE a partir da " +
           "referência (gt_vol e gt_diam). Jamais a partir de qualquer saída do " +
           "LithosRad — isso seria circular. Os limiares de estrato são pré-especificados " +
           "nesta emenda, antes de qualquer acesso ao conjunto lacrado.",
}));

corpo.push(E.p([
  b("Um viés global único é vedado como forma exclusiva de reporte. "),
  t("Ele reflete a composição morfológica da amostra, e não o desempenho do método. "),
  t("O viés global permanece reportado, acompanhado obrigatoriamente da ressalva "),
  t("acima e dos valores estratificados."),
]));

corpo.push(E.h2("E-7.1. Réplicas pré-especificadas"));

corpo.push(E.p([
  t("Registram-se, ANTES da abertura do lacre, os valores obtidos no conjunto de "),
  t("desenvolvimento, para verificação de réplica em n = 76:"),
]));

corpo.push(...E.tabela({
  cabecalho: ["Achado", "Desenvolvimento (n = 25)", "Replica no lacrado?"],
  linhas: [
    ["ρ(compacidade, erro do volume)", "−0,74  (p < 0,0001)", "a verificar"],
    ["ρ(compacidade, erro) — apenas densos (pico > 1600)", "−0,95  (p = 0,0003; n = 8)", "a verificar"],
    ["ρ(t_eq, erro do diâmetro)", "+0,59  (p = 0,0018)", "a verificar"],
    ["SHI ≈ k × (pico − 200):  k", "0,283   (1/√12 = 0,2887)", "a verificar"],
    ["SHI ≈ k × (pico − 200):  r²", "0,968", "a verificar"],
    ["Falha de segmentação", "0 / 25", "a verificar"],
    ["Fallback do estimador de diâmetro", "0 / 25 esperado", "a verificar"],
  ],
  larguras: [42, 32, 26],
}));

// ======================================================================= 8
corpo.push(E.h1("E-8. Registro de desvios (Seção 13 do v2.0)"));

corpo.push(...E.tabela({
  cabecalho: ["Data", "Desvio", "Justificativa", "Impacto declarado"],
  linhas: [
    ["12/07/2026",
     "Inventário da Fase 0 incluiu, por erro de especificação, a contagem de voxels nulos por cálculo (n_zero).",
     "Já registrado no v2.0, §12.1. Nenhuma derivação de volume foi realizada a partir dessa informação.",
     "Nenhum."],
    ["13/07/2026",
     "Descoberto que o v2.0 §3.2 descreve incorretamente o dispositivo (fill_holes “Ativo”).",
     "Erro de especificação do protocolo, não do software. Corrigido em E-1.",
     "Nenhum. O dispositivo não mudou."],
    ["13/07/2026",
     "Estimador de diâmetro substituído (cantos de voxel → marching cubes @ 0,225 × p95).",
     "Autorizado pela Regra de Alteração (§3.2). Baseado exclusivamente no conjunto de desenvolvimento e em fantomas sintéticos. Corrige defeito estrutural: o diâmetro dependia da orientação do cálculo na grade. Ver E-3.",
     "Desfecho primário (volume): nenhum. Desfecho secundário (diâmetro): passa a avaliar o estimador novo."],
    ["13/07/2026",
     "CSV desalinhado com o .mat em 53/101 cálculos (ACHADO 4).",
     "Achado estrutural. O .mat é autoritativo. Ver E-4.",
     "Nenhum, desde que o .mat seja usado."],
    ["13/07/2026",
     "A “Nota sobre o viés de composição” (§10) foi REFUTADA no conjunto de desenvolvimento.",
     "O erro volumétrico é governado por S/V, não por densidade (ρ = −0,95 isolando os densos). Ver E-5.",
     "A estratificação primária do viés muda de COMPOSIÇÃO para MORFOLOGIA. Ver E-7."],
  ],
  larguras: [10, 26, 38, 26],
}));

// ======================================================================= 9
corpo.push(E.h1("E-9. Regras de integridade — reafirmação"));

corpo.push(E.p([
  t("Todas as regras da Seção 12 do v2.0 permanecem em vigor, sem exceção. Reafirma-se "),
  t("em particular:"),
]));

corpo.push(E.bullet([
  b("EXECUÇÃO ÚNICA sobre o conjunto lacrado. "),
  t("O harness de execução implementa trava mecânica: ao concluir, grava registro "),
  t("assinado (SHA-256 do CSV de resultados) e recusa nova execução."),
]));
corpo.push(E.bullet([
  b("PRÉ-VOO OBRIGATÓRIO. "),
  t("Antes de abrir o lacre, o harness remede os 25 cálculos de desenvolvimento com o "),
  t("código congelado e verifica que reproduz o desempenho declarado no Quadro E-3. "),
  t("Se não reproduzir, "), b("aborta sem tocar no lacre"),
  t(" — pois o código congelado não seria o código caracterizado nesta emenda."),
]));
corpo.push(E.bullet([
  b("PROIBIÇÃO DE AJUSTE PÓS-DESFECHO. "),
  t("Nenhum parâmetro pode ser alterado após a visualização de qualquer desfecho do "),
  t("conjunto lacrado. A ocorrência de tal ajuste DESCARTA o estudo como validação."),
]));
corpo.push(E.bullet([
  b("CONTAGEM DE FALLBACK. "),
  t("O harness conta e reporta os cálculos medidos pelo estimador de contingência "),
  t("(centros de voxel, viés −0,26 mm, contra +0,12 mm do marching cubes). Esperado: "),
  t("zero. Qualquer ocorrência é declarada."),
]));

// ====================================================================== 10
corpo.push(E.h1("Aprovação"));

corpo.push(E.p([
  t("As assinaturas atestam que esta emenda foi integralmente definida ANTES de "),
  t("qualquer acesso a desfechos do conjunto lacrado, e que o conjunto lacrado "),
  t("(n = 76) permanece INTACTO na data de assinatura."),
]));

corpo.push(...E.tabela({
  cabecalho: ["Papel", "Nome", "Assinatura / Data"],
  linhas: [
    ["Responsável técnico", "Artur Montemezzo", ""],
    ["Responsável pela execução", "Artur Montemezzo", ""],
    ["Responsável pela qualidade", "Artur Montemezzo", ""],
  ],
  larguras: [32, 34, 34],
  legenda: "Os três papéis são acumulados pelo mesmo responsável, conforme estrutura " +
           "atual da HXBS Tecnologia Ltda.",
}));

// ---------------------------------------------------------------- MONTA --
const doc = E.documento({
  tipo: "Protocolo — Emenda v2.1",
  titulo: "PROTOCOLO DE VALIDAÇÃO ANALÍTICA EXTERNA",
  subtitulo: "VAE-001 — Emenda v2.1 ao protocolo v2.0 assinado em 12/07/2026",
  meta: [
    ["Identificador", "VAE-001 — Emenda v2.1"],
    ["Emenda a", "VAE-001 v2.0, assinado em 12/07/2026 — SHA-256 E358FAF8D9EA9333CA400C35BF4B074F9717F0EA3846F00C37C4CB8EF659AD32"],
    ["Data de emissão", "13 / 07 / 2026"],
    ["Produto", "LithosRad — SaMD para detecção, medição e quantificação de cálculos renais em TC"],
    ["Versão congelada", "commit e71787de4aae17389ded23a284d2d3df518a58e0 — tag vae001-congelado"],
    ["Enquadramento", "RDC nº 751/2022 — Classe II, CADe, leitura concorrente"],
    ["Base das alterações", "Conjunto de DESENVOLVIMENTO (n = 25) e fantomas sintéticos, exclusivamente"],
    ["Status do lacre", "INTACTO — nenhum desfecho do conjunto lacrado (n = 76) foi computado ou visualizado"],
  ],
  nota: "Autorização. Esta emenda é o registro exigido pela Regra de Alteração da Seção 3.2 " +
        "do protocolo v2.0, que permite alterar o ponto de operação com base no conjunto de " +
        "desenvolvimento — e apenas nele — mediante registro de data e justificativa, e " +
        "congelamento do novo valor ANTES de qualquer acesso ao conjunto lacrado.",
  corpo,
  rodapeNota: "HXBS Tecnologia Ltda. — LithosRad — Protocolo VAE-001 v2.1 (emenda)",
  fecho: "Anexos do v2.0 permanecem válidos. Acrescenta-se o Anexo E — Relatório da Fase 1 " +
         "(análise do conjunto de desenvolvimento, n = 25), do qual derivam todas as " +
         "alterações desta emenda.",
});

E.salvar(doc, "PROTOCOLO_VAE-001_v2.1_EMENDA.docx")
 .then((p) => console.log("Gerado:", p));
