"""
============================================================
PRINTER ASSISTANT — GERADOR DE RELEASE (.EXE + .ZIP)
(tools/build_release.py)
============================================================
Automatiza a publicação de novas versões para a equipe técnica:
  1. Atualiza __version__ em core/version.py
  2. Compila o executável com PyInstaller (PrinterAssistant_Beta.spec)
  3. Compacta dist/PrinterAssistant_Beta -> dist/PrinterAssistant_<versao>.zip
  4. Opcionalmente cria tag Git e faz push (branch + tag)
  5. Abre o Explorer no .zip pronto e a página do GitHub Releases no navegador
"""

from __future__ import annotations

import os
from pathlib import Path
import re
import subprocess
import sys
import webbrowser
import zipfile

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from core.version import GITHUB_REPO, __version__


def atualizar_version_py(nova_versao: str) -> None:
    vpath = BASE_DIR / "core" / "version.py"
    conteudo = vpath.read_text(encoding="utf-8")
    novo = re.sub(
        r'__version__\s*=\s*["\'][^"\']+["\']',
        f'__version__ = "{nova_versao}"',
        conteudo,
        count=1,
    )
    vpath.write_text(novo, encoding="utf-8")


def gerar_zip(pasta_origem: Path, zip_destino: Path) -> None:
    if zip_destino.exists():
        zip_destino.unlink()
    with zipfile.ZipFile(zip_destino, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=6) as zf:
        for arq in pasta_origem.rglob("*"):
            if arq.is_file():
                rel = arq.relative_to(pasta_origem.parent)
                zf.write(arq, arcname=str(rel))


def _escolher_python_pyinstaller() -> str:
    """Retorna o executável Python que possui PyInstaller instalado."""
    candidatos = [sys.executable, "python"]
    for py in candidatos:
        try:
            r = subprocess.run(
                [py, "-m", "PyInstaller", "--version"],
                capture_output=True,
                text=True,
                timeout=10,
            )
            if r.returncode == 0:
                return py
        except Exception:
            continue
    return sys.executable


def main() -> int:
    print("=" * 64)
    print("  PRINTER ASSISTANT — GERADOR DE RELEASE (.EXE + .ZIP)")
    print("=" * 64)
    print(f"Versão atual em core/version.py: {__version__}")
    print()

    entrada = input(f"Informe a nova versão (Enter para manter '{__version__}'): ").strip()
    versao = entrada or __version__
    if not versao.startswith("v"):
        versao = f"v{versao}"

    if versao != __version__:
        atualizar_version_py(versao)
        print(f"[OK] core/version.py atualizado para {versao}")

    # 1. Compilar com PyInstaller
    print("\n[1/3] Compilando executável com PyInstaller...")
    spec_path = BASE_DIR / "PrinterAssistant_Beta.spec"
    py_build = _escolher_python_pyinstaller()
    cmd_build = [
        py_build,
        "-m",
        "PyInstaller",
        str(spec_path),
        "--clean",
        "--noconfirm",
    ]
    res = subprocess.run(cmd_build, cwd=str(BASE_DIR))
    if res.returncode != 0:
        print("\n[ERRO] PyInstaller falhou. Verifique se está instalado no .venv:")
        print("       pip install pyinstaller")
        return 1

    pasta_dist = BASE_DIR / "dist" / "PrinterAssistant_Beta"
    if not (pasta_dist / "PrinterAssistant_Beta.exe").exists():
        print(f"\n[ERRO] Executável não encontrado em {pasta_dist}")
        return 1

    # 2. Compactar ZIP
    zip_nome = f"PrinterAssistant_{versao}.zip"
    zip_path = BASE_DIR / "dist" / zip_nome
    print(f"\n[2/3] Compactando {zip_nome}...")
    gerar_zip(pasta_dist, zip_path)
    tam_mb = zip_path.stat().st_size / (1024 * 1024)
    print(f"[OK] Pacote gerado: {zip_path} ({tam_mb:.1f} MB)")

    # 3. Git tag opcional + abrir GitHub Releases
    print("\n[3/3] Publicação no GitHub Releases")
    criar_tag = input(f"Deseja criar a tag Git '{versao}' e enviar para o GitHub? [s/N]: ").strip().lower()
    if criar_tag in ("s", "sim", "y", "yes"):
        subprocess.run(["git", "add", "core/version.py"], cwd=str(BASE_DIR))
        subprocess.run(["git", "commit", "-m", f"release: {versao}"], cwd=str(BASE_DIR))
        subprocess.run(["git", "tag", "-f", versao], cwd=str(BASE_DIR))
        subprocess.run(["git", "push", "origin", "main"], cwd=str(BASE_DIR))
        subprocess.run(["git", "push", "origin", versao, "--force"], cwd=str(BASE_DIR))

    url_release = (
        f"https://github.com/{GITHUB_REPO}/releases/new"
        f"?tag={versao}&title=Printer+Assistant+{versao}"
    )
    print("\n" + "=" * 64)
    print("PRONTO PARA PUBLICAR!")
    print(f"1. Arquivo ZIP pronto: {zip_path}")
    print(f"2. Página do Release:  {url_release}")
    print("   -> Arraste o arquivo .zip para a página do GitHub e clique em 'Publish release'.")
    print("   -> Todos os computadores com o Printer Assistant detectarão automaticamente!")
    print("=" * 64)

    try:
        if os.name == "nt":
            subprocess.Popen(["explorer.exe", f"/select,{zip_path}"])
        webbrowser.open(url_release)
    except Exception:
        pass

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
