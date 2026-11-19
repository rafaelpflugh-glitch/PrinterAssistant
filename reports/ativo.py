"""
============================================================
PRINTER ASSISTANT
RELATÓRIO DE ATIVO
============================================================

Responsabilidades:

    - receber um PrinterDevice já coletado;
    - utilizar somente os dados existentes no dispositivo;
    - preparar a etiqueta patrimonial;
    - enviar a etiqueta para a TSC;
    - NÃO realizar nova coleta.

IMPORTANTE
------------------------------------------------------------

Este módulo NÃO consulta:

    - PJL
    - SYSDEBUG
    - SNMP
    - HTTP
    - Lexmark

O PrinterDevice já deve estar previamente coletado.

O contador utilizado na etiqueta é o contador existente
em:

    device.identificacao["contador"]

A TSC é a impressora de etiquetas:

    IP   : 192.168.14.151
    PORTA: 9100

Formato atual da etiqueta:

    100 x 150 mm
    GAP 2 mm

============================================================
"""

import socket

from core.base_report import BaseReport

try:
    from core.config import resolver_ip
except ImportError:
    def resolver_ip(ip, tipo="relatorio"):
        return ip


# ============================================================
# CONFIGURAÇÃO DA TSC
# ============================================================

IMPRESSORA_TSC = "192.168.14.151"
PORTA_TSC = 9100


# ============================================================
# ERRO
# ============================================================

class AtivoReportError(Exception):
    """
    Erro controlado do Relatório de Ativo.
    """

    pass


# ============================================================
# UTILIDADES
# ============================================================

def texto(valor, padrao="DESCONHECIDO"):
    """
    Converte um valor para texto seguro para impressão.
    """

    if valor is None:
        return padrao

    valor = str(valor).strip()

    if not valor:
        return padrao

    return valor


def contador_texto(valor):
    """
    Formata o contador para apresentação.

    Exemplo:

        14483 -> 14.483

    Se o contador não estiver disponível, retorna N/D.
    """

    if valor is None:
        return "N/D"

    try:

        numero = int(valor)

        return f"{numero:,}".replace(
            ",",
            ".",
        )

    except (
        TypeError,
        ValueError,
    ):

        return str(valor)


def escapar_tspl(valor):
    """
    Prepara texto para ser colocado dentro de uma string TSPL.

    Aspas são removidas/substituídas para impedir que um valor
    vindo da impressora quebre o comando TSPL.
    """

    if valor is None:
        return ""

    valor = str(valor)

    valor = valor.replace(
        '"',
        "'",
    )

    valor = valor.replace(
        "\r",
        " ",
    )

    valor = valor.replace(
        "\n",
        " ",
    )

    return valor.strip()


# ============================================================
# EXTRAIR DADOS DO DEVICE
# ============================================================

