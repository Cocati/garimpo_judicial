#!/usr/bin/env python3
from pathlib import Path
import argparse
import sys

def _coletar_py(raiz: Path, ignorar_dirs: set):
    for p in raiz.rglob("*.py"):
        # pula se alguma parte do caminho estiver na lista de ignorados
        if any(part in ignorar_dirs for part in p.parts):
            continue
        yield p

def consolidar(raiz: str, saida: str, ignorar_dirs: set):
    raiz_path = Path(raiz).resolve()
    saida_path = Path(saida).resolve()

    arquivos = [p for p in _coletar_py(raiz_path, ignorar_dirs) if p.resolve() != saida_path]
    print(f"🔎 Encontrados {len(arquivos)} arquivos .py sob '{raiz_path}'")

    if not arquivos:
        print("⚠️ Nenhum arquivo .py encontrado (ou tudo foi ignorado).")
        return 1

    with open(saida_path, "w", encoding="utf-8") as w:
        for i, p in enumerate(arquivos, 1):
            print(f"[{i}/{len(arquivos)}] Processando: {p}")
            try:
                conteudo = p.read_text(encoding="utf-8", errors="replace")
            except Exception as e:
                print(f"⚠️ Erro ao ler {p}: {e}", file=sys.stderr)
                continue
            w.write(f"\n# ==== Início do arquivo: {p} ====\n")
            w.write(conteudo)
            w.write(f"\n# ==== Fim do arquivo: {p} ====\n")

    print(f"✅ Saída escrita em: {saida_path}")
    return 0

def main():
    parser = argparse.ArgumentParser(description="Consolida todos os .py em um único arquivo.")
    parser.add_argument("--root", default=".", help="Pasta raiz do projeto (default: .)")
    parser.add_argument("--out", default="projeto_unificado.py", help="Arquivo de saída")
    parser.add_argument(
        "--ignore", nargs="*", default=[
            "__pycache__", ".git", ".idea", ".venv", "venv", "env",
            "build", "dist", "site-packages"  # adicione "Lib" aqui se quiser pular essa pasta
        ],
        help="Nomes de pastas a ignorar (separadas por espaço)."
    )
    args = parser.parse_args()
    # transforma em set para busca mais rápida
    ignorar = set(args.ignore)
    sys.exit(consolidar(args.root, args.out, ignorar))

if __name__ == "__main__":
    main()

