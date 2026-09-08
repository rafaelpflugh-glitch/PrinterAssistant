from pathlib import Path
import ast
import re
import shutil
import subprocess
import sys

BASE = Path(r"C:\PrinterAssistant")
ARQUIVO = BASE / "core" / "sysdebug.py"
BACKUP = BASE / "core" / "sysdebug.py.bak-20260903-mx711-cirurgia"

HTML = BASE / "logs" / "sysdebug" / "sysdebug_192_168_14_200_20260902" / "sysdebug_134039.html"

PYTHON = Path(r"C:\Users\pflug\AppData\Local\hermes\hermes-agent\venv\Scripts\python.exe")

print("=" * 70)
print("CIRURGIA CONTROLADA - sysdebug.py")
print("=" * 70)

# ------------------------------------------------------------
# 1. Verificacoes iniciais
# ------------------------------------------------------------

if not ARQUIVO.exists():
    raise SystemExit(f"ERRO: arquivo nao encontrado: {ARQUIVO}")

if not HTML.exists():
    raise SystemExit(f"ERRO: SYSDEBUG MX711 nao encontrado: {HTML}")

print(f"Arquivo: {ARQUIVO}")
print(f"SYSDEBUG: {HTML}")
print()

# ------------------------------------------------------------
# 2. Backup
# ------------------------------------------------------------

shutil.copy2(ARQUIVO, BACKUP)

print(f"BACKUP CRIADO: {BACKUP}")
print()

# ------------------------------------------------------------
# 3. Ler arquivo
# ------------------------------------------------------------

texto = ARQUIVO.read_text(
    encoding="utf-8",
    errors="strict",
)

# ------------------------------------------------------------
# 4. Localizar exatamente uma funcao
# ------------------------------------------------------------

padrao_funcao = re.compile(
    r"(?ms)^def extrair_consumiveis_sysdebug\("
    r".*?"
    r"(?=^def |\Z)"
)

matches = list(padrao_funcao.finditer(texto))

print(f"Funcoes encontradas: {len(matches)}")

if len(matches) != 1:
    raise SystemExit(
        "ABORTADO: quantidade inesperada de funcoes "
        "extrair_consumiveis_sysdebug()."
    )

funcao_atual = matches[0].group(0)

print(
    "Funcao localizada:",
    f"{matches[0].start()} -> {matches[0].end()}"
)
print()

# ------------------------------------------------------------
# 5. Confirmar que estamos mexendo na versao esperada
# ------------------------------------------------------------

marcadores_obrigatorios = [
    "padrao_imaging",
    "padrao_toner",
    "FUSOR / MAINTENANCE KIT",
]

for marcador in marcadores_obrigatorios:
    if marcador not in funcao_atual:
        raise SystemExit(
            f"ABORTADO: marcador esperado nao encontrado: {marcador}"
        )

# ------------------------------------------------------------
# 6. Substituir SOMENTE o bloco que ignora Maintenance Kit
# ------------------------------------------------------------

padrao_ignora_maintenance = re.compile(
    r"(?ms)"
    r"(?P<indent>^[ \t]*)# FUSOR / MAINTENANCE KIT.*?"
    r"(?=^[ \t]*consumiveis\s*=|^[ \t]*padrao_imaging)"
)

# A funcao atual pode ter o comentario/bloco em outra posicao.
# Em vez de depender dele para toda a funcao, fazemos uma
# substituicao precisa do trecho que declara o bloqueio.

bloqueio = re.search(
    r"(?ms)"
    r"(?P<indent>^[ \t]*)# FUSOR / MAINTENANCE KIT"
    r".*?"
    r"(?=^[ \t]*padrao_imaging)",
    funcao_atual,
)

if not bloqueio:
    raise SystemExit(
        "ABORTADO: nao encontrei o bloco conhecido "
        "'# FUSOR / MAINTENANCE KIT'."
    )

trecho_bloqueio = bloqueio.group(0)

if "É deliberadamente ignorado" not in trecho_bloqueio and \
   "deliberadamente ignorado" not in trecho_bloqueio and \
   "deliberadamente ignorado" not in trecho_bloqueio.lower():
    print(
        "AVISO: texto do bloqueio diferente do esperado."
    )
    print("Trecho encontrado:")
    print(trecho_bloqueio)
    raise SystemExit(
        "ABORTADO por seguranca: nao reconheci o bloco original."
    )

# Removemos apenas o bloco de comentario/protecao.
funcao_nova = (
    funcao_atual[:bloqueio.start()]
    + funcao_atual[bloqueio.end():]
)

# ------------------------------------------------------------
# 7. Inserir extracao real do Maintenance Kit
# ------------------------------------------------------------

alvo = (
    "    padrao_imaging = re.compile("
)

if alvo not in funcao_nova:
    raise SystemExit(
        "ABORTADO: ponto de insercao da nova extracao nao encontrado."
    )

insercao = r'''    # FUSOR / MAINTENANCE KIT
    #
    # Somente aceitar serial quando o proprio SYSDEBUG confirma
    # que o numero e real:
    #   valid 1
    #   serialNumberIsReal 1
    #
    # Isso evita transformar placeholders como
    # 000000000000 em numero de serie valido.
    padrao_maintenance = re.compile(
        r"osikey\s+"
        r"(Maintenance\s+Kit|Fuser|Kit\s+Maintenance)"
        r"\s*,\s*serial\s+"
        r"([A-Za-z0-9][A-Za-z0-9_-]*)"
        r"\s+valid\s+1"
        r".{0,2500}?"
        r"serialNumberIsReal\s+1",
        re.IGNORECASE | re.DOTALL,
    )

'''