def extrair_dados(
    device,
    toner_presente=None,
    unidade_presente=None,
):
    """
    Extrai os dados necessários diretamente do PrinterDevice, incluindo presença de suprimentos.

    NÃO realiza coleta.

    Retorna:
        fabricante, modelo, serial, contador, status_toner, status_unidade
    """

    if device is None:

        raise AtivoReportError(
            "Nenhuma impressora ativa."
        )

    # --------------------------------------------------------
    # IDENTIFICAÇÃO
    # --------------------------------------------------------

    identificacao = getattr(
        device,
        "identificacao",
        None,
    )

    if not isinstance(
        identificacao,
        dict,
    ):

        # Compatibilidade caso algum objeto forneça apenas
        # to_dict().
        if hasattr(
            device,
            "to_dict",
        ):

            dados = device.to_dict()

            if isinstance(
                dados,
                dict,
            ):

                identificacao = dados.get(
                    "identificacao",
                    {},
                )

        if not isinstance(
            identificacao,
            dict,
        ):

            identificacao = {}

    fabricante = texto(
        identificacao.get(
            "fabricante"
        ),
        "DESCONHECIDO",
    )

    modelo = texto(
        identificacao.get(
            "modelo"
        ),
        "DESCONHECIDO",
    )

    serial = texto(
        identificacao.get(
            "serial"
        ),
        "SEM SERIAL",
    )

    contador = identificacao.get(
        "contador"
    )

    # --------------------------------------------------------
    # STATUS DOS SUPRIMENTOS (TONER E UNIDADE DE IMAGEM)
    # --------------------------------------------------------
    supplies = getattr(device, "supplies", [])
    if not supplies and hasattr(device, "to_dict"):
        try:
            supplies = device.to_dict().get("supplies", [])
        except Exception:
            supplies = []

    toner_detectado = False
    toner_nivel = None
    unidade_detectada = False
    unidade_nivel = None

    for s in supplies:
        if not isinstance(s, dict):
            continue
        tipo = str(s.get("tipo", "")).lower()
        nome = str(s.get("nome", "") or s.get("descricao", "")).lower()
        nivel = s.get("nivel")
        status = str(s.get("status", "") or s.get("condicao", "")).upper()
        serial_s = str(s.get("numero_serie", "") or s.get("serial", "")).strip()

        eh_ausente = (
            status in ("AUSENTE", "FALTA", "NAO_INSTALADO", "NÃO INSTALADO", "ERRO_GRAVE", "SEM SUPRIMENTO")
            or str(nivel).lower() in ("ausente", "none", "-1")
        )

        if "toner" in tipo or "toner" in nome or "cartucho" in tipo:
            if not eh_ausente and (nivel is not None and nivel >= 0 or serial_s):
                toner_detectado = True
                toner_nivel = nivel

        if any(k in tipo or k in nome for k in ["unidade", "imaging", "photoconductor", "fotocondutor", "drum"]):
            if not eh_ausente and (nivel is not None and nivel >= 0 or serial_s):
                unidade_detectada = True
                unidade_nivel = nivel

    if toner_presente is not None:
        if toner_presente:
            status_toner = f"INSTALADO ({toner_nivel}%)" if (toner_nivel is not None and toner_nivel >= 0) else "INSTALADO"
        else:
            status_toner = "NAO ACOMPANHA"
    else:
        if toner_detectado:
            status_toner = f"INSTALADO ({toner_nivel}%)" if (toner_nivel is not None and toner_nivel >= 0) else "INSTALADO"
        else:
            status_toner = "NAO ACOMPANHA"

    if unidade_presente is not None:
        if unidade_presente:
            status_unidade = f"INSTALADA ({unidade_nivel}%)" if (unidade_nivel is not None and unidade_nivel >= 0) else "INSTALADA"
        else:
            status_unidade = "NAO ACOMPANHA"
    else:
        if unidade_detectada:
            status_unidade = f"INSTALADA ({unidade_nivel}%)" if (unidade_nivel is not None and unidade_nivel >= 0) else "INSTALADA"
        elif str(fabricante).strip().lower() == "canon" or "ir" in str(modelo).lower():
            status_unidade = "INTEGRADA AO TONER"
        else:
            status_unidade = "NAO ACOMPANHA"

    return (
        fabricante,
        modelo,
        serial,
        contador,
        status_toner,
        status_unidade,
    )


# ============================================================
# GERAR TSPL
# ============================================================

