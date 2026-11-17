"""
============================================================
PRINTER ASSISTANT
RELATÓRIO DE DEMONSTRAÇÃO
============================================================

Responsabilidade:

    - carregar a imagem oficial da página de demonstração;
    - converter a imagem para dados raster PCL;
    - montar um job PCL de uma única página;
    - enviar o job para a UST através da porta RAW 9100.

IMPORTANTE:

    ESTE MÓDULO NÃO É AMARRADO A NENHUM MODELO DE IMPRESSORA.

    A UST é apenas o destino do trabalho de impressão.

    Portanto:

        MX611
        MS510
        MX511
        MX622
        CS725
        etc.

    não possuem qualquer tratamento especial aqui.

    O PrinterDevice fornece apenas o IP já conhecido.

    NÃO existe:

        - descoberta de impressora;
        - consulta EWS;
        - SNMP;
        - PJL;
        - nova coleta;
        - identificação de modelo;
        - validação de serial.

============================================================
ARQUIVO DA IMAGEM
============================================================

    C:\\PrinterAssistant\\assets\\print\\too_dark\\check_1.jpg

============================================================
IMPRESSÃO
============================================================

    Protocolo: PCL encapsulado com UEL/PJL
    Transporte: RAW TCP
    Porta: 9100

============================================================
"""

from __future__ import annotations

import io
import socket
from pathlib import Path
from typing import Any


# ============================================================
# CONFIGURAÇÃO
# ============================================================

PROJECT_ROOT = Path(
    __file__
).resolve().parent.parent


PORTA_RAW = 9100


IMAGEM_DEMONSTRACAO = (
    PROJECT_ROOT
    / "assets"
    / "print"
    / "too_dark"
    / "check_1.jpg"
)


# ============================================================
# PARÂMETROS DE IMPRESSÃO
# ============================================================

# A imagem será impressa em 300 DPI.
#
# 300 DPI é um compromisso adequado para uma página de
# demonstração e mantém o tamanho do job PCL razoável.

DPI = 300


# Papel Carta.
#
# A página oficial da Lexmark é uma página de teste para
# avaliação de qualidade. A área raster é posicionada dentro
# de uma página Letter.
#
# Caso futuramente definamos A4 como padrão do relatório,
# alteramos somente estes parâmetros.

PAPER_WIDTH_INCHES = 8.5
PAPER_HEIGHT_INCHES = 11.0


# ============================================================
# LIMITES RASTER
# ============================================================

PAPER_WIDTH_DOTS = int(
    PAPER_WIDTH_INCHES * DPI
)

PAPER_HEIGHT_DOTS = int(
    PAPER_HEIGHT_INCHES * DPI
)


# Margem mínima de segurança.
#
# Evita colocar a imagem exatamente na borda física,
# considerando a área não imprimível típica das impressoras.

MARGEM_DOTS = int(
    0.25 * DPI
)


# ============================================================
# ERROS
# ============================================================

class DemonstracaoError(Exception):
    """
    Erro específico da Página de Demonstração.
    """

    pass


# ============================================================
# LOCALIZAR IMAGEM
# ============================================================

def localizar_imagem():
    """
    Localiza a imagem oficial da Página de Demonstração.

    Não acessa a internet.

    Retorna:
        pathlib.Path
    """

    candidatos = (
        IMAGEM_DEMONSTRACAO,

        # Compatibilidade com nomenclaturas usadas durante
        # os testes do projeto.
        PROJECT_ROOT
        / "assets"
        / "print"
        / "_too_dark_check_1.jpg",

        PROJECT_ROOT
        / "assets"
        / "print"
        / "too_dark_check_1.jpg",

        PROJECT_ROOT
        / "assets"
        / "print"
        / "_too"
        / "_dark"
        / "check_1.jpg",

        PROJECT_ROOT
        / "assets"
        / "print"
        / "_too_dark"
        / "check_1.jpg",
        
        # Teste de caminho absoluto hardcoded
        Path(r"C:\PrinterAssistant\assets\print\too_dark\check_1.jpg")
    )

    for caminho in candidatos:

        try:

            if caminho.is_file():

                return caminho

        except OSError:

            continue

    caminhos = "\n".join(
        f"    {caminho}"
        for caminho in candidatos
    )

    raise DemonstracaoError(
        "Imagem da Página de Demonstração "
        "não encontrada.\n\n"
        "Caminhos procurados:\n"
        f"{caminhos}"
    )


# ============================================================
# CARREGAR IMAGEM
# ============================================================

