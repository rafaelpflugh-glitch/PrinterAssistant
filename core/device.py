
"""
Printer Assistant - Device

Representa uma impressora física.

O Device NÃO implementa protocolos.
Ele coordena:

    PJL
    SYSDEBUG
    SNMP

Responsabilidades
-----------------

PJL
    - identificação auxiliar
    - contador auxiliar

SYSDEBUG
    - serial da máquina
    - contador oficial
    - firmware
    - seriais de consumíveis quando disponíveis

SNMP
    - suprimentos
    - nível
    - capacidade
    - restante
    - consumido
    - condição

Regras importantes
------------------

1. SYSDEBUG possui prioridade para contador.

2. PJL pode fornecer contador auxiliar quando SYSDEBUG
   não estiver disponível.

3. SNMP NÃO fornece serial confiável de consumível.

4. O Device pode relacionar:
       SNMP supply
       +
       SYSDEBUG supply
   para completar o número de série.

5. Fusor não possui necessariamente número de série.
   Para o modelo de laboratório atual, o fusor deve ser
   apresentado como "NÃO APLICÁVEL".

6. Valores como "Speed: 0" NÃO são considerados modelo.

7. O Device não deve ficar preso a Lexmark.
   A MX611dhe é apenas a máquina de laboratório atual.
   Epson, Brother, Canon, HP etc. poderão ser adicionadas
   posteriormente.
"""

import asyncio


from core.pjl import coletar_identificacao
from core.snmp import coletar_supplies
from core.sysdebug import coletar_sysdebug


# ============================================================
# CONFIGURAÇÃO
# ============================================================

TIMEOUT_PJL = 15
TIMEOUT_SYSDEBUG = 15
TIMEOUT_SNMP = 45


# ============================================================
# CLASSE
# ============================================================