def gerar_etiqueta_ativo(
    fabricante,
    modelo,
    serial,
    contador,
    data_emissao=None,
    status_toner="INSTALADO",
    status_unidade="INSTALADA",
):
    """
    Gera a etiqueta TSPL.

    A TSC recebe diretamente os comandos.

    Não existe nenhuma consulta à Lexmark nesta função.
    """

    if data_emissao is None:
        from datetime import datetime
        data_emissao = datetime.now().strftime("%d/%m/%Y %H:%M")

    fabricante = escapar_tspl(
        texto(
            fabricante,
            "DESCONHECIDO",
        )
    )

    modelo = escapar_tspl(
        texto(
            modelo,
            "DESCONHECIDO",
        )
    )

    serial = escapar_tspl(
        texto(
            serial,
            "SEM SERIAL",
        )
    )

    contador = escapar_tspl(
        contador_texto(
            contador
        )
    )

    status_toner_tspl = escapar_tspl(
        texto(
            status_toner,
            "N/D",
        )
    )

    status_unidade_tspl = escapar_tspl(
        texto(
            status_unidade,
            "N/D",
        )
    )

    data_emissao_tspl = escapar_tspl(
        texto(
            data_emissao,
            "",
        )
    )

    tspl = ""

    # ========================================================
    # CONFIGURAÇÃO DA ETIQUETA
    # ========================================================

    tspl += (
        "SIZE 100 mm,150 mm\r\n"
    )

    tspl += (
        "GAP 2 mm,0 mm\r\n"
    )

    tspl += (
        "REFERENCE 0,0\r\n"
    )

    tspl += (
        "CODEPAGE 1252\r\n"
    )

    tspl += (
        "CLS\r\n"
    )

    # ========================================================
    # TÍTULO
    # ========================================================

    tspl += (
        'TEXT 60,50,"3",0,1,1,'
        '"PRINTER ASSISTANT"\r\n'
    )

    tspl += (
        'TEXT 60,100,"2",0,2,2,'
        '"RELATORIO DE ATIVO"\r\n'
    )

    # ========================================================
    # FABRICANTE
    # ========================================================

    tspl += (
        'TEXT 60,220,"1",0,2,2,'
        '"FABRICANTE"\r\n'
    )

    tspl += (
        f'TEXT 60,260,"2",0,2,2,'
        f'"{fabricante}"\r\n'
    )

    # ========================================================
    # MODELO
    # ========================================================

    tspl += (
        'TEXT 60,380,"1",0,2,2,'
        '"MODELO"\r\n'
    )

    tspl += (
        f'TEXT 60,420,"2",0,2,2,'
        f'"{modelo}"\r\n'
    )

    # ========================================================
    # NÚMERO DE SÉRIE
    # ========================================================

    tspl += (
        'TEXT 60,540,"1",0,2,2,'
        '"NUMERO DE SERIE"\r\n'
    )

    tspl += (
        f'TEXT 60,580,"2",0,2,2,'
        f'"{serial}"\r\n'
    )

    # ========================================================
    # CÓDIGO DE BARRAS
    # ========================================================

    tspl += (
        f'BARCODE 100,700,"128",140,1,0,3,3,'
        f'"{serial}"\r\n'
    )

    # ========================================================
    # CONTADOR
    # ========================================================

    tspl += (
        f'TEXT 60,910,"1",0,2,2,'
        f'"CONTADOR: {contador}"\r\n'
    )

    # ========================================================
    # SUPRIMENTOS (TONER E UNIDADE DE IMAGEM)
    # ========================================================

    if str(fabricante).strip().upper() == "CANON" or "INTEGRADA" in str(status_unidade_tspl).upper():
        tspl += (
            f'TEXT 60,970,"1",0,2,2,'
            f'"SISTEMA : CARTUCHO INTEGRADO"\r\n'
        )
        tspl += (
            f'TEXT 60,1030,"1",0,2,2,'
            f'"TONER   : {status_toner_tspl}"\r\n'
        )
    else:
        tspl += (
            f'TEXT 60,970,"1",0,2,2,'
            f'"TONER   : {status_toner_tspl}"\r\n'
        )
        tspl += (
            f'TEXT 60,1030,"1",0,2,2,'
            f'"UNIDADE : {status_unidade_tspl}"\r\n'
        )

    # ========================================================
    # DATA DE EMISSÃO
    # ========================================================

    tspl += (
        f'TEXT 60,1090,"1",0,2,2,'
        f'"EMISSAO : {data_emissao_tspl}"\r\n'
    )

    # ========================================================
    # IMPRIMIR UMA ETIQUETA
    # ========================================================

    tspl += (
        "PRINT 1\r\n"
    )

    return tspl.encode(
        "cp1252",
        errors="replace",
    )


# ============================================================
# ENVIAR PARA A TSC
# ============================================================

