"""
Printer Assistant - SNMP
========================

Coleta informações de impressoras através de SNMP.

Responsabilidades:

- identificar se SNMP está disponível;
- tentar SNMPv2c e depois SNMPv1;
- coletar Printer-MIB;
- identificar consumíveis;
- calcular nível;
- calcular condição;
- identificar toner, unidade de imagem e fusor;
- preservar part number apenas internamente;
- preservar dados brutos para diagnóstico.

O SNMP NÃO é responsável por:

- serial da impressora;
- serial de toner;
- serial de unidade de imagem;
- serial de fusor.

Esses dados pertencem ao SYSDEBUG.

Compatível com:

- Python 3.x
- pysnmp 7.x
- SNMPv1
- SNMPv2c
"""

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


# ------------------------------------------------------------
# Printer-MIB
# prtMarkerSuppliesTable
# ------------------------------------------------------------

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


# ------------------------------------------------------------
# Marker table
#
# Usado somente para diagnóstico / identificadores internos.
#
# IMPORTANTE:
#
# O .16 NÃO é serial de consumível.
# O .17 NÃO é serial de consumível.
#
# Não expor esses valores como numero_serie.
# ------------------------------------------------------------

OID_MARKER_BASE = (
    "1.3.6.1.2.1.43.5.1.1"
)


# ============================================================
# TIPOS INTERNOS
# ============================================================

TIPO_TONER = "toner"

TIPO_UNIDADE_IMAGEM = (
    "unidade_imagem"
)

TIPO_FUSOR = "fusor"

TIPO_OUTRO = "outro"

TIPO_DESCONHECIDO = (
    "desconhecido"
)


# ============================================================
# UTILITÁRIOS
# ============================================================

def limpar_valor(
    valor: Any,
) -> str | None:
    """
    Converte retorno do pysnmp para texto limpo.
    """

    if valor is None:
        return None

    try:
        texto = valor.prettyPrint()

    except Exception:
        texto = str(valor)

    if texto is None:
        return None

    texto = str(texto).strip()

    if not texto:
        return None

    return texto


def inteiro(
    valor: Any,
) -> int | None:
    """
    Converte valor para inteiro sem lançar exceção.
    """

    if valor is None:
        return None

    try:
        return int(valor)

    except (TypeError, ValueError):
        pass

    texto = limpar_valor(valor)

    if texto is None:
        return None

    try:
        return int(texto)

    except (TypeError, ValueError):
        return None


def decodificar_hexadecimal(
    valor: Any,
) -> str | None:
    """
    Algumas impressoras retornam descrições em hexadecimal.

    Exemplo:

        0x546f6e657220707265746f

    vira:

        Toner preto

    Só converte quando o resultado é texto ASCII legível.
    """

    if valor is None:
        return None

    texto = str(valor).strip()

    if not texto.lower().startswith("0x"):
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

    if not bruto:
        return texto

    try:
        dados = bytes.fromhex(bruto)

    except ValueError:
        return texto

    chars = []

    for byte in dados:

        if 32 <= byte <= 126:
            chars.append(chr(byte))

        else:
            break

    convertido = "".join(chars).strip()

    if len(convertido) >= 3:
        return convertido

    return texto