def _carregar_imagem(
    caminho: Path,
):
    """
    Carrega a imagem utilizando Pillow.

    Pillow é usado somente para preparar o raster.

    Não é feita nenhuma comunicação de rede.
    """

    try:

        from PIL import Image

    except ImportError as erro:

        raise DemonstracaoError(
            "O pacote Pillow não está instalado.\n\n"
            "Instale com:\n"
            "pip install pillow"
        ) from erro

    try:

        imagem = Image.open(
            caminho
        )

        # -----------------------------------------------------
        # Remove qualquer modo incomum.
        # -----------------------------------------------------

        imagem = imagem.convert(
            "L"
        )

        return imagem

    except Exception as erro:

        raise DemonstracaoError(
            "Não foi possível abrir a imagem "
            "da Página de Demonstração.\n\n"
            f"Arquivo:\n{caminho}\n\n"
            f"Erro:\n{erro}"
        ) from erro


# ============================================================
# PREPARAR RASTER
# ============================================================

def _preparar_raster(
    imagem,
):
    """
    Redimensiona a imagem mantendo a proporção.

    A imagem é encaixada na área imprimível da página.

    O resultado é convertido para 1 bit por pixel.

    PCL raster utiliza 1 bit por pixel para a página
    monocromática.
    """

    area_largura = (
        PAPER_WIDTH_DOTS
        - (2 * MARGEM_DOTS)
    )

    area_altura = (
        PAPER_HEIGHT_DOTS
        - (2 * MARGEM_DOTS)
    )

    largura_original, altura_original = (
        imagem.size
    )

    if (
        largura_original <= 0
        or altura_original <= 0
    ):

        raise DemonstracaoError(
            "A imagem da demonstração possui "
            "dimensões inválidas."
        )

    # --------------------------------------------------------
    # Escala mantendo proporção.
    # --------------------------------------------------------

    escala_largura = (
        area_largura
        / largura_original
    )

    escala_altura = (
        area_altura
        / altura_original
    )

    escala = min(
        escala_largura,
        escala_altura,
    )

    nova_largura = max(
        1,
        int(
            largura_original
            * escala
        ),
    )

    nova_altura = max(
        1,
        int(
            altura_original
            * escala
        ),
    )

    try:

        from PIL import Image

        imagem = imagem.resize(
            (
                nova_largura,
                nova_altura,
            ),
            Image.Resampling.LANCZOS,
        )

    except AttributeError:

        # Compatibilidade com Pillow antigo.

        imagem = imagem.resize(
            (
                nova_largura,
                nova_altura,
            )
        )

    # --------------------------------------------------------
    # Conversão para 1 bit.
    #
    # Floyd-Steinberg ajuda a preservar detalhes finos,
    # linhas e áreas cinzas da página de teste.
    # --------------------------------------------------------

    try:

        imagem = imagem.convert(
            "1",
            dither=2,
        )

    except TypeError:

        imagem = imagem.convert(
            "1"
        )

    return imagem


# ============================================================
# EMPACOTAR LINHA MONOCROMÁTICA
# ============================================================

def _empacotar_linha(
    pixels,
    largura,
):
    """
    Converte pixels 1-bit em bytes.

    No formato PCL:

        1 = pixel preto
        0 = pixel branco

    Os pixels são agrupados da esquerda para a direita,
    oito pixels por byte.
    """

    quantidade_bytes = (
        (largura + 7)
        // 8
    )

    linha = bytearray(
        quantidade_bytes
    )

    for x in range(
        largura
    ):

        pixel = pixels[x]

        # Pillow mode "1":
        #
        # 0   = preto
        # 255 = branco
        #
        # Para PCL queremos:
        #
        # bit 1 = preto

        if pixel == 0:

            indice_byte = (
                x // 8
            )

            indice_bit = (
                7 - (x % 8)
            )

            linha[
                indice_byte
            ] |= (
                1 << indice_bit
            )

    return bytes(
        linha
    )


# ============================================================
# GERAR RASTER PCL
# ============================================================