def enviar_tsc(
    dados,
    ip=IMPRESSORA_TSC,
    porta=PORTA_TSC,
):
    """
    Envia os comandos TSPL diretamente para a TSC.

    Não realiza nenhuma coleta.
    """

    if not dados:

        raise AtivoReportError(
            "A etiqueta gerada está vazia."
        )

    ip = resolver_ip(ip, tipo="relatorio")

    if not ip:

        raise AtivoReportError(
            "IP da TSC não informado."
        )

    try:

        with socket.create_connection(
            (
                ip,
                porta,
            ),
            timeout=10,
        ) as sock:

            sock.sendall(
                dados
            )

    except OSError as erro:

        raise AtivoReportError(
            "Não foi possível enviar a etiqueta "
            f"para a TSC {ip}:{porta}.\n\n"
            f"{erro}"
        ) from erro

    return True


# ============================================================
# REPORT ATIVO
# ============================================================

class ReportAtivo(BaseReport):

    title = "Relatório de Ativo"

    description = (
        "Etiqueta patrimonial da impressora "
        "com fabricante, modelo, serial, "
        "código de barras e contador."
    )

    category = "Relatórios"

    # ========================================================
    # GERAÇÃO
    # ========================================================

    def generate(
        self,
        session,
        toner_presente=None,
        unidade_presente=None,
        data_emissao=None,
    ):
        """
        Gera e imprime a etiqueta de ativo.

        'session' é o PrinterDevice já coletado.

        NÃO realiza nova coleta.
        """

        (
            fabricante,
            modelo,
            serial,
            contador,
            status_toner,
            status_unidade,
        ) = extrair_dados(
            session,
            toner_presente=toner_presente,
            unidade_presente=unidade_presente,
        )

        if data_emissao is None:
            from datetime import datetime
            data_emissao = datetime.now().strftime("%d/%m/%Y %H:%M")

        dados_tspl = gerar_etiqueta_ativo(
            fabricante=fabricante,
            modelo=modelo,
            serial=serial,
            contador=contador,
            data_emissao=data_emissao,
            status_toner=status_toner,
            status_unidade=status_unidade,
        )

        enviar_tsc(
            dados_tspl
        )

        dest_ip = resolver_ip(IMPRESSORA_TSC, tipo="relatorio")

        return {
            "sucesso": True,

            "relatorio": "ativo",

            "tipo": "etiqueta_patrimonial",

            "impressora": dest_ip,

            "porta": PORTA_TSC,

            "fabricante": fabricante,

            "modelo": modelo,

            "serial": serial,

            "contador": contador,

            "status_toner": status_toner,

            "status_unidade": status_unidade,

            "data_emissao": data_emissao,

            "bytes": len(
                dados_tspl
            ),

            "mensagem": (
                "Etiqueta de ativo enviada "
                "para a TSC com sucesso."
            ),
        }


# ============================================================
# FUNÇÃO PÚBLICA
# ============================================================

def imprimir_relatorio_ativo(
    device,
    toner_presente=None,
    unidade_presente=None,
    data_emissao=None,
):
    """
    Função pública utilizada pelo ReportService.

    Recebe um PrinterDevice.

    NÃO realiza nova coleta.

    O contador é retirado do próprio device.
    """

    if device is None:

        raise AtivoReportError(
            "Nenhuma impressora foi fornecida."
        )

    relatorio = ReportAtivo()

    return relatorio.generate(
        device,
        toner_presente=toner_presente,
        unidade_presente=unidade_presente,
        data_emissao=data_emissao,
    )


# ============================================================
# TESTE DIRETO
# ============================================================

def teste():

    print()
    print("=" * 72)
    print(
        "PRINTER ASSISTANT - TESTE RELATÓRIO DE ATIVO"
    )
    print("=" * 72)
    print()

    print(
        "Este teste espera um PrinterDevice real."
    )

    print(
        "Não será realizada nenhuma coleta."
    )

    print()


if __name__ == "__main__":

    teste()