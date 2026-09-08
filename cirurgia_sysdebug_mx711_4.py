from pathlib import Path
import ast
import re
import shutil
import sys

BASE = Path(r"C:\PrinterAssistant")
ARQUIVO = BASE / "core" / "sysdebug.py"

BACKUP = BASE / "core" / "sysdebug.py.bak-20260903-mx711-cirurgia4"

MX711 = BASE / "logs" / "sysdebug" / "sysdebug_192_168_14_200_20260902" / "sysdebug_134039.html"

MX611 = BASE / "dumps" / "mx611.txt"

print("=" * 70)
print("CIRURGIA CONTROLADA #4")
print("=" * 70)
print()

# ------------------------------------------------------------
# Ler arquivo atual
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
# Confirmar estado esperado
# ------------------------------------------------------------

if "padrao_maintenance = re.compile(" not in funcao:
    raise SystemExit(
        "ABORTADO: cirurgia anterior nao encontrada."
    )

if 'serialNumberIsReal\\s+1' not in funcao:
    raise SystemExit(
        "ABORTADO: validacao do Maintenance Kit nao encontrada."
    )

# ------------------------------------------------------------
# Localizar bloco original do padrao_toner
# ------------------------------------------------------------

padrao = re.compile(
    r'(?ms)'
    r'    padrao_toner = re\.compile\(\n'
    r'.*?'
    r'    \)\n'
)

matches = list(padrao.finditer(funcao))

if len(matches) != 1:
    raise SystemExit(
        f"ABORTADO: esperado 1 padrao_toner, encontrados {len(matches)}."
    )

padrao_atual = matches[0].group(0)

# ------------------------------------------------------------
# Novo padrao de toner
# ------------------------------------------------------------

novo_padrao = r'''    padrao_toner = re.compile(
        r"osikey\s+"
        r"([^,\r\n]*(?:Toner|Cartridge|Cartucho)[^,\r\n]*)"
        r",\s*serial\s+"
        r"([A-Za-z0-9][A-Za-z0-9_-]*)"
        r"\s+valid\s+1"
        r".{0,500}?"
        r"partNumber\s+"
        r"([A-Za-z0-9][A-Za-z0-9_-]*)",
        re.IGNORECASE | re.DOTALL,
    )
'''

funcao_nova = (
    funcao[:matches[0].start()]
    + novo_padrao
    + funcao[matches[0].end():]
)

# ------------------------------------------------------------
# Garantias
# ------------------------------------------------------------

if "padrao_toner = re.compile(" not in funcao_nova:
    raise SystemExit(
        "ABORTADO: novo padrao_toner nao encontrado."
    )

if "padrao_maintenance = re.compile(" not in funcao_nova:
    raise SystemExit(
        "ABORTADO: padrao Maintenance Kit desapareceu."
    )

if "padrao_imaging = re.compile(" not in funcao_nova:
    raise SystemExit(
        "ABORTADO: padrao Imaging Unit desapareceu."
    )

texto_novo = (
    texto[:inicio]
    + funcao_nova
    + texto[fim:]
)

# ------------------------------------------------------------
# Validar sintaxe antes de gravar
# ------------------------------------------------------------

try:
    ast.parse(texto_novo)
except SyntaxError as erro:
    print("ERRO DE SINTAXE:")
    print(erro)
    print("ABORTADO: nada foi gravado.")
    raise SystemExit(1)

print("OK: nova versao passou no ast.parse().")

# ------------------------------------------------------------
# Gravar
# ------------------------------------------------------------

ARQUIVO.write_text(
    texto_novo,
    encoding="utf-8",
    newline="",
)

print("OK: sysdebug.py gravado.")
print()

# ------------------------------------------------------------
# Validar arquivo gravado
# ------------------------------------------------------------

confirmacao = ARQUIVO.read_text(
    encoding="utf-8",
    errors="strict",
)

try:
    ast.parse(confirmacao)
except SyntaxError as erro:
    print("ERRO: arquivo gravado invalido.")
    print(erro)
    print("RESTAURANDO BACKUP...")
    shutil.copy2(BACKUP, ARQUIVO)
    print("OK: backup restaurado.")
    raise SystemExit(1)

# ------------------------------------------------------------
# Teste MX711
# ------------------------------------------------------------

sys.path.insert(0, str(BASE))

from core.sysdebug import parse_sysdebug

html_mx711 = MX711.read_text(
    encoding="utf-8",
    errors="ignore",
)

dados = parse_sysdebug(html_mx711)

print("=" * 70)
print("TESTE MX711")
print("=" * 70)
print()

print("Serial da maquina:", dados.get("serial"))
print()

for i, supply in enumerate(
    dados.get("consumiveis", []),
    start=1,
):
    print(
        f"[{i}] "
        f"tipo={supply.get('tipo')} | "
        f"nome={supply.get('nome')} | "
        f"serial={supply.get('numero_serie')} | "
        f"PN={supply.get('part_number')}"
    )

seriais_mx711 = {
    s.get("numero_serie")
    for s in dados.get("consumiveis", [])
    if s.get("numero_serie")
}

esperados_mx711 = {
    "CAD213148EC4",
    "CAB1821928E9",
    "001225810317",
}

if esperados_mx711 - seriais_mx711:
    print()
    print(
        "FALHA MX711 - faltantes:",
        ", ".join(sorted(esperados_mx711 - seriais_mx711)),
    )
    raise SystemExit(2)

if "000000000000" in seriais_mx711:
    raise SystemExit(
        "FALHA MX711: placeholder aceito."
    )

# Não pode haver Imaging Unit classificado como toner.
for supply in dados.get("consumiveis", []):
    nome = str(supply.get("nome") or "").lower()

    if "imaging unit" in nome and supply.get("tipo") == "toner":
        raise SystemExit(
            "FALHA MX711: Imaging Unit ainda foi classificado como toner."
        )

print()
print("OK MX711: 3 seriais esperados encontrados.")
print("OK MX711: Imaging Unit nao foi classificado como toner.")
print()

# ------------------------------------------------------------
# Teste MX611
# ------------------------------------------------------------

if MX611.exists():
    texto_mx611 = MX611.read_text(
        encoding="utf-8",
        errors="ignore",
    )

    dados_mx611 = parse_sysdebug(texto_mx611)

    print("=" * 70)
    print("TESTE MX611")
    print("=" * 70)
    print()

    print("Serial da maquina:", dados_mx611.get("serial"))
    print()

    for i, supply in enumerate(
        dados_mx611.get("consumiveis", []),
        start=1,
    ):
        print(
            f"[{i}] "
            f"tipo={supply.get('tipo')} | "
            f"nome={supply.get('nome')} | "
            f"serial={supply.get('numero_serie')} | "
            f"PN={supply.get('part_number')}"
        )

    seriais_mx611 = {
        s.get("numero_serie")
        for s in dados_mx611.get("consumiveis", [])
        if s.get("numero_serie")
    }

    if "000000000000" in seriais_mx611:
        raise SystemExit(
            "FALHA MX611: placeholder 000000000000 foi aceito."
        )

    print()
    print("OK MX611: placeholder nao aceito.")
else:
    print()
    print("AVISO: dumps\\mx611.txt nao encontrado; teste MX611 ignorado.")

print()
print("=" * 70)
print("CIRURGIA #4 CONCLUIDA COM SUCESSO")
print("=" * 70)
