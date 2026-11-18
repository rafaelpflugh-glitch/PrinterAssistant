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

def extrair_dados(device):
    """
    Extrai os dados necessários diretamente do PrinterDevice.

    NÃO realiza coleta.

    Retorna:

        fabricante
        modelo
        serial
        contador
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

    return (
        fabricante,
        modelo,
        serial,
        contador,
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
        f'TEXT 60,950,"1",0,2,2,'
        f'"CONTADOR: {contador}"\r\n'
    )

    # ========================================================
    # DATA DE EMISSÃO
    # ========================================================

    tspl += (
        f'TEXT 60,1020,"1",0,2,2,'
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
        ) = extrair_dados(
            session
        )

        from datetime import datetime
        data_emissao = datetime.now().strftime("%d/%m/%Y %H:%M")

        dados_tspl = gerar_etiqueta_ativo(
            fabricante=fabricante,
            modelo=modelo,
            serial=serial,
            contador=contador,
            data_emissao=data_emissao,
        )

        enviar_tsc(
            dados_tspl
        )

        return {
            "sucesso": True,

            "relatorio": "ativo",

            "tipo": "etiqueta_patrimonial",

            "impressora": IMPRESSORA_TSC,

            "porta": PORTA_TSC,

            "fabricante": fabricante,

            "modelo": modelo,

            "serial": serial,

            "contador": contador,

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
        device
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