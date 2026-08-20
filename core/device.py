# core/device.py


"""
============================================================
PRINTER ASSISTANT
DEVICE
============================================================

Representa uma impressora física dentro do sistema.

Fontes:

    PJL
        identificação auxiliar
        contador auxiliar

    SYSDEBUG
        fabricante
        modelo
        serial
        firmware
        contador oficial
        consumíveis
        seriais de consumíveis quando disponíveis

    SNMP
        consumíveis
        capacidade
        restante
        consumido
        nível
        condição

IMPORTANTE
------------------------------------------------------------

O Device NÃO implementa protocolos.

Ele apenas coordena:

    core.pjl
    core.sysdebug
    core.snmp

REGRAS
------------------------------------------------------------

1. SYSDEBUG tem prioridade para contador.

2. PJL pode fornecer contador auxiliar.

3. SYSDEBUG tem prioridade para serial da impressora.

4. SNMP fornece os dados quantitativos dos consumíveis.

5. SYSDEBUG pode fornecer os seriais dos consumíveis.

6. Part Number não é informação apresentada nesta etapa.

7. Fusor não recebe número de série na interface.

8. Timeout de PJL/SYSDEBUG não pode travar a coleta completa.

9. A MX611dhe é apenas o equipamento de laboratório atual.

10. O Device NÃO interpreta prtMarkerSuppliesLevel.
    Essa interpretação pertence ao módulo SNMP.

11. O Device preserva os valores quantitativos recebidos
    pelo SNMP e não deve transformar um nível bruto em
    percentual novamente.

"""

import asyncio
import threading


from core.pjl import coletar_identificacao
from core.snmp import coletar_supplies
from core.sysdebug import coletar_sysdebug


# ============================================================
# CONFIGURAÇÃO
# ============================================================

TIMEOUT_PJL = 15
TIMEOUT_SYSDEBUG = 60
TIMEOUT_SNMP = 45