def normalizar_descricao(
    valor: Any,
) -> dict:
    """
    Normaliza descrição de supply.

    O bruto continua disponível para diagnóstico.
    """

    bruto = limpar_valor(valor)

    if bruto is None:
        return {
            "valor": None,
            "bruto": None,
            "codificado": False,
        }

    convertido = (
        decodificar_hexadecimal(
            bruto
        )
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
    """

    if not nome:
        return TIPO_DESCONHECIDO

    texto = (
        str(nome)
        .strip()
        .lower()
    )

    # Toner
    if any(
        termo in texto
        for termo in (
            "toner",
            "cartucho",
            "cartridge",
        )
    ):
        return TIPO_TONER

    # Unidade de imagem
    if any(
        termo in texto
        for termo in (
            "unid. imagem",
            "unidade de imagem",
            "image unit",
            "imaging unit",
            "imagem",
            "imaging",
            "photoconductor",
            "fotocondutor",
            "drum",
        )
    ):
        return TIPO_UNIDADE_IMAGEM

    # Fusor
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
    """
    Nome simplificado para a interface.
    """

    if tipo == TIPO_TONER:
        return "Toner"

    if tipo == TIPO_UNIDADE_IMAGEM:
        return "Unidade de imagem"

    if tipo == TIPO_FUSOR:
        return "Fusor"

    if nome:
        return str(nome).strip()

    return "Consumível"


def calcular_condicao_consumivel(
    percentual: float | None,
) -> str:
    """
    Interpreta o nível do consumível.

    > 50%   = OK
    > 30%   = ATENÇÃO
    > 15%   = BAIXO
    <= 15%  = CRÍTICO
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


def calcular_status_supply(
    percentual: float | None,
) -> str:
    """
    Compatibilidade com versões antigas.
    """

    return calcular_condicao_consumivel(
        percentual
    )


def calcular_garantia_unidade_imagem(
    percentual: float | None,
) -> bool | None:
    """
    Regra exclusiva da unidade de imagem.

    >= 50%:
        possível garantia.

    IMPORTANTE:
    não aplicar ao toner ou fusor.
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

    Não conhece SYSDEBUG.

    Não atribui serial de consumível.
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

        # Dados brutos.
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
        """
        Cria alvo UDP do pysnmp.
        """

        return await UdpTransportTarget.create(
            (self.ip, 161),
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
        """
        Cria CommunityData para SNMPv1/v2c.
        """

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

        self.versao = (
            "SNMPv2c"
            if modelo == SNMP_V2C
            else "SNMPv1"
        )


    # ========================================================
    # GET
    # ========================================================

    async def get(
        self,
        oid: str,
    ):
        """
        Tenta:

        1. SNMPv2c
        2. SNMPv1
        """

        for modelo in (
            SNMP_V2C,
            SNMP_V1,
        ):

            try:

                engine = SnmpEngine()

                target = (
                    await self.target()
                )

                (
                    erro_snmp,
                    status,
                    _,
                    binds,
                ) = await get_cmd(

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

                continue

        return None


    # ========================================================
    # WALK
    # ========================================================

    async def walk(
        self,
        oid: str,
    ):
        """
        Executa WALK usando:

        1. SNMPv2c
        2. SNMPv1
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

                target = (
                    await self.target()
                )

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

                    (
                        erro_snmp,
                        status,
                        _,
                        binds,
                    ) = resposta

                    if erro_snmp:

                        print(
                            "[SNMP WALK]",
                            erro_snmp,
                        )

                        break

                    if status:

                        print(
                            "[SNMP WALK]",
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

                        texto_valor = (
                            limpar_valor(
                                valor
                            )
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
    # PRINTER-MIB
    # ========================================================

    async def coletar_tabela_supplies(
        self,
    ):
        """
        Coleta prtMarkerSuppliesTable.
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

        prefixo = (
            OID_SUPPLIES_BASE
            + "."
        )

        for oid, valor in dados.items():

            oid_texto = str(oid)

            if not oid_texto.startswith(
                prefixo
            ):
                continue

            restante_oid = (
                oid_texto[
                    len(prefixo):
                ]
            )

            partes = (
                restante_oid.split(".")
            )

            if len(partes) < 2:
                continue

            coluna = partes[0]

            indice = ".".join(
                partes[1:]
            )

            item = tabela.setdefault(
                indice,
                {},
            )

            if coluna == "6":

                info = (
                    normalizar_descricao(
                        valor
                    )
                )

                item["nome"] = (
                    info["valor"]
                )

                item["nome_bruto"] = (
                    info["bruto"]
                )

                item[
                    "nome_codificado"
                ] = info[
                    "codificado"
                ]

            elif coluna == "7":

                item["unidade"] = (
                    inteiro(valor)
                )

            elif coluna == "8":

                item["capacidade"] = (
                    inteiro(valor)
                )

            elif coluna == "9":

                item["restante"] = (
                    inteiro(valor)
                )

        return tabela


    # ========================================================
    # IDENTIFICADORES
    # ========================================================

    async def coletar_identificadores_supplies(
        self,
    ):
        """
        Coleta dados da marker table apenas para diagnóstico.

        NÃO transforma .16/.17 em serial de consumível.
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

        prefixo = (
            OID_MARKER_BASE
            + "."
        )

        for oid, valor in dados.items():

            oid_texto = str(oid)

            if not oid_texto.startswith(
                prefixo
            ):
                continue

            restante_oid = (
                oid_texto[
                    len(prefixo):
                ]
            )

            partes = (
                restante_oid.split(".")
            )

            if len(partes) < 2:
                continue

            coluna = partes[0]

            indice = ".".join(
                partes[1:]
            )

            texto = limpar_valor(
                valor
            )

            if not texto:
                continue

            item = resultado.setdefault(
                indice,
                {},
            )

            # Estes dados são internos.
            if coluna == "16":

                item[
                    "marker_identifier"
                ] = texto

            elif coluna == "17":

                item[
                    "part_number"
                ] = texto

        return resultado


    # ========================================================
    # SUPPLIES
    # ========================================================

    async def supplies(
        self,
    ):
        """
        Retorna somente dados normalizados
        de consumíveis.

        Serial não pertence ao SNMP.
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

            nome = (
                nome_exibicao_consumivel(
                    nome_original,
                    tipo,
                )
            )

            capacidade = item.get(
                "capacidade"
            )

            restante = item.get(
                "restante"
            )

            unidade = item.get(
                "unidade"
            )

            nivel = None

            consumido = None

            if (
                capacidade is not None
                and capacidade > 0
                and restante is not None
            ):

                nivel = round(
                    (
                        restante
                        / capacidade
                    ) * 100,
                    1,
                )

                nivel = max(
                    0,
                    min(
                        100,
                        nivel,
                    ),
                )

                consumido = (
                    capacidade
                    - restante
                )

            info_id = (
                identificadores.get(
                    indice,
                    {}
                )
            )

            part_number = (
                info_id.get(
                    "part_number"
                )
            )

            # ------------------------------------------------
            # Modelo público limpo
            # ------------------------------------------------

            item_resultado = {

                "indice": indice,

                "tipo": tipo,

                "nome": nome,

                "unidade": unidade,

                "capacidade": capacidade,

                "restante": restante,

                "consumido": consumido,

                "nivel": nivel,

                "condicao": (
                    calcular_condicao_consumivel(
                        nivel
                    )
                ),

            }

            # ------------------------------------------------
            # Garantia:
            # SOMENTE unidade de imagem.
            # ------------------------------------------------

            if (
                tipo
                == TIPO_UNIDADE_IMAGEM
            ):

                item_resultado[
                    "garantia"
                ] = (
                    calcular_garantia_unidade_imagem(
                        nivel
                    )
                )

            # ------------------------------------------------
            # Dados internos.
            #
            # Não entram no modelo público.
            # ------------------------------------------------

            item_resultado[
                "_interno"
            ] = {

                "supply_index":
                    indice.split(
                        "."
                    )[-1],

                "part_number":
                    part_number,

                "marker_identifier":
                    info_id.get(
                        "marker_identifier"
                    ),

                "nome_original":
                    nome_original,

                "nome_bruto":
                    item.get(
                        "nome_bruto"
                    ),

                "nome_codificado":
                    item.get(
                        "nome_codificado",
                        False,
                    ),
            }

            resultado.append(
                item_resultado
            )

        # ----------------------------------------------------
        # Ordenação
        # ----------------------------------------------------

        def chave_ordenacao(
            item
        ):

            try:

                return int(
                    item.get(
                        "_interno",
                        {}
                    ).get(
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
        Coleta dados SNMP.

        Retorno público limpo.
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

        # Não expor marker identifiers
        # nem part numbers.
        supplies_publicos = []

        for supply in supplies:

            item = {
                chave: valor
                for chave, valor
                in supply.items()
                if chave != "_interno"
            }

            supplies_publicos.append(
                item
            )

        return {

            "snmp": snmp_ativo,

            "versao": self.versao,

            "descricao": (
                identificacao[
                    "descricao"
                ]
            ),

            "supplies":
                supplies_publicos,
        }

    # ========================================================
    # DIAGNÓSTICO
    # ========================================================

    def diagnostico(
        self,
    ) -> dict:
        """
        Retorna dados brutos do SNMP.

        Nunca deve ser usado diretamente pela UI normal.
        """

        return {

            "versao":
                self.versao,

            "modelo_snmp":
                self.modelo_snmp,

            "raw_supplies":
                dict(
                    self.raw_supplies
                ),

            "raw_identificadores":
                dict(
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
    """
    API compatível com versões anteriores.

    Retorna somente supplies públicos.
    """

    printer = SNMPPrinter(
        ip=ip,
        community=community,
    )

    return await printer.supplies()


async def coletar_snmp(
    ip: str,
    community: str = COMMUNITY_PADRAO,
):
    """
    API principal do módulo.
    """

    printer = SNMPPrinter(
        ip=ip,
        community=community,
    )

    return await printer.coletar()


# ============================================================
# COMPATIBILIDADE ANTIGA
# ============================================================

def parse_supplies(
    dados,
):
    """
    Compatibilidade com versões antigas.

    Recebe dump bruto da Printer-MIB e devolve
    uma lista padronizada sem duplicação.
    """

    if not dados:
        return []

    tabela = {}

    prefixo = (
        OID_SUPPLIES_BASE
        + "."
    )

    for oid, valor in dados.items():

        oid_texto = str(oid)

        if not oid_texto.startswith(
            prefixo
        ):
            continue

        restante_oid = (
            oid_texto[
                len(prefixo):
            ]
        )

        partes = (
            restante_oid.split(".")
        )

        if len(partes) < 2:
            continue

        coluna = partes[0]

        indice = ".".join(
            partes[1:]
        )

        item = tabela.setdefault(
            indice,
            {},
        )

        if coluna == "6":

            item["nome"] = valor

        elif coluna == "7":

            item["unidade"] = valor

        elif coluna == "8":

            item["capacidade"] = valor

        elif coluna == "9":

            item["restante"] = valor

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

        nome = (
            nome_exibicao_consumivel(
                nome_original,
                tipo,
            )
        )

        capacidade = inteiro(
            item.get(
                "capacidade"
            )
        )

        restante = inteiro(
            item.get(
                "restante"
            )
        )

        unidade = inteiro(
            item.get(
                "unidade"
            )
        )

        nivel = None

        consumido = None

        if (
            capacidade is not None
            and capacidade > 0
            and restante is not None
        ):

            nivel = round(
                (
                    restante
                    / capacidade
                ) * 100,
                1,
            )

            nivel = max(
                0,
                min(
                    100,
                    nivel,
                ),
            )

            consumido = (
                capacidade
                - restante
            )

        supply = {

            "indice":
                indice,

            "tipo":
                tipo,

            "nome":
                nome,

            "unidade":
                unidade,

            "capacidade":
                capacidade,

            "restante":
                restante,

            "consumido":
                consumido,

            "nivel":
                nivel,

            "condicao":
                calcular_condicao_consumivel(
                    nivel
                ),
        }

        if (
            tipo
            == TIPO_UNIDADE_IMAGEM
        ):

            supply[
                "garantia"
            ] = (
                calcular_garantia_unidade_imagem(
                    nivel
                )
            )

        resultado.append(
            supply
        )

    return resultado


# ============================================================
# TESTE DIRETO
# ============================================================

async def teste():

    print()

    print("=" * 68)

    print(
        "PRINTER ASSISTANT - TESTE SNMP"
    )

    print("=" * 68)

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

    print("=" * 68)

    print(
        "RESULTADO SNMP"
    )

    print("=" * 68)

    print()

    print(
        "SNMP:",
        (
            "ATIVO"
            if dados.get("snmp")
            else "INATIVO"
        )
    )

    print(
        "Versão:",
        dados.get(
            "versao"
        )
        or "N/D"
    )

    print(
        "Descrição:",
        dados.get(
            "descricao"
        )
        or "N/D"
    )

    supplies = dados.get(
        "supplies",
        [],
    )

    print()

    print(
        f"Consumíveis: {len(supplies)}"
    )

    for numero, supply in enumerate(
        supplies,
        start=1,
    ):

        print()

        print(
            f"[{numero}] "
            f"{supply.get('nome', 'Consumível')}"
        )

        print(
            "    Tipo:",
            supply.get(
                "tipo",
                "N/D"
            )
        )

        print(
            "    Nível:",
            (
                f"{supply.get('nivel')}%"
                if supply.get("nivel")
                is not None
                else "N/D"
            )
        )

        print(
            "    Condição:",
            supply.get(
                "condicao",
                "N/D"
            )
        )

        print(
            "    Capacidade:",
            supply.get(
                "capacidade",
                "N/D"
            )
        )

        print(
            "    Restante:",
            supply.get(
                "restante",
                "N/D"
            )
        )

        print(
            "    Consumido:",
            supply.get(
                "consumido",
                "N/D"
            )
        )

        if (
            supply.get("tipo")
            == TIPO_UNIDADE_IMAGEM
        ):

            garantia = supply.get(
                "garantia"
            )

            if garantia is True:
                texto = "POSSÍVEL"

            elif garantia is False:
                texto = "NÃO ELEGÍVEL"

            else:
                texto = "N/D"

            print(
                "    Garantia:",
                texto
            )

    print()

    print("=" * 68)

    print(
        "TESTE CONCLUÍDO"
    )

    print("=" * 68)

    print()


if __name__ == "__main__":

    import asyncio

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