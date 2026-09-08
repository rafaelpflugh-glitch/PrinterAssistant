"""
============================================================
PRINTER ASSISTANT
SNMP MODULE
============================================================

Módulo SNMP principal do Printer Assistant.

Responsabilidades:
- identificar a impressora via SNMP
- tentar SNMPv2c e depois SNMPv1
- coletar Printer-MIB
- coletar consumíveis
- calcular nível e condição
- identificar toner, unidade de imagem e fusor
- tentar localizar números de série dos consumíveis
- manter part number apenas nos dados internos
- aplicar regra de garantia somente à unidade de imagem
- preservar dados brutos para diagnóstico

Compatível com:
- Python 3.x
- pysnmp 7.x
- SNMPv1
- SNMPv2c
"""

import asyncio
import re
from typing import Any


from pysnmp.hlapi.v3arch.asyncio import (
    SnmpEngine,
    CommunityData,
    UdpTransportTarget,
    ContextData,
    ObjectType,
    ObjectIdentity,
    get_cmd,
    walk_cmd,
)


# ============================================================
# CONFIGURAÇÃO
# ============================================================

COMMUNITY_PADRAO = "public"

TIMEOUT_PADRAO = 2

RETRIES_PADRAO = 1

SNMP_V2C = 1

SNMP_V1 = 0


# ============================================================
# OIDS
# ============================================================

OID_SYS_DESCRICAO = (
    "1.3.6.1.2.1.1.1.0"
)


# ============================================================
# PRINTER-MIB
# ============================================================

OID_SUPPLIES_BASE = (
    "1.3.6.1.2.1.43.11.1.1"
)

OID_SUPPLY_INDEX = (
    "1.3.6.1.2.1.43.11.1.1.2"
)

OID_SUPPLY_DESCRIPTION = (
    "1.3.6.1.2.1.43.11.1.1.6"
)

OID_SUPPLY_UNIT = (
    "1.3.6.1.2.1.43.11.1.1.7"
)

OID_SUPPLY_CAPACITY = (
    "1.3.6.1.2.1.43.11.1.1.8"
)

OID_SUPPLY_LEVEL = (
    "1.3.6.1.2.1.43.11.1.1.9"
)


# Tabela adicional usada somente para tentativa
# de localizar identificadores.
OID_MARKER_BASE = (
    "1.3.6.1.2.1.43.5.1.1"
)


# ============================================================
# TIPOS INTERNOS
# ============================================================

TIPO_TONER = "toner"

TIPO_UNIDADE_IMAGEM = "unidade_imagem"

TIPO_FUSOR = "fusor"

TIPO_OUTRO = "outro"

TIPO_DESCONHECIDO = "desconhecido"


# ============================================================
# UTILITÁRIOS
# ============================================================

def limpar_valor(
    valor: Any,
) -> str | None:
    """
    Converte um retorno do pysnmp para texto.
    """

    if valor is None:
        return None

    try:
        texto = valor.prettyPrint()

    except Exception:
        texto = str(valor)

    if texto is None:
        return None

    return str(
        texto
    ).strip()


def inteiro(
    valor: Any,
) -> int | None:
    """
    Converte valor para inteiro sem lançar exceção.
    """

    try:
        return int(
            valor
        )

    except (
        TypeError,
        ValueError,
    ):
        return None


def decodificar_hexadecimal(
    valor: Any,
) -> str | None:
    """
    Algumas Lexmark podem retornar descrições
    em hexadecimal.

    Exemplo:

        0x546f6e657220707265746f

    Retorno:

        Toner preto
    """

    if valor is None:
        return None

    texto = str(
        valor
    ).strip()

    if not texto.lower().startswith(
        "0x"
    ):
        return texto

    bruto = texto[2:]

    if not bruto:
        return texto

    if not re.fullmatch(
        r"[0-9a-fA-F]+",
        bruto,
    ):
        return texto

    if len(bruto) % 2:
        bruto = bruto[:-1]

    try:
        dados = bytes.fromhex(
            bruto
        )

    except ValueError:
        return texto

    chars = []

    for byte in dados:

        if 32 <= byte <= 126:
            chars.append(
                chr(byte)
            )

        else:
            break

    convertido = "".join(
        chars
    ).strip()

    if len(convertido) >= 3:
        return convertido

    return texto