# ============================================================
# DEVICE
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

        if not self.modelo_valido(
            modelo_novo
        ):

            modelo_novo = None

        if modelo_novo:

            if not self.modelo_valido(
                modelo_atual
            ):

                modelo_atual = None

            if modelo_atual:

                modelo_final = (
                    modelo_atual
                )

            else:

                modelo_final = str(
                    modelo_novo
                ).strip()

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
            and serial_atual != "Desconhecido"
        ):

            serial_novo = (
                serial_atual
            )

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

        elif (
            firmware_atual
            and firmware_atual != "Desconhecido"
        ):

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

        fabricante = dados.get(
            "fabricante"
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
    # EXECUTAR FUNÇÃO BLOQUEANTE COM TIMEOUT REAL
    # ========================================================

    @staticmethod
    async def executar_com_timeout(
        funcao,
        timeout,
        nome,
    ):
        """
        Executa uma função bloqueante em uma thread daemon.

        NÃO utiliza asyncio.to_thread() para a operação
        bloqueante diretamente.

        Isso permite abandonar a espera quando uma operação
        externa ficar travada.
        """

        loop = asyncio.get_running_loop()

        resultado = {
            "terminou": False,
            "valor": None,
            "erro": None,
        }

        concluido = (
            threading.Event()
        )

        def executar():

            try:

                resultado["valor"] = (
                    funcao()
                )

            except Exception as erro:

                resultado["erro"] = erro

            finally:

                resultado["terminou"] = True

                loop.call_soon_threadsafe(
                    concluido.set
                )

        thread = threading.Thread(
            target=executar,
            daemon=True,
            name=f"PrinterAssistant-{nome}",
        )

        thread.start()

        try:

            await asyncio.wait_for(
                asyncio.to_thread(
                    concluido.wait
                ),
                timeout=timeout,
            )

        except asyncio.TimeoutError:

            print(
                f"[DEVICE] {nome} excedeu timeout."
            )

            return None

        except Exception as erro:

            print(
                f"[DEVICE] Erro aguardando {nome}: "
                f"{erro}"
            )

            return None

        if resultado["erro"] is not None:

            print(
                f"[DEVICE] Erro {nome}: "
                f"{resultado['erro']}"
            )

            return None

        return resultado["valor"]


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
                f"[DEVICE] Erro SYSDEBUG: "
                f"{erro}"
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
                f"[DEVICE] Erro PJL: "
                f"{erro}"
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

            texto = str(
                tipo
            ).strip().lower()

            if texto in (
                "toner",
                "cartucho",
                "cartridge",
            ):

                return "toner"

            if texto in (
                "unidade_imagem",
                "unidade imagem",
                "imaging",
                "imaging unit",
                "photoconductor",
                "fotocondutor",
                "drum",
            ):

                return "unidade_imagem"

            if texto in (
                "fusor",
                "fuser",
                "maintenance",
                "maintenance kit",
                "kit manutencao",
                "kit manutenção",
            ):

                return "fusor"

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
        ).strip().lower()

        if (
            "maintenance kit"
            in texto
        ):

            return "fusor"

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

        if (
            "toner" in texto
            or
            "cartucho" in texto
            or
            "cartridge" in texto
        ):

            return "toner"

        if (
            "unidade de imagem"
            in texto
            or
            "imaging unit"
            in texto
            or
            "imaging" in texto
            or
            "photoconductor" in texto
            or
            "drum" in texto
            or
            "fotocondutor" in texto
        ):

            return "unidade_imagem"

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

                for valor in (
                    objeto.values()
                ):

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
    # NORMALIZAR SUPPLIES RECEBIDOS DO SNMP
    # ========================================================

    @staticmethod
    def normalizar_supply_snmp(
        supply,
    ):
        """
        Normalização de segurança do objeto recebido do SNMP.

        IMPORTANTE:

        O cálculo correto do percentual pertence ao SNMP.

        O Device não recalcula um valor normal válido.

        Esta função apenas impede que uma implementação antiga
        que ainda esteja entregando o valor bruto de
        prtMarkerSuppliesLevel seja exibida diretamente como
        percentual quando:

            nivel > 100
            capacidade > 0

        Exemplo de retorno antigo:

            capacidade = 10000
            nivel = 7300

        Nesse caso:

            7300 / 10000 * 100 = 73%

        Se o SNMP moderno já entregar:

            percentual = 73

        o valor é preservado.

        Valores especiais negativos do Printer-MIB não são
        convertidos silenciosamente.
        """

        if not isinstance(
            supply,
            dict,
        ):

            return None

        resultado = supply.copy()

        capacidade = resultado.get(
            "capacidade"
        )

        nivel = resultado.get(
            "nivel"
        )

        percentual = resultado.get(
            "percentual"
        )

        try:

            capacidade_num = (
                float(capacidade)
                if capacidade is not None
                else None
            )

        except (
            TypeError,
            ValueError,
        ):

            capacidade_num = None

        try:

            nivel_num = (
                float(nivel)
                if nivel is not None
                else None
            )

        except (
            TypeError,
            ValueError,
        ):

            nivel_num = None

        try:

            percentual_num = (
                float(percentual)
                if percentual is not None
                else None
            )

        except (
            TypeError,
            ValueError,
        ):

            percentual_num = None

        # ----------------------------------------------------
        # SNMP moderno
        # ----------------------------------------------------
        #
        # Se o módulo SNMP já calculou o percentual, não
        # mexemos nele.
        #

        if (
            percentual_num is not None
            and 0 <= percentual_num <= 100
        ):

            resultado[
                "percentual"
            ] = percentual_num

            resultado[
                "nivel"
            ] = percentual_num

            return resultado

        # ----------------------------------------------------
        # Compatibilidade com retorno antigo
        # ----------------------------------------------------

        if (
            nivel_num is not None
            and capacidade_num is not None
            and capacidade_num > 0
            and nivel_num >= 0
            and nivel_num > 100
            and nivel_num <= capacidade_num
        ):

            percentual_calculado = (
                nivel_num
                / capacidade_num
                * 100
            )

            percentual_calculado = max(
                0,
                min(
                    100,
                    percentual_calculado,
                ),
            )

            resultado[
                "percentual"
            ] = percentual_calculado

            resultado[
                "nivel"
            ] = percentual_calculado

            # Se o SNMP antigo não tinha esses campos,
            # calculamos apenas para compatibilidade.

            if (
                resultado.get(
                    "restante"
                )
                is None
            ):

                resultado[
                    "restante"
                ] = round(
                    capacidade_num
                    * percentual_calculado
                    / 100
                )

            if (
                resultado.get(
                    "consumido"
                )
                is None
            ):

                resultado[
                    "consumido"
                ] = (
                    capacidade_num
                    - resultado[
                        "restante"
                    ]
                )

            return resultado

        # ----------------------------------------------------
        # Valor desconhecido / especial
        # ----------------------------------------------------

        if nivel_num is not None:

            if nivel_num < 0:

                resultado[
                    "nivel"
                ] = None

                resultado[
                    "percentual"
                ] = None

        return resultado


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
                f"[DEVICE] Erro SNMP: "
                f"{erro}"
            )

            return self.supplies

        if not dados:

            print(
                "[DEVICE] SNMP não retornou "
                "suprimentos."
            )

            return self.supplies

        self.supplies = []

        for supply in dados:

            if not isinstance(
                supply,
                dict,
            ):

                continue

            supply = (
                self.normalizar_supply_snmp(
                    supply
                )
            )

            if supply is None:

                continue

            # ------------------------------------------------
            # SERIAL
            # ------------------------------------------------
            #
            # SNMP não define aqui o serial de consumível.
            # O serial será associado posteriormente a partir
            # do SYSDEBUG.
            #

            supply[
                "numero_serie"
            ] = None

            # Fusor nunca apresenta serial.

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
        # PJL
        # ----------------------------------------------------

        await self.executar_com_timeout(
            self.coletar_pjl,
            TIMEOUT_PJL,
            "PJL",
        )

        # ----------------------------------------------------
        # SYSDEBUG
        # ----------------------------------------------------

        dados_sysdebug = (
            await self.executar_com_timeout(
                self.coletar_sysdebug_sync,
                TIMEOUT_SYSDEBUG,
                "SYSDEBUG",
            )
        )

        if not isinstance(
            dados_sysdebug,
            dict,
        ):

            dados_sysdebug = {}


        # ----------------------------------------------------
        # SNMP
        # ----------------------------------------------------

        try:

            await self.coletar_snmp()

        except Exception as erro:

            print(
                f"[DEVICE] Erro SNMP: "
                f"{erro}"
            )


        # ----------------------------------------------------
        # ASSOCIAR SERIAIS
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

        fontes = (
            self.conectividade[
                "pjl"
            ],
            self.conectividade[
                "sysdebug"
            ],
            self.conectividade[
                "snmp"
            ],
        )

        if all(fontes):

            return "EXCELENTE"

        if any(fontes):

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
# CONVENIÊNCIA
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
    print("IMPRESSORA")
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

    print()
    print("=" * 72)
    print("CONSUMÍVEIS")
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

        nivel = supply.get(
            "percentual"
        )

        if nivel is None:

            nivel = supply.get(
                "nivel"
            )

        if nivel is None:

            print(
                "    Nível: N/D"
            )

        else:

            try:

                print(
                    f"    Nível: {float(nivel):g} %"
                )

            except (
                TypeError,
                ValueError,
            ):

                print(
                    f"    Nível: {nivel} %"
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

        if tipo_supply == "fusor":

            print(
                "    Nº série: NÃO APLICÁVEL"
            )

        else:

            print(
                "    Nº série:",
                supply.get(
                    "numero_serie"
                )
                or
                "N/D"
            )

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


if __name__ == "__main__":

    asyncio.run(
        teste()
    )