funcao_nova = funcao_nova.replace(
    alvo,
    insercao + alvo,
    1,
)

# ------------------------------------------------------------
# 8. Inserir processamento do Maintenance Kit
# ------------------------------------------------------------

alvo2 = (
    "    padrao_toner = re.compile("
)

if alvo2 not in funcao_nova:
    raise SystemExit(
        "ABORTADO: segundo ponto de insercao nao encontrado."
    )

processamento = r'''    for match in padrao_maintenance.finditer(texto):
        nome = valor_limpo(match.group(1))
        serial = valor_limpo(match.group(2))

        if not serial:
            continue

        if re.fullmatch(r"0+", serial):
            continue

        consumiveis.append(
            {
                "tipo": "fusor",
                "nome": "Maintenance Kit",
                "numero_serie": serial,
                "part_number": None,
            }
        )

'''

funcao_nova = funcao_nova.replace(
    alvo2,
    processamento + alvo2,
    1,
)

# ------------------------------------------------------------
# 9. Garantias antes de gravar
# ------------------------------------------------------------

if "padrao_maintenance" not in funcao_nova:
    raise SystemExit(
        "ABORTADO: padrao_maintenance nao apareceu na nova funcao."
    )

if 'serialNumberIsReal\\s+1' not in funcao_nova:
    raise SystemExit(
        "ABORTADO: validacao serialNumberIsReal nao apareceu."
    )

if '"tipo": "fusor"' not in funcao_nova:
    raise SystemExit(
        "ABORTADO: tipo fusor nao apareceu na nova funcao."
    )

# ------------------------------------------------------------
# 10. Montar novo arquivo
# ------------------------------------------------------------

texto_novo = (
    texto[:matches[0].start()]
    + funcao_nova
    + texto[matches[0].end():]
)

# ------------------------------------------------------------
# 11. Validar sintaxe Python ANTES de gravar
# ------------------------------------------------------------

try:
    ast.parse(texto_novo)
except SyntaxError as erro:
    print()
    print("ERRO DE SINTAXE NA NOVA VERSAO.")
    print(erro)
    print()
    print("ABORTADO: arquivo original permanece intacto.")
    raise SystemExit(1)

# ------------------------------------------------------------
# 12. Gravar
# ------------------------------------------------------------

ARQUIVO.write_text(
    texto_novo,
    encoding="utf-8",
    newline="",
)

print("OK: nova versao passou no ast.parse().")
print("OK: arquivo gravado.")
print()

# ------------------------------------------------------------
# 13. Reabrir e validar novamente
# ------------------------------------------------------------

verificacao = ARQUIVO.read_text(
    encoding="utf-8",
    errors="strict",
)

try:
    ast.parse(verificacao)
except SyntaxError as erro:
    shutil.copy2(BACKUP, ARQUIVO)
    print("ERRO: arquivo gravado ficou invalido.")
    print("BACKUP RESTAURADO.")
    raise SystemExit(1)

print("OK: sysdebug.py continua com sintaxe Python valida.")
print()

# ------------------------------------------------------------
# 14. Teste REAL contra o SYSDEBUG do MX711
# ------------------------------------------------------------

texto_html = HTML.read_text(
    encoding="utf-8",
    errors="ignore",
)

sys.path.insert(0, str(BASE))

from core.sysdebug import parse_sysdebug

dados = parse_sysdebug(texto_html)

print("=" * 70)
print("VALIDACAO DO MX711")
print("=" * 70)

print("Serial da maquina:")
print(dados.get("serial"))
print()

print("Consumiveis extraidos:")
print()

consumiveis = dados.get("consumiveis", [])

for i, supply in enumerate(consumiveis, 1):
    print(
        f"[{i}] "
        f"tipo={supply.get('tipo')} | "
        f"nome={supply.get('nome')} | "
        f"serial={supply.get('numero_serie')} | "
        f"PN={supply.get('part_number')}"
    )

print()

# ------------------------------------------------------------
# 15. Validacao objetiva do resultado esperado
# ------------------------------------------------------------

seriais = {
    s.get("numero_serie")
    for s in consumiveis
    if s.get("numero_serie")
}

esperados = {
    "CAD213148EC4",
    "CAB1821928E9",
    "001225810317",
}

faltantes = esperados - seriais

if faltantes:
    print("ATENCAO: resultado nao contem todos os seriais esperados.")
    print("Faltantes:", ", ".join(sorted(faltantes)))
    print()
    print("O BACKUP NAO FOI RESTAURADO automaticamente,")
    print("porque a alteracao passou pela validacao de sintaxe,")
    print("mas o resultado funcional precisa ser analisado.")
    raise SystemExit(2)

print("OK: os 3 seriais esperados foram encontrados.")
print()
print("CAD213148EC4  -> Toner")
print("CAB1821928E9  -> Imaging Unit")
print("001225810317  -> Maintenance Kit")
print()
print("=" * 70)
print("CIRURGIA CONCLUIDA COM SUCESSO")
print("=" * 70)