def normalizar_descricao(
    valor: Any,
) -> dict:

    bruto = limpar_valor(
        valor
    )

    if bruto is None:

        return {
            "valor": None,
            "bruto": None,
            "codificado": False,
        }

    convertido = decodificar_hexadecimal(
        bruto
    )

    return {
        "valor": convertido,
        "bruto": bruto,
        "codificado": (
            convertido != bruto
        ),
    }


# ============================================================
# CONSUMÍVEIS
# ============================================================

def identificar_tipo(
    nome: str | None,
) -> str:
    """
    Classifica o consumível.

    Regras:

        Toner
            -> toner

        Unidade de imagem
            -> unidade_imagem

        Fuser / Fusor / Maintenance Kit
            -> fusor
    """

    if not nome:
        return TIPO_DESCONHECIDO

    texto = str(
        nome
    ).strip().lower()

    # --------------------------------------------------------
    # TONER
    # --------------------------------------------------------

    if any(
        termo in texto
        for termo in (
            "toner",
            "cartucho",
            "cartridge",
        )
    ):
        return TIPO_TONER

    # --------------------------------------------------------
    # UNIDADE DE IMAGEM
    # --------------------------------------------------------

    if any(
        termo in texto
        for termo in (
            "unid. imagem",
            "unidade de imagem",
            "image unit",
            "imaging unit",
            "photoconductor",
            "fotocondutor",
            "drum",
        )
    ):
        return TIPO_UNIDADE_IMAGEM

    # --------------------------------------------------------
    # FUSOR
    # --------------------------------------------------------

    if any(
        termo in texto
        for termo in (
            "kit manuten",
            "maintenance kit",
            "maintenance",
            "fuser",
            "fusor",
        )
    ):
        return TIPO_FUSOR

    return TIPO_OUTRO


def nome_exibicao_consumivel(
    nome: str | None,
    tipo: str,
) -> str:

    if tipo == TIPO_TONER:
        return "Toner"

    if tipo == TIPO_UNIDADE_IMAGEM:
        return "Unidade de imagem"

    if tipo == TIPO_FUSOR:
        return "Fusor"

    if nome:
        return str(
            nome
        ).strip()

    return "Consumível"


def calcular_condicao_consumivel(
    percentual: float | None,
) -> str:
    """
    Interpretação do nível:

        > 50%  -> OK
        > 30%  -> ATENÇÃO
        > 15%  -> BAIXO
        <= 15% -> CRÍTICO
    """

    if percentual is None:
        return "DESCONHECIDO"

    if percentual > 50:
        return "OK"

    if percentual > 30:
        return "ATENÇÃO"

    if percentual > 15:
        return "BAIXO"

    return "CRÍTICO"


# Compatibilidade com código antigo.
def calcular_status_supply(
    percentual: float | None,
) -> str:

    return calcular_condicao_consumivel(
        percentual
    )


def calcular_garantia_unidade_imagem(
    percentual: float | None,
) -> bool | None:
    """
    Regra específica da unidade de imagem.

    50% ou mais:
        possível encaminhamento para garantia.

    Esta regra NÃO é aplicada a toner
    nem a fusor.
    """

    if percentual is None:
        return None

    return percentual >= 50


# ============================================================
# SNMP
# ============================================================