class PrinterDevice:

    def __init__(
        self,
        ip,
        nome=None,
    ):

        self.ip = ip
        self.nome = nome

        self.identificacao = {
            "fabricante": "Desconhecido",
            "modelo": "Desconhecido",
            "familia": "",
            "tipo": "",
            "serial": "Desconhecido",
            "firmware": "Desconhecido",
            "contador": None,
        }

        self.supplies = []

        self.conectividade = {
            "ip": ip,
            "pjl": False,
            "sysdebug": False,
            "snmp": False,
            "web": False,
            "raw": False,
            "ipp": False,
        }

        self.origem_contador = None

        self.raw_sysdebug = {}


    # ========================================================
    # FABRICANTE
    # ========================================================

    @staticmethod
    def detectar_fabricante(
        modelo,
    ):

        texto = str(
            modelo or ""
        ).lower()

        if "lexmark" in texto:
            return "Lexmark"

        if "epson" in texto:
            return "Epson"

        if "brother" in texto:
            return "Brother"

        if "canon" in texto:
            return "Canon"

        if (
            "hp" in texto
            or "hewlett" in texto
        ):
            return "HP"

        return "Desconhecido"


    # ========================================================
    # VALIDAR MODELO
    # ========================================================

    @staticmethod
    def modelo_valido(
        modelo,
    ):
        """
        Verifica se determinado valor pode ser utilizado
        como modelo da impressora.

        Evita valores absurdos encontrados em relatórios,
        como:

            Speed: 0
            Speed
            0
            N/D
            Desconhecido
        """

        if modelo is None:
            return False

        texto = str(
            modelo
        ).strip()

        if not texto:
            return False

        normalizado = texto.lower()

        valores_invalidos = (
            "",
            "speed",
            "speed: 0",
            "speed 0",
            "0",
            "n/d",
            "nd",
            "desconhecido",
            "unknown",
            "none",
            "null",
        )

        if normalizado in valores_invalidos:
            return False

        if normalizado.startswith(
            "speed:"
        ):
            return False

        if normalizado.startswith(
            "speed "
        ):
            return False

        return True


    # ========================================================
    # FAMÍLIA
    # ========================================================

    @staticmethod
    def detectar_familia(
        modelo,
    ):

        if not modelo:
            return ""

        texto = str(
            modelo
        ).strip()

        partes = texto.split()

        if not partes:
            return ""

        # Lexmark MX611dhe -> MX
        if (
            partes[0].lower()
            == "lexmark"
            and len(partes) > 1
        ):

            candidato = (
                partes[1]
                .upper()
            )

        else:

            candidato = (
                partes[0]
                .upper()
            )

        familias = (
            "MX",
            "MS",
            "CX",
            "CS",
            "XM",
        )

        for familia in familias:

            if candidato.startswith(
                familia
            ):

                return familia

        return candidato


    # ========================================================
    # TIPO
    # ========================================================

    @staticmethod
    def detectar_tipo(
        fabricante,
        modelo,
    ):

        texto = str(
            modelo or ""
        ).lower()

        if fabricante == "Lexmark":

            if "mx" in texto:
                return (
                    "Multifuncional Laser Mono"
                )

            if "ms" in texto:
                return (
                    "Impressora Laser Mono"
                )

            if "cx" in texto:
                return (
                    "Multifuncional Laser Color"
                )

            if "cs" in texto:
                return (
                    "Impressora Laser Color"
                )

            return "Impressora Lexmark"

        if fabricante == "Epson":
            return "Impressora Epson"

        if fabricante == "Brother":
            return "Impressora Brother"

        if fabricante == "Canon":
            return "Impressora Canon"

        if fabricante == "HP":
            return "Impressora HP"

        return "Equipamento de impressão"


    # ========================================================
    # NORMALIZAR IDENTIFICAÇÃO
    # ========================================================

    def normalizar_identificacao(
        self,
        dados,
        origem=None,
    ):

        if not isinstance(
            dados,
            dict,
        ):
            return

        if origem is None:

            origem = dados.get(
                "origem"
            )


        # ----------------------------------------------------
        # MODELO
        # ----------------------------------------------------

        modelo_novo = dados.get(
            "modelo"
        )

        modelo_atual = (
            self.identificacao.get(
                "modelo"
            )
        )

        # Speed: 0 não é modelo.
        if not self.modelo_valido(
            modelo_novo
        ):

            modelo_novo = None

        # Se o novo modelo é válido,
        # utilizamos somente se não houver
        # um modelo confiável previamente identificado.
        #
        # Isso evita que um SYSDEBUG inconsistente
        # substitua o MX611dhe identificado pelo PJL.

        if modelo_novo:

            if not self.modelo_valido(
                modelo_atual
            ):

                modelo_atual = None

            if modelo_atual:

                # Se já temos um modelo real,
                # preservamos o modelo existente.
                modelo_final = modelo_atual

            else:

                modelo_final = (
                    str(
                        modelo_novo
                    ).strip()
                )

        else:

            if self.modelo_valido(
                modelo_atual
            ):

                modelo_final = (
                    modelo_atual
                )

            else:

                modelo_final = (
                    "Desconhecido"
                )


        # ----------------------------------------------------
        # SERIAL DA MÁQUINA
        # ----------------------------------------------------

        serial_novo = dados.get(
            "serial"
        )

        serial_atual = (
            self.identificacao.get(
                "serial"
            )
        )

        if serial_novo:

            serial_novo = str(
                serial_novo
            ).strip()

        if (
            not serial_novo
            and serial_atual
        ):

            serial_novo = serial_atual

        if not serial_novo:

            serial_novo = (
                "Desconhecido"
            )


        # ----------------------------------------------------
        # FIRMWARE
        # ----------------------------------------------------

        firmware_novo = dados.get(
            "firmware"
        )

        firmware_atual = (
            self.identificacao.get(
                "firmware"
            )
        )

        if firmware_novo:

            firmware_novo = str(
                firmware_novo
            ).strip()

        elif firmware_atual:

            firmware_novo = (
                firmware_atual
            )

        else:

            firmware_novo = (
                "Desconhecido"
            )


        # ----------------------------------------------------
        # CONTADOR
        # ----------------------------------------------------

        contador_novo = dados.get(
            "contador"
        )

        contador_atual = (
            self.identificacao.get(
                "contador"
            )
        )

        # SYSDEBUG possui prioridade absoluta.
        if (
            contador_novo is not None
            and origem == "SYSDEBUG"
        ):

            self.origem_contador = (
                "SYSDEBUG"
            )

        elif (
            contador_novo is not None
        ):

            # PJL somente assume se ainda não
            # houver contador oficial do SYSDEBUG.

            if (
                self.origem_contador
                != "SYSDEBUG"
            ):

                self.origem_contador = (
                    origem
                )

        else:

            contador_novo = (
                contador_atual
            )


        # ----------------------------------------------------
        # FABRICANTE
        # ----------------------------------------------------

        fabricante = (
            dados.get(
                "fabricante"
            )
        )

        if not fabricante:

            fabricante = (
                self.detectar_fabricante(
                    modelo_final
                )
            )

        if (
            not fabricante
            or
            fabricante == "Desconhecido"
        ):

            fabricante = (
                self.detectar_fabricante(
                    modelo_final
                )
            )


        # ----------------------------------------------------
        # FAMÍLIA
        # ----------------------------------------------------

        familia = (
            self.detectar_familia(
                modelo_final
            )
        )


        # ----------------------------------------------------
        # TIPO
        # ----------------------------------------------------

        tipo = (
            self.detectar_tipo(
                fabricante,
                modelo_final,
            )
        )


        # ----------------------------------------------------
        # RESULTADO
        # ----------------------------------------------------

        self.identificacao = {

            "fabricante":
                fabricante,

            "modelo":
                modelo_final,

            "familia":
                familia,

            "tipo":
                tipo,

            "serial":
                serial_novo,

            "firmware":
                firmware_novo,

            "contador":
                contador_novo,
        }


    # ========================================================
    # SYSDEBUG
    # ========================================================

    def coletar_sysdebug_sync(
        self,
    ):

        try:

            dados = coletar_sysdebug(
                self.ip
            )

            if not dados:

                return {}


            if isinstance(
                dados,
                dict,
            ):

                self.raw_sysdebug = (
                    dados.copy()
                )

                self.normalizar_identificacao(
                    dados,
                    "SYSDEBUG",
                )

                self.conectividade[
                    "sysdebug"
                ] = True

                self.conectividade[
                    "web"
                ] = True


            return dados


        except Exception as erro:

            print(
                f"[DEVICE] Erro SYSDEBUG: {erro}"
            )

            return {}


    # ========================================================
    # PJL
    # ========================================================

    def coletar_pjl(
        self,
    ):

        try:

            dados = coletar_identificacao(
                self.ip
            )

            if not dados:

                return {}


            if isinstance(
                dados,
                dict,
            ):

                self.normalizar_identificacao(
                    dados,
                    "PJL",
                )

                respondeu = bool(

                    dados.get(
                        "modelo"
                    )

                    or

                    dados.get(
                        "serial"
                    )

                    or

                    dados.get(
                        "contador"
                    )
                )


            else:

                respondeu = False


            if respondeu:

                self.conectividade[
                    "pjl"
                ] = True

                self.conectividade[
                    "raw"
                ] = True


            return dados


        except Exception as erro:

            print(
                f"[DEVICE] Erro PJL: {erro}"
            )

            return {}


    # ========================================================
    # TIPO CONSUMÍVEL
    # ========================================================

    @staticmethod
    def tipo_consumivel(
        supply,
    ):

        if not isinstance(
            supply,
            dict,
        ):

            return ""


        tipo = supply.get(
            "tipo"
        )

        if tipo:

            return str(
                tipo
            ).strip().lower()


        nome = (

            supply.get(
                "nome"
            )

            or

            supply.get(
                "name"
            )

            or

            supply.get(
                "descricao"
            )

            or

            supply.get(
                "description"
            )

            or

            ""
        )


        texto = str(
            nome
        ).lower()


        if (
            "toner" in texto
            or
            "cartucho" in texto
            or
            "cartridge" in texto
        ):

            return "toner"


        if (
            "imagem" in texto
            or
            "imaging" in texto
            or
            "photoconductor" in texto
            or
            "fotocondutor" in texto
            or
            "drum" in texto
        ):

            return "unidade_imagem"


        if (
            "fusor" in texto
            or
            "fuser" in texto
            or
            "maintenance" in texto
            or
            "manuten" in texto
        ):

            return "fusor"


        return ""


    # ========================================================
    # NORMALIZAR TEXTO
    # ========================================================

    @staticmethod
    def normalizar_texto(
        valor,
    ):

        if valor is None:

            return ""


        texto = str(
            valor
        ).strip().lower()


        substituicoes = {

            "á": "a",
            "à": "a",
            "ã": "a",
            "â": "a",

            "é": "e",
            "ê": "e",

            "í": "i",

            "ó": "o",
            "ô": "o",
            "õ": "o",

            "ú": "u",

            "ç": "c",

            ".": " ",
            "-": " ",
            "_": " ",
        }


        for antigo, novo in (
            substituicoes.items()
        ):

            texto = texto.replace(
                antigo,
                novo,
            )


        return " ".join(
            texto.split()
        )


    # ========================================================
    # EXTRAIR SUPPLIES SYSDEBUG
    # ========================================================

    @classmethod
    def extrair_supplies_sysdebug(
        cls,
        dados,
    ):

        encontrados = []


        def percorrer(
            objeto,
        ):

            if isinstance(
                objeto,
                dict,
            ):

                chaves = {

                    cls.normalizar_texto(
                        chave
                    )

                    for chave
                    in objeto.keys()
                }


                possui_identificacao = bool(

                    {
                        "nome",
                        "name",
                        "descricao",
                        "description",
                        "tipo",
                        "type",
                    }

                    &

                    chaves
                )


                possui_serial = bool(

                    {
                        "serial",
                        "numero serie",
                        "serial number",
                        "serial_number",
                    }

                    &

                    chaves
                )


                if (
                    possui_identificacao
                    or
                    possui_serial
                ):

                    encontrados.append(
                        objeto
                    )


                for valor in objeto.values():

                    percorrer(
                        valor
                    )


            elif isinstance(
                objeto,
                list,
            ):

                for item in objeto:

                    percorrer(
                        item
                    )


        percorrer(
            dados
        )


        return encontrados


    # ========================================================
    # EXTRAIR SERIAL SUPPLY
    # ========================================================

    @staticmethod
    def extrair_serial_supply(
        supply,
    ):

        if not isinstance(
            supply,
            dict,
        ):

            return None


        possiveis = (

            "numero_serie",
            "numero série",
            "serial",
            "serial_number",
            "serial number",
            "supply_serial",
            "consumable_serial",
        )


        for chave in possiveis:

            valor = supply.get(
                chave
            )

            if valor:

                texto = str(
                    valor
                ).strip()

                if texto:

                    return texto


        return None


    # ========================================================
    # ASSOCIAR SERIAIS SYSDEBUG -> SNMP
    # ========================================================

    def associar_seriais_sysdebug(
        self,
        dados_sysdebug,
    ):

        if not dados_sysdebug:

            return


        candidatos_brutos = (
            self.extrair_supplies_sysdebug(
                dados_sysdebug
            )
        )


        if not candidatos_brutos:

            return


        candidatos = []


        for item in candidatos_brutos:

            serial = (
                self.extrair_serial_supply(
                    item
                )
            )


            if not serial:

                continue


            tipo = (
                self.tipo_consumivel(
                    item
                )
            )


            nome = ""


            if isinstance(
                item,
                dict,
            ):

                nome = (

                    item.get(
                        "nome"
                    )

                    or

                    item.get(
                        "name"
                    )

                    or

                    item.get(
                        "descricao"
                    )

                    or

                    item.get(
                        "description"
                    )

                    or

                    ""
                )


            candidatos.append(
                {
                    "serial": serial,
                    "tipo": tipo,
                    "nome":
                        self.normalizar_texto(
                            nome
                        ),
                }
            )


        if not candidatos:

            return


        usados = set()


        for supply in self.supplies:

            tipo_supply = (
                self.tipo_consumivel(
                    supply
                )
            )


            # Fusor não deve receber serial.
            if tipo_supply == "fusor":

                supply[
                    "numero_serie"
                ] = None

                continue


            nome_supply = (
                self.normalizar_texto(
                    supply.get(
                        "nome"
                    )
                )
            )


            escolhido = None


            # ------------------------------------------------
            # 1. TIPO
            # ------------------------------------------------

            for numero, candidato in enumerate(
                candidatos
            ):

                if numero in usados:

                    continue


                if (

                    tipo_supply

                    and

                    candidato[
                        "tipo"
                    ]

                    and

                    tipo_supply
                    ==
                    candidato[
                        "tipo"
                    ]
                ):

                    escolhido = (
                        numero,
                        candidato,
                    )

                    break


            # ------------------------------------------------
            # 2. NOME
            # ------------------------------------------------

            if escolhido is None:

                for numero, candidato in enumerate(
                    candidatos
                ):

                    if numero in usados:

                        continue


                    nome_candidato = (
                        candidato[
                            "nome"
                        ]
                    )


                    if not nome_candidato:

                        continue


                    if (

                        nome_candidato
                        in nome_supply

                        or

                        nome_supply
                        in nome_candidato
                    ):

                        escolhido = (
                            numero,
                            candidato,
                        )

                        break


            if escolhido is None:

                continue


            numero, candidato = (
                escolhido
            )


            supply[
                "numero_serie"
            ] = candidato[
                "serial"
            ]


            usados.add(
                numero
            )


    # ========================================================
    # SNMP
    # ========================================================

    async def coletar_snmp(
        self,
    ):

        print(
            "[DEVICE] Consultando suprimentos via SNMP..."
        )


        try:

            dados = await asyncio.wait_for(

                coletar_supplies(
                    self.ip
                ),

                timeout=TIMEOUT_SNMP,
            )


        except asyncio.TimeoutError:

            print(
                "[DEVICE] SNMP excedeu timeout."
            )

            return self.supplies


        except Exception as erro:

            print(
                f"[DEVICE] Erro SNMP: {erro}"
            )

            return self.supplies


        if not dados:

            print(
                "[DEVICE] SNMP não retornou suprimentos."
            )

            return self.supplies


        self.supplies = []


        for supply in dados:

            if not isinstance(
                supply,
                dict,
            ):

                continue


            supply = supply.copy()


            # Serial de consumível não vem do SNMP.
            supply[
                "numero_serie"
            ] = None


            # Fusor desta máquina não possui
            # número de série aplicável.
            if (
                self.tipo_consumivel(
                    supply
                )
                == "fusor"
            ):

                supply[
                    "numero_serie"
                ] = None


            self.supplies.append(
                supply
            )


        self.conectividade[
            "snmp"
        ] = True


        print(
            "[DEVICE] SNMP encontrou "
            f"{len(self.supplies)} suprimentos."
        )


        return self.supplies


    # ========================================================
    # COLETA COMPLETA
    # ========================================================

    async def coletar(
        self,
    ):

        print()
        print(
            "Coletando PJL + SYSDEBUG + SNMP..."
        )
        print()


        # ----------------------------------------------------
        # 1. PJL
        # ----------------------------------------------------

        try:

            await asyncio.wait_for(

                asyncio.to_thread(
                    self.coletar_pjl
                ),

                timeout=TIMEOUT_PJL,
            )


        except asyncio.TimeoutError:

            print(
                "[DEVICE] PJL excedeu timeout."
            )


        except Exception as erro:

            print(
                f"[DEVICE] Erro PJL: {erro}"
            )


        # ----------------------------------------------------
        # 2. SYSDEBUG
        # ----------------------------------------------------

        dados_sysdebug = {}


        try:

            dados_sysdebug = (
                await asyncio.wait_for(

                    asyncio.to_thread(
                        self.coletar_sysdebug_sync
                    ),

                    timeout=TIMEOUT_SYSDEBUG,
                )
            )


        except asyncio.TimeoutError:

            print(
                "[DEVICE] SYSDEBUG excedeu timeout."
            )


        except Exception as erro:

            print(
                f"[DEVICE] Erro SYSDEBUG: {erro}"
            )


        # ----------------------------------------------------
        # 3. SNMP
        # ----------------------------------------------------

        try:

            await self.coletar_snmp()


        except Exception as erro:

            print(
                f"[DEVICE] Erro SNMP: {erro}"
            )


        # ----------------------------------------------------
        # 4. RELACIONAR SERIAIS
        # ----------------------------------------------------

        try:

            self.associar_seriais_sysdebug(
                dados_sysdebug
            )


        except Exception as erro:

            print(
                "[DEVICE] Erro associando "
                f"seriais SYSDEBUG: {erro}"
            )


        return self.to_dict()


    # ========================================================
    # ESTADO
    # ========================================================

    def estado(
        self,
    ):

        if (

            self.conectividade[
                "pjl"
            ]

            and

            self.conectividade[
                "sysdebug"
            ]

            and

            self.conectividade[
                "snmp"
            ]

        ):

            return "EXCELENTE"


        if (

            self.conectividade[
                "pjl"
            ]

            or

            self.conectividade[
                "sysdebug"
            ]

            or

            self.conectividade[
                "snmp"
            ]

        ):

            return "PARCIAL"


        return "OFFLINE"


    # ========================================================
    # TOTAL SUPPLIES
    # ========================================================

    def total_supplies(
        self,
    ):

        return len(
            self.supplies
        )


    # ========================================================
    # CONTADOR
    # ========================================================

    def contador(
        self,
    ):

        return self.identificacao.get(
            "contador"
        )


    # ========================================================
    # SERIAL
    # ========================================================

    def serial(
        self,
    ):

        return self.identificacao.get(
            "serial"
        )


    # ========================================================
    # MODELO
    # ========================================================

    def modelo(
        self,
    ):

        return self.identificacao.get(
            "modelo"
        )


    # ========================================================
    # REPRESENTAÇÃO
    # ========================================================

    def to_dict(
        self,
    ):

        return {

            "ip":
                self.ip,

            "nome":
                self.nome,

            "identificacao":
                self.identificacao.copy(),

            "conectividade":
                self.conectividade.copy(),

            "supplies":
                list(
                    self.supplies
                ),

            "estado":
                self.estado(),

            "total_supplies":
                self.total_supplies(),

            "raw_sysdebug":
                (
                    self.raw_sysdebug.copy()

                    if isinstance(
                        self.raw_sysdebug,
                        dict,
                    )

                    else self.raw_sysdebug
                ),
        }


