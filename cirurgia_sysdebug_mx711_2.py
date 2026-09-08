from pathlib import Path
import ast
import re
import shutil

BASE = Path(r"C:\PrinterAssistant")
ARQUIVO = BASE / "core" / "sysdebug.py"
BACKUP = BASE / "core" / "sysdebug.py.bak-20260903-mx711-cirurgia2"

HTML = BASE / "logs" / "sysdebug" / "sysdebug_192_168_14_200_20260902" / "sysdebug_134039.html"

print("=" * 70)
print("CIRURGIA CONTROLADA #2")
print("=" * 70)

# ------------------------------------------------------------
# 1. Backup
# ------------------------------------------------------------

shutil.copy2(ARQUIVO, BACKUP)

print(f"Backup criado: {BACKUP}")
print()

# ------------------------------------------------------------
# 2. Ler arquivo
# ------------------------------------------------------------

texto = ARQUIVO.read_text(
    encoding="utf-8",
    errors="strict",
)

# ------------------------------------------------------------
# 3. Localizar a funcao
# ------------------------------------------------------------

inicio = texto.find("def extrair_consumiveis_sysdebug(")

if inicio < 0:
    raise SystemExit(
        "ABORTADO: funcao extrair_consumiveis_sysdebug nao encontrada."
    )

fim = texto.find(
    "\n# ============================================================\n# PARSER PRINCIPAL",
    inicio,
)

if fim < 0:
    raise SystemExit(
        "ABORTADO: final conhecido da funcao nao encontrado."
    )

funcao = texto[inicio:fim]

print("Funcao localizada.")
print()

# ------------------------------------------------------------
# 4. Garantir que ainda e a versao conhecida
# ------------------------------------------------------------

obrigatorios = [
    "padrao_imaging = re.compile(",
    "padrao_toner = re.compile(",
    "PROTE",
    "return consumiveis",
]

for marcador in obrigatorios:
    if marcador not in funcao:
        raise SystemExit(
            f"ABORTADO: marcador esperado ausente: {marcador}"
        )

# ------------------------------------------------------------
# 5. Garantir que nao inserimos duas vezes
# ------------------------------------------------------------

if "padrao_maintenance = re.compile(" in funcao:
    raise SystemExit(
        "ABORTADO: padrao_maintenance ja existe. "
        "Nao sera feita uma segunda insercao."
    )

# ------------------------------------------------------------
# 6. Localizar o return final
# ------------------------------------------------------------

alvo = "    return consumiveis"

ocorrencias = funcao.count(alvo)

if ocorrencias != 1:
    raise SystemExit(
        f"ABORTADO: esperado exatamente 1 'return consumiveis', "
        f"encontrados {ocorrencias}."
    )

# ------------------------------------------------------------
# 7. Novo bloco - SOMENTE Maintenance Kit
# ------------------------------------------------------------

novo_bloco = r'''
    # ========================================================
    # FUSOR / MAINTENANCE KIT
    # ========================================================
    #
    # O MX711 fornece o serial real no ST Supply Table Data.
    #
    # Aceitamos somente quando:
    #
    #   valid 1
    #   serialNumberIsReal 1
    #
    # Assim, valores como 000000000000 nao entram.
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

        # Nunca aceitar placeholder composto somente por zeros.
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
# 8. Inserir imediatamente antes do return
# ------------------------------------------------------------

funcao_nova = funcao.replace(
    alvo,
    novo_bloco + alvo,
    1,
)

# ------------------------------------------------------------
# 9. Validar estrutura Python antes de gravar
# ------------------------------------------------------------

texto_novo = (
    texto[:inicio]
    + funcao_nova
    + texto[fim:]
)

try:
    ast.parse(texto_novo)
except SyntaxError as erro:
    print("ERRO DE SINTAXE:")
    print(erro)
    print()
    print("ABORTADO: arquivo original NAO foi gravado.")
    raise SystemExit(1)

print("OK: sintaxe Python valida.")
print()

# ------------------------------------------------------------
# 10. Gravar
# ------------------------------------------------------------

ARQUIVO.write_text(
    texto_novo,
    encoding="utf-8",
    newline="",
)

print("OK: arquivo gravado.")
print()

# ------------------------------------------------------------
# 11. Validar novamente apos gravacao
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
    print()
    print("RESTAURANDO BACKUP...")

    shutil.copy2(BACKUP, ARQUIVO)

    print("OK: backup restaurado.")
    raise SystemExit(1)

print("OK: arquivo gravado continua com sintaxe valida.")
print()

# ------------------------------------------------------------
# 12. Teste funcional real do MX711
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
print("RESULTADO DO PARSER - MX711")
print("=" * 70)

print()
print("Serial da maquina:")
print(dados.get("serial"))

print()
print("Consumiveis encontrados:")
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

# ------------------------------------------------------------
# 13. Validacoes objetivas
# ------------------------------------------------------------

seriais = {
    s.get("numero_serie")
    for s in consumiveis
    if s.get("numero_serie")
}

print()

esperados = {
    "CAD213148EC4",
    "CAB1821928E9",
    "001225810317",
}

faltantes = esperados - seriais

if faltantes:
    print(
        "ATENCAO: faltaram os seguintes seriais:"
    )

    for serial in sorted(faltantes):
        print(" -", serial)

    raise SystemExit(2)

if "000000000000" in seriais:
    print(
        "ERRO: placeholder 000000000000 foi aceito."
    )
    raise SystemExit(3)

print("OK: CAD213148EC4 encontrado.")
print("OK: CAB1821928E9 encontrado.")
print("OK: 001225810317 encontrado.")
print("OK: 000000000000 nao foi aceito.")
print()
print("=" * 70)
print("CIRURGIA #2 CONCLUIDA COM SUCESSO")
print("=" * 70)