class SNMPPrinter:
    """
    Cliente SNMP de uma impressora.
    """

    def __init__(
        self,
        ip: str,
        community: str = COMMUNITY_PADRAO,
        timeout: int = TIMEOUT_PADRAO,
        retries: int = RETRIES_PADRAO,
    ):

        self.ip = ip

        self.community = community

        self.timeout = timeout

        self.retries = retries

        self.versao: str | None = None

        self.modelo_snmp: int | None = None

        # ----------------------------------------------------
        # Dados brutos para diagnóstico.
        # ----------------------------------------------------

        self.raw_supplies: dict[
            str,
            str | None,
        ] = {}

        self.raw_identificadores: dict[
            str,
            str | None,
        ] = {}

    # ========================================================
    # TARGET
    # ========================================================

    async def target(self):

        return await UdpTransportTarget.create(
            (
                self.ip,
                161,
            ),
            timeout=self.timeout,
            retries=self.retries,
        )

    # ========================================================
    # COMMUNITY
    # ========================================================

    def community_data(
        self,
        modelo: int,
    ):

        return CommunityData(
            self.community,
            mpModel=modelo,
        )

    # ========================================================
    # VERSÃO
    # ========================================================

    def marcar_versao(
        self,
        modelo: int,
    ):

        self.modelo_snmp = modelo

        if modelo == SNMP_V2C:

            self.versao = "SNMPv2c"

        else:

            self.versao = "SNMPv1"

    # ========================================================
    # GET
    # ========================================================

    async def get(
        self,
        oid: str,
    ):
        """
        Executa GET usando:

            1. SNMPv2c
            2. SNMPv1
        """

        for modelo in (
            SNMP_V2C,
            SNMP_V1,
        ):

            try:

                engine = SnmpEngine()

                target = await self.target()

                erro_snmp, status, _, binds = (
                    await get_cmd(
                        engine,
                        self.community_data(
                            modelo
                        ),
                        target,
                        ContextData(),
                        ObjectType(
                            ObjectIdentity(
                                oid
                            )
                        ),
                    )
                )

                if erro_snmp:
                    continue

                if status:
                    continue

                for _, valor in binds:

                    texto = limpar_valor(
                        valor
                    )

                    if texto is not None:

                        self.marcar_versao(
                            modelo
                        )

                        return texto

            except Exception as exc:

                print(
                    "[SNMP GET]",
                    exc,
                )

        return None

    # ========================================================
    # WALK
    # ========================================================

    async def walk(
        self,
        oid: str,
    ):
        """
        Executa WALK usando SNMPv2c e SNMPv1.

        Retorna:

            {
                "OID": "valor",
                ...
            }

        O parser das tabelas fica separado do WALK.
        """

        for modelo in (
            SNMP_V2C,
            SNMP_V1,
        ):

            dados: dict[
                str,
                str | None,
            ] = {}

            try:

                engine = SnmpEngine()

                target = await self.target()

                consulta = walk_cmd(
                    engine,
                    self.community_data(
                        modelo
                    ),
                    target,
                    ContextData(),
                    ObjectType(
                        ObjectIdentity(
                            oid
                        )
                    ),
                    lexicographicMode=False,
                    lookupMib=False,
                )

                async for resposta in consulta:

                    erro_snmp, status, _, binds = (
                        resposta
                    )

                    if erro_snmp:

                        print(
                            "[SNMP WALK]",
                            erro_snmp,
                        )

                        break

                    if status:

                        print(
                            "[SNMP WALK STATUS]",
                            status,
                        )

                        break

                    for (
                        oid_resultado,
                        valor,
                    ) in binds:

                        texto_oid = str(
                            oid_resultado
                        )

                        texto_valor = limpar_valor(
                            valor
                        )

                        dados[
                            texto_oid
                        ] = texto_valor

                if dados:

                    self.marcar_versao(
                        modelo
                    )

                    return dados

            except Exception as exc:

                print(
                    "[SNMP WALK]",
                    exc,
                )

        return {}

    # ========================================================
    # IDENTIFICAÇÃO
    # ========================================================

    async def identificacao(
        self,
    ) -> dict:
        """
        Obtém descrição básica da impressora.
        """

        descricao = await self.get(
            OID_SYS_DESCRICAO
        )

        return {
            "ativo": (
                self.versao is not None
                or descricao is not None
            ),
            "descricao": descricao,
        }

    # ========================================================
    # PARSER DO SUPPLIES TABLE
    # ========================================================

    @staticmethod
    def _extrair_coluna_indice(
        oid: str,
        base_oid: str,
    ):
        """
        Extrai:

            coluna
            índice

        de um OID pertencente à tabela.

        Exemplo:

            base:
                1.3.6.1.2.1.43.11.1.1

            OID:
                1.3.6.1.2.1.43.11.1.1.6.1

        Resultado:

            coluna = "6"
            indice = "1"

        Para índices compostos, preservamos todos
        os componentes após a coluna.
        """

        prefixo = (
            base_oid.rstrip(".")
            + "."
        )

        if not oid.startswith(
            prefixo
        ):
            return None, None

        resto = oid[
            len(prefixo):
        ]

        partes = resto.split(
            "."
        )

        if len(partes) < 2:
            return None, None

        coluna = partes[0]

        indice = ".".join(
            partes[1:]
        )

        return coluna, indice

    # ========================================================
    # PRINTER-MIB
    # ========================================================

    async def coletar_tabela_supplies(
        self,
    ):
        """
        Coleta a tabela Printer-MIB de suprimentos.

        Estrutura:

            <base>.<coluna>.<índice>

        Agora o parser usa explicitamente o BASE OID.
        """

        dados = await self.walk(
            OID_SUPPLIES_BASE
        )

        self.raw_supplies = dict(
            dados
        )

        if not dados:
            return {}

        tabela: dict[
            str,
            dict,
        ] = {}

        for oid, valor in dados.items():

            coluna, indice = (
                self._extrair_coluna_indice(
                    oid,
                    OID_SUPPLIES_BASE,
                )
            )

            if (
                coluna is None
                or indice is None
            ):
                continue

            item = tabela.setdefault(
                indice,
                {},
            )

            # ------------------------------------------------
            # DESCRIÇÃO
            # ------------------------------------------------

            if coluna == "6":

                info = normalizar_descricao(
                    valor
                )

                item[
                    "nome"
                ] = info[
                    "valor"
                ]

                item[
                    "nome_bruto"
                ] = info[
                    "bruto"
                ]

                item[
                    "nome_codificado"
                ] = info[
                    "codificado"
                ]

            # ------------------------------------------------
            # UNIDADE
            # ------------------------------------------------

            elif coluna == "7":

                item[
                    "unidade"
                ] = inteiro(
                    valor
                )

            # ------------------------------------------------
            # CAPACIDADE MÁXIMA
            # ------------------------------------------------

            elif coluna == "8":

                item[
                    "capacidade"
                ] = inteiro(
                    valor
                )

            # ------------------------------------------------
            # NÍVEL ATUAL
            # ------------------------------------------------

            elif coluna == "9":

                item[
                    "nivel"
                ] = inteiro(
                    valor
                )

        return tabela

    # ========================================================
    # IDENTIFICADORES
    # ========================================================

    async def coletar_identificadores_supplies(
        self,
    ):
        """
        Tenta encontrar número de série e part number
        em tabelas adicionais.

        O part number permanece somente nos dados internos.

        A estrutura proprietária pode variar entre modelos
        Lexmark. Portanto os dados brutos continuam sendo
        preservados para diagnóstico.
        """

        dados = await self.walk(
            OID_MARKER_BASE
        )

        self.raw_identificadores = dict(
            dados
        )

        resultado: dict[
            str,
            dict,
        ] = {}

        if not dados:
            return resultado

        for oid, valor in dados.items():

            coluna, indice = (
                self._extrair_coluna_indice(
                    oid,
                    OID_MARKER_BASE,
                )
            )

            if (
                coluna is None
                or indice is None
            ):
                continue

            texto = limpar_valor(
                valor
            )

            if not texto:
                continue

            item = resultado.setdefault(
                indice,
                {},
            )

            # ------------------------------------------------
            # Candidata a serial
            # ------------------------------------------------

            if coluna == "16":

                item[
                    "numero_serie"
                ] = texto

            # ------------------------------------------------
            # Candidata a part number
            # ------------------------------------------------

            elif coluna == "17":

                item[
                    "part_number"
                ] = texto

        return resultado

    # ========================================================
    # RELACIONAMENTO DOS IDENTIFICADORES
    # ========================================================

    @staticmethod
    def localizar_identificador(
        identificadores: dict,
        indice: str,
    ) -> dict:
        """
        Tenta relacionar o identificador ao supply.

        Primeiro tenta o índice completo.

        Depois tenta somente o último componente.
        """

        if not identificadores:
            return {}

        if indice in identificadores:

            return identificadores[
                indice
            ]

        ultimo = indice.split(
            "."
        )[-1]

        if ultimo in identificadores:

            return identificadores[
                ultimo
            ]

        return {}

    # ========================================================
    # CALCULAR PERCENTUAL
    # ========================================================

    @staticmethod
    def calcular_percentual(
        nivel: int | float | None,
        capacidade: int | float | None,
    ) -> float | None:
        """
        Converte o valor de prtMarkerSuppliesLevel
        em percentual usando prtMarkerSuppliesMaxCapacity.

        Printer-MIB:

            level
                = nível atual na unidade definida
                  pelo próprio consumível.

            maxCapacity
                = capacidade máxima na mesma unidade.

        Portanto:

            percentual =
                (level / maxCapacity) * 100

        Valores negativos de level são tratados como
        estado especial / desconhecido e NÃO são
        transformados em 0%.

        Se a capacidade for 100 e o nível for 75:

            75 / 100 * 100 = 75%

        Se a capacidade for 1000 e o nível for 500:

            500 / 1000 * 100 = 50%
        """

        if nivel is None:
            return None

        if capacidade is None:
            return None

        try:

            nivel_num = float(
                nivel
            )

            capacidade_num = float(
                capacidade
            )

        except (
            TypeError,
            ValueError,
        ):

            return None

        # ----------------------------------------------------
        # Valores negativos na Printer-MIB podem representar
        # estados especiais e não um percentual real.
        # ----------------------------------------------------

        if nivel_num < 0:
            return None

        if capacidade_num <= 0:
            return None

        percentual = (
            nivel_num
            / capacidade_num
            * 100.0
        )

        return max(
            0.0,
            min(
                100.0,
                percentual,
            ),
        )

    # ========================================================
    # SUPPLIES
    # ========================================================

    async def supplies(
        self,
    ):
        """
        Retorna consumíveis normalizados.
        """

        tabela = (
            await self.coletar_tabela_supplies()
        )

        if not tabela:
            return []

        identificadores = (
            await self.coletar_identificadores_supplies()
        )

        resultado = []

        for indice, item in tabela.items():

            nome_original = item.get(
                "nome"
            )

            if not nome_original:
                continue

            tipo = identificar_tipo(
                nome_original
            )

            nome = nome_exibicao_consumivel(
                nome_original,
                tipo,
            )

            capacidade = item.get(
                "capacidade"
            )

            nivel_raw = item.get(
                "nivel"
            )

            unidade = item.get(
                "unidade"
            )

            percentual = None

            restante = None

            consumido = None

            # ------------------------------------------------
            # NÍVEL
            # ------------------------------------------------

            percentual = (
                self.calcular_percentual(
                    nivel_raw,
                    capacidade,
                )
            )

            # ------------------------------------------------
            # CAPACIDADE / NÍVEL
            # ------------------------------------------------
            #
            # CORREÇÃO:
            #
            # prtMarkerSuppliesLevel NÃO deve ser tratado
            # diretamente como percentual.
            #
            # O percentual é calculado usando:
            #
            #       level / maxCapacity * 100
            #
            # Isso evita que qualquer valor acima de 100
            # seja simplesmente convertido para 100%.
            # ------------------------------------------------

            if (
                nivel_raw is not None
                and capacidade is not None
                and capacidade > 0
                and nivel_raw >= 0
            ):

                try:

                    restante = round(
                        float(
                            nivel_raw
                        )
                    )

                    consumido = max(
                        0,
                        round(
                            float(
                                capacidade
                            )
                            - float(
                                nivel_raw
                            )
                        ),
                    )

                except (
                    TypeError,
                    ValueError,
                ):

                    restante = None

                    consumido = None

            # ------------------------------------------------
            # IDENTIFICADORES
            # ------------------------------------------------

            info_id = (
                self.localizar_identificador(
                    identificadores,
                    indice,
                )
            )

            numero_serie = info_id.get(
                "numero_serie"
            )

            part_number = info_id.get(
                "part_number"
            )

            # ------------------------------------------------
            # RESULTADO
            # ------------------------------------------------

            item_resultado = {

                # Índices internos.
                "indice": indice,

                "supply_index": (
                    indice.split(
                        "."
                    )[-1]
                ),

                # ------------------------------------------------
                # EXIBIÇÃO
                # ------------------------------------------------

                "nome": nome,

                "tipo": tipo,

                # ------------------------------------------------
                # DADOS TÉCNICOS
                # ------------------------------------------------

                "unidade": unidade,

                "capacidade": capacidade,

                "restante": restante,

                "consumido": consumido,

                "nivel": percentual,

                "percentual": percentual,

                # ------------------------------------------------
                # INTERPRETAÇÃO
                # ------------------------------------------------

                "condicao": (
                    calcular_condicao_consumivel(
                        percentual
                    )
                ),

                # ------------------------------------------------
                # INTERNO
                # ------------------------------------------------

                "part_number": part_number,

                # ------------------------------------------------
                # BRUTOS
                # ------------------------------------------------

                "nivel_raw": nivel_raw,

                "nome_original": (
                    nome_original
                ),

                "nome_bruto": (
                    item.get(
                        "nome_bruto"
                    )
                ),

                "nome_codificado": (
                    item.get(
                        "nome_codificado",
                        False,
                    )
                ),
            }

            # ------------------------------------------------
            # SERIAL
            # ------------------------------------------------

            # Regra:
            #
            # toner -> pode ter serial
            # unidade de imagem -> pode ter serial
            # fusor -> NÃO adicionar serial
            #
            if (
                tipo != TIPO_FUSOR
                and numero_serie
            ):

                item_resultado[
                    "numero_serie"
                ] = numero_serie

            # ------------------------------------------------
            # GARANTIA
            # ------------------------------------------------

            # Somente unidade de imagem.
            if tipo == TIPO_UNIDADE_IMAGEM:

                item_resultado[
                    "garantia"
                ] = (
                    calcular_garantia_unidade_imagem(
                        percentual
                    )
                )

            resultado.append(
                item_resultado
            )

        # ----------------------------------------------------
        # ORDENAÇÃO
        # ----------------------------------------------------

        def chave_ordenacao(
            item,
        ):

            try:

                return int(
                    item.get(
                        "supply_index",
                        999999,
                    )
                )

            except (
                TypeError,
                ValueError,
            ):

                return 999999

        resultado.sort(
            key=chave_ordenacao
        )

        return resultado

    # ========================================================
    # COLETA GERAL
    # ========================================================

    async def coletar(
        self,
    ):
        """
        Executa a coleta completa.

        SNMP é considerado ativo se qualquer operação
        SNMP tiver respondido.
        """

        identificacao = (
            await self.identificacao()
        )

        supplies = (
            await self.supplies()
        )

        snmp_ativo = (
            self.versao is not None
            or identificacao[
                "ativo"
            ]
            or bool(
                self.raw_supplies
            )
            or bool(
                self.raw_identificadores
            )
        )

        return {

            "ip": self.ip,

            "snmp": snmp_ativo,

            "versao": self.versao,

            "descricao": identificacao[
                "descricao"
            ],

            "supplies": supplies,

            # Diagnóstico interno.
            "raw_supplies": (
                self.raw_supplies
            ),

            "raw_identificadores": (
                self.raw_identificadores
            ),
        }