def _gerar_raster_pcl(
    imagem,
):
    """
    Gera a região raster PCL correspondente à imagem.

    Retorna:

        bytes_raster
        largura
        altura
    """

    largura, altura = (
        imagem.size
    )

    raster = bytearray()

    # --------------------------------------------------------
    # Para centralizar verticalmente na página.
    # Estas medidas estão em DOTS @ 300 DPI.
    # --------------------------------------------------------

    topo_dots = (
        PAPER_HEIGHT_DOTS
        - altura
    ) // 2

    esquerda_dots = (
        PAPER_WIDTH_DOTS
        - largura
    ) // 2

    if esquerda_dots < MARGEM_DOTS:
        esquerda_dots = MARGEM_DOTS

    if topo_dots < MARGEM_DOTS:
        topo_dots = MARGEM_DOTS

    # --------------------------------------------------------
    # CONVERSÃO PARA DECIPOINTS (1/720 de polegada)
    #
    # Os comandos \x1b&a#H e \x1b&a#V do PCL operam em 
    # decipoints, e não em dots. Se usarmos dots diretos
    # a impressora fará um posicionamento totalmente errado.
    # --------------------------------------------------------

    esquerda_decipoints = int((esquerda_dots / DPI) * 720)
    topo_decipoints = int((topo_dots / DPI) * 720)

    # --------------------------------------------------------
    # UEL (Universal Exit Language) E CABEÇALHO PJL
    #
    # Isso é EXTREMAMENTE NECESSÁRIO para impressoras Lexmark.
    # Se enviarmos PCL puro sem este cabeçalho, a Lexmark
    # na porta 9100 pode ignorar o Job completamente.
    # --------------------------------------------------------

    raster.extend(
        b"\x1b%-12345X@PJL\r\n"
    )
    
    raster.extend(
        b"@PJL ENTER LANGUAGE=PCL\r\n"
    )

    # --------------------------------------------------------
    # Inicialização PCL.
    # --------------------------------------------------------

    raster.extend(
        b"\x1bE"
    )

    # --------------------------------------------------------
    # Seleciona papel Letter.
    #
    # PCL:
    #
    # Esc & l 2 A
    # --------------------------------------------------------

    raster.extend(
        b"\x1b&l2A"
    )

    # --------------------------------------------------------
    # Orientação retrato.
    # --------------------------------------------------------

    raster.extend(
        b"\x1b&l0O"
    )

    # --------------------------------------------------------
    # 300 DPI.
    #
    # Esc * t 300 R
    # --------------------------------------------------------

    raster.extend(
        b"\x1b*t300R"
    )

    # --------------------------------------------------------
    # Posicionamento absoluto vertical (em decipoints).
    #
    # Esc & a # V
    # --------------------------------------------------------

    raster.extend(
        f"\x1b&a{topo_decipoints}V".encode(
            "ascii"
        )
    )

    # --------------------------------------------------------
    # Posicionamento horizontal (em decipoints).
    #
    # Esc & a # H
    # --------------------------------------------------------

    raster.extend(
        f"\x1b&a{esquerda_decipoints}H".encode(
            "ascii"
        )
    )

    # --------------------------------------------------------
    # Inicia raster gráfico.
    #
    # IMPORTANTE: Esc * r 0 A  (Usa o X atual)
    # Se for 1 A, ele ignora o decipoint e joga pra margem zero.
    # --------------------------------------------------------

    raster.extend(
        b"\x1b*r0A"
    )

    # --------------------------------------------------------
    # Define largura raster.
    #
    # Esc * r # S
    # --------------------------------------------------------

    raster.extend(
        f"\x1b*r{largura}S".encode(
            "ascii"
        )
    )

    # --------------------------------------------------------
    # Define altura raster.
    #
    # Esc * r # T
    # --------------------------------------------------------

    raster.extend(
        f"\x1b*r{altura}T".encode(
            "ascii"
        )
    )

    # --------------------------------------------------------
    # Dados raster.
    #
    # Otimizado com carregamento em bloco (pix) para performance.
    # --------------------------------------------------------

    pix = imagem.load()

    for y in range(
        altura
    ):

        pixels = [
            pix[x, y]
            for x in range(
                largura
            )
        ]

        linha = _empacotar_linha(
            pixels,
            largura,
        )

        raster.extend(
            f"\x1b*b{len(linha)}W".encode(
                "ascii"
            )
        )

        raster.extend(
            linha
        )

    # --------------------------------------------------------
    # Finaliza raster.
    #
    # Esc * r B
    # --------------------------------------------------------

    raster.extend(
        b"\x1b*rB"
    )

    # --------------------------------------------------------
    # Avança para próxima página / termina job PCL.
    # --------------------------------------------------------

    raster.extend(
        b"\x1bE"
    )

    # Form feed.
    # Garante a saída da página.
    raster.extend(
        b"\x0c"
    )

    # --------------------------------------------------------
    # UEL de Fechamento.
    # Encerra a sessão PCL adequadamente.
    # --------------------------------------------------------
    
    raster.extend(
        b"\x1b%-12345X"
    )

    return (
        bytes(raster),
        largura,
        altura,
        esquerda_dots,
        topo_dots,
    )


