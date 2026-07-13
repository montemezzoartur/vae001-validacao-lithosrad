#!/usr/bin/env python3
"""
VAE-001 — FASE 0: INVENTÁRIO
Dataset: ct-uroliths-freiburg (figshare 21992264, Kellner & Neubauer 2023)
Formato real: 1 CSV + 1 MAT

REGRA DA FASE 0
---------------
Este script inspeciona ESTRUTURA. É PROIBIDO aqui:
  - aplicar limiar, segmentar, ou computar qualquer volume a partir das imagens
  - comparar qualquer saída do LithosRad com a referência

É PERMITIDO (e necessário):
  - listar chaves, formas, tipos, espaçamento
  - descrever estatísticas DA REFERÊNCIA sozinha (é característica basal,
    não desfecho — não revela nenhuma comparação)

Uso:  python fase0_inventario.py data/raw/
Saída: results/fase0_inventario.md
"""
import sys, os, hashlib, json
from pathlib import Path
import numpy as np
import pandas as pd

OUT = []
def w(s=""):
    print(s)
    OUT.append(s)


def sha256(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def describe(name, obj, depth=0):
    """Descreve recursivamente uma estrutura vinda do .mat."""
    pad = "  " * depth
    if isinstance(obj, np.ndarray):
        w(f"{pad}- `{name}`: ndarray  shape={obj.shape}  dtype={obj.dtype}")
        # struct array do MATLAB
        if obj.dtype.names:
            w(f"{pad}    campos: {list(obj.dtype.names)}")
            if obj.size:
                first = obj.flat[0]
                for fld in obj.dtype.names:
                    try:
                        describe(fld, first[fld], depth + 2)
                    except Exception as e:
                        w(f"{pad}      - `{fld}`: <ilegível: {e}>")
        elif obj.dtype == object:
            w(f"{pad}    cell array; {obj.size} elementos")
            if obj.size:
                describe(f"{name}[0]", obj.flat[0], depth + 2)
        elif obj.ndim == 3:
            w(f"{pad}    *** VOLUME 3D *** min={obj.min():.1f} max={obj.max():.1f} "
              f"mean={obj.mean():.1f}")
            w(f"{pad}    (se isto for UH: max ~1000-2000 indica cálculo; "
              f"min ~0 indica água, ~-1000 indica ar)")
        elif obj.size <= 12:
            w(f"{pad}    valores: {obj.ravel().tolist()}")
    elif isinstance(obj, dict):
        w(f"{pad}- `{name}`: dict, chaves = {list(obj.keys())}")
        for k, v in obj.items():
            if not k.startswith("__"):
                describe(k, v, depth + 1)
    else:
        w(f"{pad}- `{name}`: {type(obj).__name__} = {repr(obj)[:120]}")


def main(raw_dir):
    raw = Path(raw_dir)
    files = sorted(p for p in raw.iterdir() if p.is_file() and not p.name.startswith("."))

    w("# VAE-001 — Fase 0: Inventário do dataset")
    w()
    w("Dataset: ct-uroliths-freiburg — DOI 10.6084/m9.figshare.21992264")
    w("Kellner E, Neubauer J. 2023-02-08.")
    w()

    # ---------- 1. arquivos e hashes ----------
    w("## 1. Arquivos e integridade")
    w()
    w("| Arquivo | Tamanho | SHA-256 |")
    w("|---|---|---|")
    for p in files:
        w(f"| `{p.name}` | {p.stat().st_size:,} B | `{sha256(p)}` |")
    w()

    # ---------- 2. CSV de referência ----------
    csvs = [p for p in files if p.suffix.lower() == ".csv"]
    w("## 2. Tabela de referência (CSV)")
    w()
    for p in csvs:
        df = pd.read_csv(p)
        w(f"### `{p.name}`")
        w()
        w(f"- Linhas: **{len(df)}**  (esperado: 101 urólitos)")
        w(f"- Colunas: **{len(df.columns)}**")
        w()
        w("| Coluna | dtype | n não-nulo | min | max |")
        w("|---|---|---|---|---|")
        for c in df.columns:
            s = df[c]
            if pd.api.types.is_numeric_dtype(s):
                w(f"| `{c}` | {s.dtype} | {s.notna().sum()} | {s.min():.4g} | {s.max():.4g} |")
            else:
                w(f"| `{c}` | {s.dtype} | {s.notna().sum()} | — | — |")
        w()
        w("**CHECAGEM CRÍTICA — medições individuais dos 3 avaliadores.**")
        w()
        w("A Seção 5 do protocolo depende delas para computar o piso de incerteza")
        w("da referência. Procure colunas do tipo `rater1/2/3`, `vol_1/2/3`, `obs*`.")
        w()
        cols = [c.lower() for c in df.columns]
        tem_raters = any(any(k in c for k in ("rater", "obs", "_1", "_2", "_3")) for c in cols)
        w(f"- Indício de colunas por avaliador: **{'SIM' if tem_raters else 'NÃO ENCONTRADO'}**")
        if not tem_raters:
            w("- ⚠️  Se não estiverem no `.mat` tampouco, o protocolo precisa de emenda:")
            w("  o piso de incerteza fica indisponível e os critérios de aceitação")
            w("  perdem sua âncora. Nesse caso, contatar os autores.")
        w()

        # baseline da REFERÊNCIA (permitido — não é desfecho)
        num = df.select_dtypes(include=[np.number])
        if len(num.columns):
            w("**Distribuição da referência** (característica basal — não é desfecho):")
            w()
            w("```")
            w(num.describe().to_string())
            w("```")
            w()

        # estratos do protocolo — só contagem
        diam_col = next((c for c in df.columns
                         if any(k in c.lower() for k in ("diam", "dmax", "size", "mm"))), None)
        if diam_col and pd.api.types.is_numeric_dtype(df[diam_col]):
            bins = [0, 5, 10, 20, np.inf]
            labs = ["< 5 mm", "5–10 mm", "10–20 mm", "> 20 mm"]
            cnt = pd.cut(df[diam_col], bins=bins, labels=labs, right=False).value_counts().reindex(labs)
            w(f"**População dos estratos do protocolo** (via `{diam_col}`):")
            w()
            w("| Estrato | n |")
            w("|---|---|")
            for k, v in cnt.items():
                w(f"| {k} | {int(v) if pd.notna(v) else 0} |")
            w()
            w("> O estrato **10–20 mm** é o desfecho primário. Se estiver pouco povoado,")
            w("> o estudo perde poder e isso precisa ser registrado como limitação ANTES de rodar.")
            w()

        origem_col = next((c for c in df.columns
                           if any(k in c.lower() for k in ("orig", "spec", "human", "dog", "canin", "anim"))), None)
        w(f"- Coluna de origem (humano/canino) detectada: "
          f"**{origem_col if origem_col else 'NÃO ENCONTRADA'}**")
        if not origem_col:
            w("  - ⚠️  A estratificação por origem é OBRIGATÓRIA (Seção 8). Se não houver")
            w("    essa coluna, verifique o `.mat` ou contate os autores. Sem ela, o estrato")
            w("    ≥10 mm — majoritariamente canino — não é interpretável.")
        w()

    # ---------- 3. MAT ----------
    mats = [p for p in files if p.suffix.lower() == ".mat"]
    w("## 3. Dados de imagem (MATLAB)")
    w()
    for p in mats:
        w(f"### `{p.name}`")
        w()
        loaded = False
        try:  # v7 e anteriores
            from scipy.io import loadmat
            m = loadmat(p, squeeze_me=False, struct_as_record=True)
            w("- Formato: **MAT v7 ou anterior** (lido com `scipy.io.loadmat`)")
            w()
            for k, v in m.items():
                if not k.startswith("__"):
                    describe(k, v)
            loaded = True
        except NotImplementedError:
            pass
        except Exception as e:
            w(f"- `scipy.io.loadmat` falhou: {e}")

        if not loaded:
            try:  # v7.3 = HDF5
                import h5py
                w("- Formato: **MAT v7.3 (HDF5)** (lido com `h5py`)")
                w()
                with h5py.File(p, "r") as f:
                    def visit(name, obj):
                        if isinstance(obj, h5py.Dataset):
                            w(f"- `{name}`: shape={obj.shape} dtype={obj.dtype}")
                    f.visititems(visit)
                loaded = True
            except Exception as e:
                w(f"- ❌ Falha ao ler como HDF5 também: {e}")
                w("- Instale: `pip install h5py`")
        w()

    # ---------- 4. perguntas em aberto ----------
    w("## 4. Perguntas que precisam virar emenda ao protocolo")
    w()
    w("Responda cada uma com base no que está acima, ANTES de congelar:")
    w()
    w("1. **Espaçamento do voxel está no arquivo?** Se sim, qual? Se não, assumimos")
    w("   0,7 × 0,7 × 0,7 mm do artigo — e isso vira premissa documentada, não dado.")
    w("2. **Os volumes são VOIs recortados ou exames inteiros?** (Ver shape dos arrays 3D.)")
    w("   Se recortados, o critério de exclusão por VAZAMENTO (Seção 11) fica inaplicável")
    w("   e deve ser removido por emenda.")
    w("3. **Um cálculo por volume, ou vários?** Define se há lógica de semente.")
    w("4. **As medições dos 3 avaliadores estão disponíveis?** Se não, a Seção 5 cai")
    w("   e os critérios de aceitação precisam de nova âncora.")
    w("5. **Há coluna de origem (humano/canino)?** Se não, a Seção 8 é inexequível.")
    w("6. **Há coluna de composição?** (41 dos 101 são 'não determinada'.)")
    w("7. **As unidades da referência**: volume em mL ou mm³? Diâmetro em mm?")
    w("8. **Os dados já vêm em UH**, ou há escala a aplicar? (Ver min/max dos volumes 3D.)")
    w()
    w("## 5. Licença — verificar na página do figshare")
    w()
    w("- [ ] CC BY 4.0 → uso comercial OK com atribuição. **Seguir.**")
    w("- [ ] CC BY-NC → uso comercial VEDADO. **O estudo não pode entrar no dossiê.**")
    w("- [ ] Outra: ______________________")
    w()


if __name__ == "__main__":
    raw_dir = sys.argv[1] if len(sys.argv) > 1 else "data/raw"
    main(raw_dir)
    os.makedirs("results", exist_ok=True)
    with open("results/fase0_inventario.md", "w", encoding="utf-8") as f:
        f.write("\n".join(OUT) + "\n")
    print("\n\n>>> Salvo em results/fase0_inventario.md")