# ============================================================
# API COMPATÍVEL
# ============================================================

async def coletar_supplies(
    ip: str,
    community: str = COMMUNITY_PADRAO,
):

    printer = SNMPPrinter(
        ip,
        community,
    )

    return await printer.supplies()


async def coletar_snmp(
    ip: str,
    community: str = COMMUNITY_PADRAO,
):
    """
    API principal do módulo.

    Esta função existe no módulo e é utilizada
    pelo restante do Printer Assistant.
    """

    printer = SNMPPrinter(
        ip,
        community,
    )

    return await printer.coletar()


# ============================================================
# PARSE COMPATÍVEL
# ============================================================

def parse_supplies(
    dados,
):
    """
    Compatibilidade com versões antigas.

    Recebe um dump bruto da Printer-MIB e devolve
    uma lista padronizada.

    A estrutura esperada é:

        <base>.<coluna>.<índice>

    com:

        .6 = descrição
        .7 = unidade
        .8 = capacidade
        .9 = nível
    """

    if not dados:
        return []

    tabela = {}

    for oid, valor in dados.items():

        coluna, indice = (
            SNMPPrinter._extrair_coluna_indice(
                str(oid),
                OID_SUPPLIES_BASE,
            )
        )

        if (
            coluna is None
            or indice is None
        ):
            continue

        item = tabela.setdefault(
            indice,
            {},
        )

        if coluna == "6":

            item[
                "nome"
            ] = valor

        elif coluna == "7":

            item[
                "unidade"
            ] = valor

        elif coluna == "8":

            item[
                "capacidade"
            ] = valor

        elif coluna == "9":

            item[
                "nivel"
            ] = valor

    resultado = []

    for indice, item in tabela.items():

        nome_info = (
            normalizar_descricao(
                item.get("nome")
            )
        )

        nome_original = (
            nome_info.get(
                "valor"
            )
        )

        if not nome_original:
            continue

        tipo = identificar_tipo(
            nome_original
        )

        nome = nome_exibicao_consumivel(
            nome_original,
            tipo,
        )

        capacidade = inteiro(
            item.get(
                "capacidade"
            )
        )

        nivel_raw = inteiro(
            item.get(
                "nivel"
            )
        )

        unidade = inteiro(
            item.get(
                "unidade"
            )
        )

        percentual = (
            SNMPPrinter.calcular_percentual(
                nivel_raw,
                capacidade,
            )
        )

        restante = None

        consumido = None

        # ----------------------------------------------------
        # CORREÇÃO:
        #
        # restante representa o nível bruto na unidade
        # informada pela Printer-MIB.
        #
        # percentual é calculado separadamente:
        #
        #     nivel / capacidade * 100
        # ----------------------------------------------------

        if (
            nivel_raw is not None
            and capacidade is not None
            and capacidade > 0
            and nivel_raw >= 0
        ):

            restante = nivel_raw

            consumido = max(
                0,
                capacidade - nivel_raw,
            )

        supply = {

            "indice": indice,

            "supply_index": (
                indice.split(
                    "."
                )[-1]
            ),

            "nome": nome,

            "nome_original": (
                nome_original
            ),

            "tipo": tipo,

            "unidade": unidade,

            "capacidade": capacidade,

            "restante": restante,

            "consumido": consumido,

            "nivel": percentual,

            "percentual": percentual,

            "condicao": (
                calcular_condicao_consumivel(
                    percentual
                )
            ),

            "numero_serie": None,

            "part_number": None,

            "nivel_raw": nivel_raw,
        }

        if tipo == TIPO_UNIDADE_IMAGEM:

            supply[
                "garantia"
            ] = (
                calcular_garantia_unidade_imagem(
                    percentual
                )
            )

        resultado.append(
            supply
        )

    return resultado