# ============================================================
# GERAR PCL COMPLETO
# ============================================================

def gerar_pcl(
    imagem_path=None,
):
    """
    Gera o job PCL completo da Página de Demonstração.

    Não envia nada para a rede.

    Parâmetro:

        imagem_path:
            caminho opcional da imagem.

    Retorna:

        bytes
    """

    if imagem_path is None:

        caminho = localizar_imagem()

    else:

        caminho = Path(
            imagem_path
        )

    if not caminho.is_file():

        raise DemonstracaoError(
            "A imagem da Página de Demonstração "
            "não existe:\n"
            f"{caminho}"
        )

    imagem = _carregar_imagem(
        caminho
    )

    imagem = _preparar_raster(
        imagem
    )

    try:

        (
            dados_pcl,
            largura,
            altura,
            esquerda,
            topo,
        ) = _gerar_raster_pcl(
            imagem
        )

    except Exception as erro:

        raise DemonstracaoError(
            "Não foi possível gerar "
            "o raster PCL da demonstração.\n\n"
            f"{erro}"
        ) from erro

    if not dados_pcl:

        raise DemonstracaoError(
            "O job PCL da demonstração "
            "foi gerado vazio."
        )

    return dados_pcl


# ============================================================
# OBTER IP DO DEVICE
# ============================================================

def _obter_ip(
    device=None,
    ip=None,
):
    """
    Obtém o IP já conhecido da UST.

    IMPORTANTE:

        Não realiza descoberta.

        Não faz ping.

        Não consulta SNMP.

        Não consulta EWS.

        Não consulta PJL.

    """

    if ip:

        return str(
            ip
        ).strip()

    if isinstance(device, str) and device.strip():

        return device.strip()

    if device is None:

        raise DemonstracaoError(
            "Nenhum PrinterDevice foi fornecido "
            "e nenhum IP foi informado."
        )

    # --------------------------------------------------------
    # Primeiro tenta atributo direto.
    # --------------------------------------------------------

    valor = getattr(
        device,
        "ip",
        None,
    )

    if valor:

        return str(
            valor
        ).strip()

    # --------------------------------------------------------
    # Depois tenta to_dict().
    # --------------------------------------------------------

    try:

        dados = device.to_dict()

    except Exception as erro:

        raise DemonstracaoError(
            "Não foi possível obter o IP "
            "já conhecido da UST.\n\n"
            f"{erro}"
        ) from erro

    if isinstance(
        dados,
        dict,
    ):

        valor = dados.get(
            "ip"
        )

        if valor:

            return str(
                valor
            ).strip()

    raise DemonstracaoError(
        "O PrinterDevice não possui "
        "um endereço IP disponível."
    )


# ============================================================
# ENVIAR RAW
# ============================================================

def enviar_raw(
    dados,
    ip,
    porta=PORTA_RAW,
    timeout=15,
):
    """
    Envia bytes RAW para a UST.

    Comunicação:

        TCP
        IP já conhecido
        porta 9100

    Não existe qualquer identificação da máquina aqui.
    """

    if not dados:

        raise DemonstracaoError(
            "Não há dados para enviar."
        )

    if not ip:

        raise DemonstracaoError(
            "O endereço IP da UST não foi informado."
        )

    ip = str(
        ip
    ).strip()

    try:

        porta = int(
            porta
        )

    except (
        TypeError,
        ValueError,
    ):

        raise DemonstracaoError(
            f"Porta RAW inválida: {porta}"
        )

    try:

        with socket.create_connection(
            (
                ip,
                porta,
            ),
            timeout=timeout,
        ) as conexao:

            conexao.sendall(
                dados
            )

    except socket.timeout as erro:

        raise DemonstracaoError(
            "Tempo esgotado ao enviar "
            "a Página de Demonstração.\n\n"
            f"Destino: {ip}:{porta}"
        ) from erro

    except OSError as erro:

        raise DemonstracaoError(
            "Não foi possível enviar "
            "a Página de Demonstração para a UST.\n\n"
            f"Destino: {ip}:{porta}\n\n"
            f"Erro: {erro}"
        ) from erro


# ============================================================
# IMPRIMIR RELATÓRIO DE DEMONSTRAÇÃO
# ============================================================

