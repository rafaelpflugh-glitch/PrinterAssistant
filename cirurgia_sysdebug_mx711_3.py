from pathlib import Path
import ast
import re
import shutil
import hashlib

BASE = Path(r"C:\PrinterAssistant")
ARQUIVO = BASE / "core" / "sysdebug.py"
BACKUP = BASE / "core" / "sysdebug.py.bak-20260903-mx711-cirurgia3"

HTML = BASE / "logs" / "sysdebug" / "sysdebug_192_168_14_200_20260902" / "sysdebug_134039.html"

print("=" * 70)
print("CIRURGIA CONTROLADA #3")
print("=" * 70)

# ------------------------------------------------------------
# BACKUP
# ------------------------------------------------------------

shutil.copy2(ARQUIVO, BACKUP)
print(f"Backup: {BACKUP}")
print()

# ------------------------------------------------------------
# LEITURA
# ------------------------------------------------------------

texto = ARQUIVO.read_text(
    encoding="utf-8",
    errors="strict",
)

inicio = texto.find("def extrair_consumiveis_sysdebug(")

if inicio < 0:
    raise SystemExit(
        "ABORTADO: funcao nao encontrada."
    )

# Procuramos o proximo parser principal para delimitar a funcao.
fim = texto.find(
    "\n# ============================================================\n# PARSER PRINCIPAL",
    inicio,
)

if fim < 0:
    raise SystemExit(
        "ABORTADO: fim da funcao nao encontrado."
    )

funcao = texto[inicio:fim]

# ------------------------------------------------------------
# CONFIRMACOES
# ------------------------------------------------------------

if "padrao_imaging = re.compile(" not in funcao:
    raise SystemExit(
        "ABORTADO: padrao_imaging nao encontrado."
    )

if "padrao_toner = re.compile(" not in funcao:
    raise SystemExit(
        "ABORTADO: padrao_toner nao encontrado."
    )

if "return consumiveis" not in funcao:
    raise SystemExit(
        "ABORTADO: return consumiveis nao encontrado."
    )

if "padrao_maintenance = re.compile(" in funcao:
    raise SystemExit(
        "ABORTADO: padrao_maintenance ja existe."
    )

# ------------------------------------------------------------
# LOCALIZAR O RETURN FINAL
# ------------------------------------------------------------

posicoes = [
    m.start()
    for m in re.finditer(
        r"(?m)^    return consumiveis\s*$",
        funcao,
    )
]

print("Returns finais encontrados:", len(posicoes))

if len(posicoes) != 1:
    raise SystemExit(
        "ABORTADO: esperado exatamente um return final "
        "indentado dentro da funcao."
    )

pos_return = posicoes[0]

# ------------------------------------------------------------
# BLOCO NOVO
# ------------------------------------------------------------

bloco = r'''
    # ========================================================
    # FUSOR / MAINTENANCE KIT
    # ========================================================
    #
    # O MX711 fornece o serial real no ST Supply Table Data.
    #
    # Aceitar somente quando o proprio SYSDEBUG confirma:
    #
    #   valid 1
    #   serialNumberIsReal 1
    #
    # Isso impede que placeholders como 000000000000
    # sejam apresentados como serial valido.
    #

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

    for encontrado in padrao_maintenance.finditer(
        texto_limpo
    ):

        nome = valor_limpo(
            encontrado.group(1)
        )

        serial = valor_limpo(
            encontrado.group(2)
        )

        if not serial:
            continue

        if re.fullmatch(r"0+", serial):
            continue

        consumiveis.append(
            {
                "tipo":
                    "fusor",

                "nome":
                    nome or "Maintenance Kit",

                "numero_serie":
                    serial,

                "part_number":
                    None,
            }
        )

'''

# ------------------------------------------------------------
# INSERCAO
# ------------------------------------------------------------

funcao_nova = (
    funcao[:pos_return]
    + bloco
    + funcao[pos_return:]
)

texto_novo = (
    texto[:inicio]
    + funcao_nova
    + texto[fim:]
)

# ------------------------------------------------------------
# VALIDAR ANTES DE GRAVAR
# ------------------------------------------------------------

try:
    ast.parse(texto_novo)
except SyntaxError as erro:
    print()
    print("ERRO DE SINTAXE.")
    print(erro)
    print()
    print("ABORTADO: arquivo original permanece intacto.")
    raise SystemExit(1)

print("OK: nova versao passou no ast.parse().")

# ------------------------------------------------------------
# GRAVAR
# ------------------------------------------------------------

ARQUIVO.write_text(
    texto_novo,
    encoding="utf-8",
    newline="",
)

print("OK: arquivo gravado.")
print()

# ------------------------------------------------------------
# VALIDAR ARQUIVO GRAVADO
# ------------------------------------------------------------

confirmacao = ARQUIVO.read_text(
    encoding="utf-8",
    errors="strict",
)

try:
    ast.parse(confirmacao)
except SyntaxError as erro:
    print("ERRO: arquivo gravado ficou invalido.")
    print(erro)
    print("Restaurando backup...")
    shutil.copy2(BACKUP, ARQUIVO)
    print("OK: backup restaurado.")
    raise SystemExit(1)

print("OK: arquivo gravado continua valido.")
print()

# ------------------------------------------------------------
# TESTE FUNCIONAL MX711
# ------------------------------------------------------------

import sys

sys.path.insert(0, str(BASE))

from core.sysdebug import parse_sysdebug

html = HTML.read_text(
    encoding="utf-8",
    errors="ignore",
)

dados = parse_sysdebug(html)

print("=" * 70)
print("VALIDACAO FUNCIONAL - MX711")
print("=" * 70)

print()
print("Serial da maquina:")
print(dados.get("serial"))

print()
print("Consumiveis:")
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

print()

faltantes = esperados - seriais

if faltantes:
    print("FALHA: seriais esperados ausentes:")
    for item in sorted(faltantes):
        print(" -", item)
    raise SystemExit(2)

if "000000000000" in seriais:
    print("FALHA: placeholder 000000000000 foi aceito.")
    raise SystemExit(3)

print("OK: CAD213148EC4")
print("OK: CAB1821928E9")
print("OK: 001225810317")
print("OK: nenhum placeholder de zeros aceito.")
print()
print("=" * 70)
print("CIRURGIA #3 CONCLUIDA COM SUCESSO")
print("=" * 70)
