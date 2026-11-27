"""
============================================================
PRINTER ASSISTANT — MOTOR DE ATUALIZAÇÃO (AUTO-UPDATER)
(core/updater.py)
============================================================

Suporta automaticamente os dois modos de distribuição:
  1. Executável compilado (.exe / ZIP PyInstaller):
     - Consulta GitHub Releases (sem necessidade de login/token).
     - Baixa o .zip da nova versão com progresso em tempo real.
     - Preserva config.json e logs/relatorios do usuário.
     - Aplica a atualização via script auxiliar após encerrar o processo
       e reabre o Printer Assistant atualizado automaticamente.

  2. Instalação via Git (git clone):
     - Detecta tanto novas GitHub Releases quanto novos commits em origin/main.
     - Protege config.json local contra conflitos de merge.
     - Executa git pull --ff-only origin main e atualiza requirements.txt
       no Python/.venv atual caso tenha havido alteração.
     - Permite reiniciar o programa com 1 clique.
"""

from __future__ import annotations

from dataclasses import dataclass, field
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import urllib.error
import urllib.request
import zipfile
from typing import Callable, Optional, Tuple

from core.version import GITHUB_BRANCH, GITHUB_REPO, __version__

_CREATE_NO_WINDOW = 0x08000000 if os.name == "nt" else 0
_USER_AGENT = f"PrinterAssistant-Updater/{__version__}"


@dataclass
class UpdateInfo:
    disponivel: bool = False
    modo: str = "git"  # "exe" | "git" | "zip_manual"
    versao_atual: str = __version__
    nova_versao: str = __version__
    commits_pendentes: int = 0
    notas: str = ""
    download_url: str = ""
    asset_nome: str = ""
    asset_tamanho: int = 0
    release_url: str = f"https://github.com/{GITHUB_REPO}/releases"
    erro: Optional[str] = None
    resumo_curto: str = ""
    detalhes: list = field(default_factory=list)


def is_frozen_exe() -> bool:
    return bool(getattr(sys, "frozen", False))


def get_app_dir() -> Path:
    if is_frozen_exe():
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent.parent


def detectar_modo_instalacao() -> str:
    if is_frozen_exe():
        return "exe"
    if (get_app_dir() / ".git").exists():
        return "git"
    return "zip_manual"


def parse_semver(versao: str) -> Tuple[int, int, int, int, str]:
    """
    Converte strings como 'v1.1.0-beta', '1.2.0', 'v1.0.2-beta.1' em tupla ordenável.
    Versões estáveis (sem sufixo) vencem pré-releases com mesmo major.minor.patch.
    """
    limpo = (versao or "").strip().lstrip("vV")
    m = re.match(r"^(\d+)(?:\.(\d+))?(?:\.(\d+))?(?:[-_.]?(.*))?$", limpo)
    if not m:
        return (0, 0, 0, 0, limpo.lower())
    major = int(m.group(1) or 0)
    minor = int(m.group(2) or 0)
    patch = int(m.group(3) or 0)
    sufixo = (m.group(4) or "").strip().lower()
    eh_estavel = 1 if not sufixo else 0
    return (major, minor, patch, eh_estavel, sufixo)


def versao_mais_nova(remota: str, local: str) -> bool:
    if not remota:
        return False
    return parse_semver(remota) > parse_semver(local)