def imprimir_relatorio_demonstracao(
    device=None,
    imagem=None,
    ip=None,
    porta=PORTA_RAW,
    timeout=15,
):
    """
    Gera e envia a Página de Demonstração.

    Parâmetros:

        device:
            PrinterDevice já coletado ou IP string.

        imagem:
            Caminho opcional para a imagem oficial.

        ip:
            IP opcional da UST.

        porta:
            Porta RAW. Padrão: 9100.

        timeout:
            Timeout da conexão TCP.

    O método não realiza nenhuma coleta.

    O modelo da impressora não é utilizado.
    """

    # --------------------------------------------------------
    # IMAGEM
    # --------------------------------------------------------

    if imagem is None:

        caminho_imagem = (
            localizar_imagem()
        )

    else:

        caminho_imagem = Path(
            imagem
        )

    if not caminho_imagem.is_file():

        raise DemonstracaoError(
            "Imagem da Página de Demonstração "
            "não encontrada:\n"
            f"{caminho_imagem}"
        )

    # --------------------------------------------------------
    # IP
    # --------------------------------------------------------

    destino_ip = _obter_ip(
        device=device,
        ip=ip,
    )

    # --------------------------------------------------------
    # GERA PCL
    # --------------------------------------------------------

    dados_pcl = gerar_pcl(
        caminho_imagem
    )

    # --------------------------------------------------------
    # ENVIA
    # --------------------------------------------------------

    enviar_raw(
        dados_pcl,
        destino_ip,
        porta=porta,
        timeout=timeout,
    )

    # --------------------------------------------------------
    # RETORNO
    # --------------------------------------------------------

    return {
        "sucesso": True,
        "relatorio": "demonstracao",
        "destino": "UST",
        "ip": destino_ip,
        "porta": porta,
        "protocolo": "RAW/PCL",
        "imagem": str(
            caminho_imagem
        ),
        "bytes": len(
            dados_pcl
        ),
    }


# ============================================================
# FUNÇÃO DE COMPATIBILIDADE
# ============================================================

def imprimir(
    dados_pcl,
    ip,
    porta=PORTA_RAW,
):
    """
    Compatibilidade com o padrão utilizado por outros
    relatórios do Printer Assistant.

    Recebe dados PCL já preparados e envia para a UST.
    """

    if not dados_pcl:

        raise DemonstracaoError(
            "Dados PCL não fornecidos."
        )

    enviar_raw(
        dados_pcl,
        ip,
        porta=porta,
    )

    return {
        "sucesso": True,
        "destino": "UST",
        "ip": str(
            ip
        ),
        "porta": porta,
        "protocolo": "RAW/PCL",
        "bytes": len(
            dados_pcl
        ),
    }


# ============================================================
# PREPARAR RELATÓRIO
# ============================================================

def preparar_relatorio_demonstracao(
    imagem=None,
):
    """
    Apenas prepara o relatório.

    Não comunica com a impressora.

    Útil para testes e para a interface.
    """

    if imagem is None:

        caminho = localizar_imagem()

    else:

        caminho = Path(
            imagem
        )

    if not caminho.is_file():

        raise DemonstracaoError(
            "Imagem não encontrada:\n"
            f"{caminho}"
        )

    dados_pcl = gerar_pcl(
        caminho
    )

    return {
        "sucesso": True,
        "relatorio": "demonstracao",
        "imagem": str(
            caminho
        ),
        "dados_pcl": dados_pcl,
        "bytes": len(
            dados_pcl
        ),
        "protocolo": "RAW/PCL",
        "porta": PORTA_RAW,
    }


# ============================================================
# TESTE LOCAL
# ============================================================

if __name__ == "__main__":

    """
    Uso:

        python reports/demonstracao.py

    Esse teste NÃO imprime.

    Ele apenas verifica:

        - existência da imagem;
        - leitura da imagem;
        - geração do PCL.

    Para imprimir, a função
    imprimir_relatorio_demonstracao()
    precisa ser chamada explicitamente.
    """

    try:

        resultado = (
            preparar_relatorio_demonstracao()
        )

        print(
            "OK: Página de Demonstração preparada."
        )

        print(
            f"Imagem: {resultado['imagem']}"
        )

        print(
            f"Bytes PCL: {resultado['bytes']}"
        )

        print(
            f"Protocolo: {resultado['protocolo']}"
        )

        print(
            f"Porta: {resultado['porta']}"
        )

    except Exception as erro:

        print(
            "ERRO:"
        )

        print(
            erro
        )