# ============================================================
# TESTE DIRETO
# ============================================================

def imprimir_linha():

    print(
        "=" * 68
    )


def imprimir_consumivel(
    numero: int,
    supply: dict,
):

    print()

    print(
        f"[{numero}] "
        f"{supply.get('nome', 'Consumível')}"
    )

    percentual = supply.get(
        "percentual"
    )

    if percentual is None:

        nivel_texto = "N/D"

    else:

        nivel_texto = (
            f"{percentual:g} %"
        )

    print(
        f"    Nível:       "
        f"{nivel_texto}"
    )

    print(
        f"    Condição:    "
        f"{supply.get('condicao', 'DESCONHECIDO')}"
    )

    print(
        f"    Capacidade:  "
        f"{supply.get('capacidade', 'N/D')}"
    )

    print(
        f"    Restante:    "
        f"{supply.get('restante', 'N/D')}"
    )

    print(
        f"    Consumido:   "
        f"{supply.get('consumido', 'N/D')}"
    )

    # --------------------------------------------------------
    # SERIAL
    # --------------------------------------------------------

    numero_serie = supply.get(
        "numero_serie"
    )

    # Mantemos a saída do teste coerente com a interface:
    # fusor não apresenta número de série.

    if supply.get("tipo") != TIPO_FUSOR:

        print(
            f"    Nº série:    "
            f"{numero_serie if numero_serie else 'N/D'}"
        )

    # --------------------------------------------------------
    # GARANTIA
    # --------------------------------------------------------

    if (
        supply.get("tipo")
        == TIPO_UNIDADE_IMAGEM
    ):

        garantia = supply.get(
            "garantia"
        )

        if garantia is True:

            texto_garantia = (
                "POSSÍVEL"
            )

        elif garantia is False:

            texto_garantia = (
                "NÃO ELEGÍVEL"
            )

        else:

            texto_garantia = "N/D"

        print(
            f"    Garantia:    "
            f"{texto_garantia}"
        )