def _http_get_json(url: str, timeout: float = 5.0) -> Optional[dict]:
    req = urllib.request.Request(
        url,
        headers={
            "Accept": "application/vnd.github+json",
            "User-Agent": _USER_AGENT,
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            if resp.status != 200:
                return None
            return json.loads(resp.read().decode("utf-8", errors="ignore"))
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return None
        raise
    except Exception:
        raise


def _consultar_ultima_release_github(timeout: float = 5.0) -> Optional[dict]:
    """
    Consulta primeiro /releases/latest; se o repositório só tiver pré-releases
    (ex: tags '-beta'), /releases/latest retorna 404 — fazemos fallback para
    /releases?per_page=5 pegando a primeira não-draft.
    """
    base = f"https://api.github.com/repos/{GITHUB_REPO}"
    try:
        latest = _http_get_json(f"{base}/releases/latest", timeout=timeout)
        if isinstance(latest, dict) and latest.get("tag_name"):
            return latest
    except Exception:
        pass

    try:
        lista = _http_get_json(f"{base}/releases?per_page=5", timeout=timeout)
        if isinstance(lista, list):
            for rel in lista:
                if isinstance(rel, dict) and not rel.get("draft") and rel.get("tag_name"):
                    return rel
    except Exception:
        pass

    return None


def _extrair_asset_zip(release: dict) -> Tuple[str, str, int]:
    assets = release.get("assets") or []
    for asset in assets:
        nome = str(asset.get("name") or "")
        if nome.lower().endswith(".zip"):
            return (
                str(asset.get("browser_download_url") or ""),
                nome,
                int(asset.get("size") or 0),
            )
    return ("", "", 0)


def _run_git(args: list[str], cwd: Path, timeout: float = 15.0) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["git", *args],
        cwd=str(cwd),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="ignore",
        timeout=timeout,
        creationflags=_CREATE_NO_WINDOW,
    )


def verificar_atualizacao(timeout: float = 5.0) -> UpdateInfo:
    """
    Verifica atualizações sem lançar exceções para a interface.
    Funciona tanto no modo .exe (GitHub Releases) quanto no modo Git (commits + Releases).
    """
    modo = detectar_modo_instalacao()
    info = UpdateInfo(
        disponivel=False,
        modo=modo,
        versao_atual=__version__,
        nova_versao=__version__,
    )

    # 1. Consulta GitHub Releases (útil em todos os modos)
    release = None
    erro_rede = None
    try:
        release = _consultar_ultima_release_github(timeout=timeout)
    except Exception as exc:
        erro_rede = str(exc)

    if release:
        tag = str(release.get("tag_name") or "").strip()
        notas = str(release.get("body") or "").strip()
        url_rel = str(release.get("html_url") or info.release_url)
        dl_url, asset_nome, asset_tam = _extrair_asset_zip(release)

        info.release_url = url_rel
        if versao_mais_nova(tag, __version__):
            info.disponivel = True
            info.nova_versao = tag
            info.notas = notas or f"Nova versão {tag} publicada no GitHub Releases."
            info.download_url = dl_url
            info.asset_nome = asset_nome
            info.asset_tamanho = asset_tam
            info.resumo_curto = f"Nova versão {tag}"

    # 2. Se instalado via Git, também verifica commits pendentes em origin/<branch>
    if modo == "git":
        app_dir = get_app_dir()
        try:
            proc_fetch = _run_git(["fetch", "--quiet", "origin", GITHUB_BRANCH], cwd=app_dir, timeout=10.0)
            if proc_fetch.returncode == 0:
                proc_cnt = _run_git(
                    ["rev-list", "--count", f"HEAD..origin/{GITHUB_BRANCH}"],
                    cwd=app_dir,
                    timeout=5.0,
                )
                if proc_cnt.returncode == 0:
                    qtd = int((proc_cnt.stdout or "0").strip() or "0")
                    info.commits_pendentes = qtd
                    if qtd > 0:
                        info.disponivel = True
                        proc_log = _run_git(
                            ["log", f"HEAD..origin/{GITHUB_BRANCH}", "--pretty=format:- %s (%h)", "-n", "10"],
                            cwd=app_dir,
                            timeout=5.0,
                        )
                        linhas_log = [ln.strip() for ln in (proc_log.stdout or "").splitlines() if ln.strip()]
                        info.detalhes = linhas_log
                        if not info.resumo_curto:
                            suf = "atualização" if qtd == 1 else "atualizações"
                            info.resumo_curto = f"{qtd} {suf} via Git"
                        if not info.notas:
                            info.notas = "Alterações disponíveis no repositório:\n\n" + "\n".join(linhas_log)
                        else:
                            info.notas += "\n\nCommits pendentes:\n" + "\n".join(linhas_log)
                        if info.nova_versao == __version__:
                            # Tenta ler a versão remota direto de origin/main:core/version.py
                            proc_ver = _run_git(
                                ["show", f"origin/{GITHUB_BRANCH}:core/version.py"],
                                cwd=app_dir,
                                timeout=5.0,
                            )
                            m_ver = re.search(r'__version__\s*=\s*["\']([^"\']+)["\']', proc_ver.stdout or "")
                            if m_ver:
                                info.nova_versao = m_ver.group(1).strip()
                            else:
                                info.nova_versao = f"{__version__} (+{qtd})"
            elif not info.disponivel and erro_rede:
                info.erro = f"Sem conexão com o GitHub ({erro_rede})"
        except FileNotFoundError:
            info.modo = "zip_manual"
        except Exception as exc:
            if not info.disponivel:
                info.erro = str(exc)
    elif not info.disponivel and erro_rede:
        info.erro = f"Sem conexão com o GitHub ({erro_rede})"

    return info


def aplicar_atualizacao_git(
    on_progress: Optional[Callable[[int, str], None]] = None,
) -> Tuple[bool, str]:
    """
    Atualiza instalação Git preservando config.json local e instalando
    novas dependências caso requirements.txt tenha mudado.
    """
    app_dir = get_app_dir()
    cfg_path = app_dir / "config.json"
    cfg_backup: Optional[bytes] = None

    def _prog(pct: int, msg: str):
        if on_progress:
            on_progress(pct, msg)

    try:
        _prog(10, "Protegendo configurações locais (config.json)...")
        if cfg_path.exists():
            cfg_backup = cfg_path.read_bytes()

        # Hash anterior do requirements.txt
        req_path = app_dir / "requirements.txt"
        req_antes = req_path.read_bytes() if req_path.exists() else b""

        # Se config.json estiver modificado localmente, limpa só ele antes do pull
        proc_st = _run_git(["status", "--porcelain"], cwd=app_dir, timeout=5.0)
        linhas_sujas = [ln for ln in (proc_st.stdout or "").splitlines() if ln.strip()]
        outros_modificados = [
            ln for ln in linhas_sujas
            if not ln.strip().endswith("config.json") and not ln.startswith("??")
        ]
        if outros_modificados:
            return (
                False,
                "Existem alterações locais em arquivos de código que impedem a atualização automática:\n"
                + "\n".join(outros_modificados[:5]),
            )

        if any(ln.strip().endswith("config.json") for ln in linhas_sujas):
            _run_git(["checkout", "--", "config.json"], cwd=app_dir, timeout=5.0)

        _prog(35, f"Baixando atualizações de origin/{GITHUB_BRANCH}...")
        proc_pull = _run_git(["pull", "--ff-only", "origin", GITHUB_BRANCH], cwd=app_dir, timeout=30.0)
        if proc_pull.returncode != 0:
            if cfg_backup is not None:
                cfg_path.write_bytes(cfg_backup)
            detalhe = (proc_pull.stderr or proc_pull.stdout or "").strip()
            return False, f"Falha no git pull:\n{detalhe}"

        # Restaura config.json preservando IPs/caminhos do técnico
        if cfg_backup is not None:
            _prog(65, "Restaurando configurações locais...")
            cfg_path.write_bytes(cfg_backup)

        # Instala dependências novas se requirements.txt mudou
        req_depois = req_path.read_bytes() if req_path.exists() else b""
        if req_depois != req_antes and req_path.exists():
            _prog(80, "Atualizando dependências Python (requirements.txt)...")
            subprocess.run(
                [sys.executable, "-m", "pip", "install", "-r", str(req_path)],
                cwd=str(app_dir),
                capture_output=True,
                text=True,
                timeout=180,
                creationflags=_CREATE_NO_WINDOW,
            )

        _prog(100, "Atualização concluída com sucesso!")
        return True, "Atualização via Git concluída! O Printer Assistant será reiniciado."
    except Exception as exc:
        if cfg_backup is not None:
            try:
                cfg_path.write_bytes(cfg_backup)
            except Exception:
                pass
        return False, f"Erro durante atualização via Git: {exc}"


def _localizar_raiz_extraida(pasta_extract: Path) -> Optional[Path]:
    """Encontra a pasta que contém o executável principal dentro do ZIP extraído."""
    for exe in pasta_extract.rglob("*.exe"):
        if "printerassistant" in exe.name.lower():
            return exe.parent
    for exe in pasta_extract.rglob("*.exe"):
        return exe.parent
    return None


def aplicar_atualizacao_exe(
    info: UpdateInfo,
    on_progress: Optional[Callable[[int, str], None]] = None,
) -> Tuple[bool, str, Optional[Path]]:
    """
    Baixa o ZIP da Release no GitHub, extrai em %TEMP% e gera um .bat auxiliar
    que substitui os arquivos após o fechamento do processo atual, preservando
    config.json, logs e relatórios, e reabre o executável atualizado.
    """
    def _prog(pct: int, msg: str):
        if on_progress:
            on_progress(pct, msg)

    if not info.download_url:
        return (
            False,
            "Esta Release no GitHub não possui um arquivo .zip anexado para download automático.",
            None,
        )

    app_dir = get_app_dir()
    exe_atual = Path(sys.executable).resolve()
    tmp_root = Path(tempfile.mkdtemp(prefix="pa_update_"))
    zip_path = tmp_root / (info.asset_nome or "update.zip")
    extract_dir = tmp_root / "extracted"

    try:
        _prog(5, f"Baixando {info.asset_nome or info.nova_versao}...")
        req = urllib.request.Request(
            info.download_url,
            headers={"User-Agent": _USER_AGENT},
        )
        with urllib.request.urlopen(req, timeout=30) as resp:
            total = int(resp.headers.get("Content-Length") or info.asset_tamanho or 0)
            baixado = 0
            bloco = 65536
            with open(zip_path, "wb") as out:
                while True:
                    chunk = resp.read(bloco)
                    if not chunk:
                        break
                    out.write(chunk)
                    baixado += len(chunk)
                    if total > 0:
                        pct = 5 + int((baixado / total) * 70)
                        mb_b = baixado / (1024 * 1024)
                        mb_t = total / (1024 * 1024)
                        _prog(min(pct, 75), f"Baixando... {mb_b:.1f} MB / {mb_t:.1f} MB")

        _prog(80, "Extraindo arquivos da nova versão...")
        extract_dir.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(zip_path, "r") as zf:
            zf.extractall(extract_dir)

        origem = _localizar_raiz_extraida(extract_dir)
        if origem is None:
            shutil.rmtree(tmp_root, ignore_errors=True)
            return False, "O arquivo ZIP baixado não contém um executável válido do Printer Assistant.", None

        exe_novo_nome = exe_atual.name
        if not (origem / exe_novo_nome).exists():
            candidatos_exe = list(origem.glob("*.exe"))
            if candidatos_exe:
                exe_novo_nome = candidatos_exe[0].name

        _prog(95, "Preparando substituição segura dos arquivos...")
        bat_path = Path(tempfile.gettempdir()) / f"pa_apply_update_{os.getpid()}.bat"
        pid_atual = os.getpid()
        exe_final = app_dir / exe_novo_nome

        bat_conteudo = f"""@echo off
setlocal
set "PID={pid_atual}"
set "SRC={origem}"
set "DST={app_dir}"
set "TMP={tmp_root}"
set "EXE={exe_final}"

REM Aguarda o encerramento do Printer Assistant atual (ate 20s)
set /a COUNT=0
:WAITLOOP
tasklist /FI "PID eq %PID%" 2>NUL | find /I "%PID%" >NUL
if "%ERRORLEVEL%"=="0" (
    set /a COUNT+=1
    if %COUNT% GEQ 20 goto APPLY
    timeout /t 1 /nobreak >NUL
    goto WAITLOOP
)

:APPLY
REM Backup de config.json (raiz e _internal se existirem)
if exist "%DST%\\config.json" copy /Y "%DST%\\config.json" "%TMP%\\config_root.bak" >NUL
if exist "%DST%\\_internal\\config.json" copy /Y "%DST%\\_internal\\config.json" "%TMP%\\config_int.bak" >NUL

REM Copia arquivos novos preservando logs/relatorios existentes
robocopy "%SRC%" "%DST%" /E /R:4 /W:1 /NFL /NDL /NJH /NJS /NC /NS >NUL

REM Restaura configuracoes do tecnico
if exist "%TMP%\\config_root.bak" copy /Y "%TMP%\\config_root.bak" "%DST%\\config.json" >NUL
if exist "%TMP%\\config_int.bak" copy /Y "%TMP%\\config_int.bak" "%DST%\\_internal\\config.json" >NUL

REM Reabre o Printer Assistant atualizado
if exist "%EXE%" start "" "%EXE%"

REM Limpeza temporaria
rd /s /q "%TMP%" >NUL 2>&1
del "%~f0" >NUL 2>&1
"""
        bat_path.write_text(bat_conteudo, encoding="cp1252", errors="ignore")
        _prog(100, "Pronto! Reiniciando para aplicar atualização...")
        return True, "Download concluído! O Printer Assistant será fechado e reaberto atualizado.", bat_path

    except Exception as exc:
        shutil.rmtree(tmp_root, ignore_errors=True)
        return False, f"Erro ao baixar/extrair atualização: {exc}", None


def iniciar_script_atualizacao_exe(bat_path: Path) -> None:
    subprocess.Popen(
        ["cmd.exe", "/c", str(bat_path)],
        creationflags=_CREATE_NO_WINDOW | getattr(subprocess, "DETACHED_PROCESS", 0),
        close_fds=True,
    )


def reiniciar_aplicacao_python() -> None:
    app_dir = get_app_dir()
    main_py = app_dir / "main.py"
    subprocess.Popen(
        [sys.executable, str(main_py)],
        cwd=str(app_dir),
        close_fds=True,
    )