# ============================================================
# COMPATIBILIDADE
# ============================================================

Device = PrinterDevice


# ============================================================
# FUNÇÃO DE CONVENIÊNCIA
# ============================================================

async def coletar_device(
    ip,
    nome=None,
):

    device = PrinterDevice(
        ip=ip,
        nome=nome,
    )

    await device.coletar()

    return device


# ============================================================
# TESTE DIRETO
# ============================================================

async def teste():

    print()
    print("=" * 72)
    print(
        "PRINTER ASSISTANT - TESTE DEVICE"
    )
    print("=" * 72)
    print()


    ip = input(
        "Digite o IP da impressora: "
    ).strip()


    if not ip:

        print(
            "IP não informado."
        )

        return


    device = PrinterDevice(
        ip
    )


    await device.coletar()


    dados = device.to_dict()


    identificacao = (
        dados[
            "identificacao"
        ]
    )


    conectividade = (
        dados[
            "conectividade"
        ]
    )


    print()
    print("=" * 72)
    print(
        "IMPRESSORA"
    )
    print("=" * 72)
    print()


    print(
        "IP:",
        device.ip
    )


    print(
        "Fabricante:",
        identificacao[
            "fabricante"
        ]
    )


    print(
        "Modelo:",
        identificacao[
            "modelo"
        ]
    )


    print(
        "Família:",
        identificacao[
            "familia"
        ]
    )


    print(
        "Tipo:",
        identificacao[
            "tipo"
        ]
    )


    print(
        "Serial:",
        identificacao[
            "serial"
        ]
    )


    print(
        "Firmware:",
        identificacao[
            "firmware"
        ]
    )


    contador = identificacao[
        "contador"
    ]


    if contador is None:

        print(
            "Contador: desconhecido"
        )

    else:

        print(
            "Contador:",
            f"{contador:,}".replace(
                ",",
                ".",
            )
        )


    print()
    print(
        "PJL:",
        "ATIVO"
        if conectividade[
            "pjl"
        ]
        else "INATIVO"
    )


    print(
        "SYSDEBUG:",
        "ATIVO"
        if conectividade[
            "sysdebug"
        ]
        else "INATIVO"
    )


    print(
        "SNMP:",
        "ATIVO"
        if conectividade[
            "snmp"
        ]
        else "INATIVO"
    )


    print()
    print(
        "Estado:",
        dados[
            "estado"
        ]
    )


    print(
        "Suprimentos:",
        len(
            dados[
                "supplies"
            ]
        )
    )


    # ========================================================
    # CONSUMÍVEIS
    # ========================================================

    print()
    print("=" * 72)
    print(
        "CONSUMÍVEIS"
    )
    print("=" * 72)


    for numero, supply in enumerate(
        dados[
            "supplies"
        ],
        start=1,
    ):

        print()


        nome_supply = (
            supply.get(
                "nome"
            )
            or
            "Consumível"
        )


        tipo_supply = (
            device.tipo_consumivel(
                supply
            )
        )


        print(
            f"[{numero}] "
            f"{nome_supply}"
        )


        print(
            "    Nível:",
            end=" "
        )


        nivel = supply.get(
            "nivel"
        )


        if nivel is None:

            nivel = supply.get(
                "percentual"
            )


        if nivel is None:

            print(
                "N/D"
            )

        else:

            print(
                f"{nivel} %"
            )


        print(
            "    Condição:",
            supply.get(
                "condicao",
                "N/D",
            )
        )


        print(
            "    Capacidade:",
            supply.get(
                "capacidade",
                "N/D",
            )
        )


        print(
            "    Restante:",
            supply.get(
                "restante",
                "N/D",
            )
        )


        print(
            "    Consumido:",
            supply.get(
                "consumido",
                "N/D",
            )
        )


        # ----------------------------------------------------
        # SERIAL
        # ----------------------------------------------------

        if tipo_supply == "fusor":

            print(
                "    Nº série: NÃO APLICÁVEL"
            )

        else:

            serial_supply = (
                supply.get(
                    "numero_serie"
                )
            )

            print(
                "    Nº série:",
                serial_supply
                or
                "N/D"
            )


        # ----------------------------------------------------
        # GARANTIA
        # ----------------------------------------------------

        if (
            tipo_supply
            == "unidade_imagem"
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

                texto_garantia = (
                    "N/D"
                )


            print(
                "    Garantia:",
                texto_garantia
            )


    print()
    print("=" * 72)
    print(
        "TESTE CONCLUÍDO"
    )
    print("=" * 72)
    print()


# ============================================================
# EXECUÇÃO COMO MÓDULO
# ============================================================

if __name__ == "__main__":

    asyncio.run(
        teste()
    )