async def teste():

    imprimir_linha()

    print(
        "PRINTER ASSISTANT - TESTE SNMP"
    )

    imprimir_linha()

    print()

    ip = input(
        "IP da impressora: "
    ).strip()

    if not ip:

        print()

        print(
            "[ERRO] IP não informado."
        )

        return

    print()

    print(
        "Consultando SNMP..."
    )

    print()

    try:

        dados = await coletar_snmp(
            ip
        )

    except Exception as exc:

        print()

        print(
            "[ERRO SNMP]",
            exc,
        )

        return

    print()

    imprimir_linha()

    print(
        "RESULTADO SNMP"
    )

    imprimir_linha()

    print()

    print(
        f"IP:        "
        f"{dados.get('ip')}"
    )

    print(
        "SNMP:      "
        + (
            "ATIVO"
            if dados.get("snmp")
            else "INATIVO"
        )
    )

    print(
        f"Versão:    "
        f"{dados.get('versao') or 'N/D'}"
    )

    descricao = dados.get(
        "descricao"
    )

    print(
        f"Descrição: "
        f"{descricao or 'N/D'}"
    )

    supplies = dados.get(
        "supplies",
        [],
    )

    print()

    imprimir_linha()

    print(
        f"CONSUMÍVEIS ({len(supplies)})"
    )

    imprimir_linha()

    if not supplies:

        print()

        print(
            "Nenhum consumível encontrado."
        )

    for numero, supply in enumerate(
        supplies,
        start=1,
    ):

        imprimir_consumivel(
            numero,
            supply,
        )

    print()

    imprimir_linha()

    print(
        "TESTE CONCLUÍDO"
    )

    imprimir_linha()

    print()


# ============================================================
# START
# ============================================================

if __name__ == "__main__":

    try:

        asyncio.run(
            teste()
        )

    except KeyboardInterrupt:

        print()

        print(
            "Programa encerrado pelo usuário."
        )

        print()