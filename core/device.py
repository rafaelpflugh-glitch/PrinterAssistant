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

10. O Device não deve interpretar diretamente
    prtMarkerSuppliesLevel quando o SNMP moderno já tiver
    fornecido os valores normalizados.

11. O Device preserva os valores quantitativos recebidos
    pelo SNMP.

12. Compatibilidade com retornos antigos do SNMP é mantida,
    sem interferir quando o módulo SNMP moderno já fornece
    percentual normalizado.

13. Nenhuma fonte posterior deve apagar uma informação válida
    simplesmente por ter retornado valor vazio, desconhecido
    ou inválido.

14. O Device coordena as fontes; não implementa protocolos.

15. A interface trabalha somente com três categorias padrão
    de consumíveis:

        toner
        unidade de imagem
        fusor

    Outros itens retornados pelo SNMP, como ADF Kit, Roller Kit,
    grampos ou perfurador, não fazem parte da lista padrão.

16. A ordem padrão dos consumíveis é:

        1. toner
        2. unidade de imagem
        3. fusor
"""


import asyncio
import inspect
import threading
import unicodedata


from core.pjl import coletar_identificacao
from core.snmp import coletar_supplies, coletar_identificacao_snmp
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

        self.sysdebug_filtered = {}


    # ========================================================
    # UTILITÁRIOS DE NORMALIZAÇÃO
    # ========================================================

    @staticmethod
    def normalizar_texto(
        valor,
    ):
        """
        Normaliza texto para comparações internas.

        Exemplos:

            "Número de Série"
            "numero_serie"
            "numero-série"
            "NÚMERO SÉRIE"

        tornam-se equivalentes para comparação.

        A normalização é usada apenas internamente.
        O valor original não é alterado.
        """

        if valor is None:

            return ""

        texto = str(
            valor
        ).strip().lower()

        texto = unicodedata.normalize(
            "NFKD",
            texto,
        )

        texto = "".join(
            caractere
            for caractere in texto
            if not unicodedata.combining(
                caractere
            )
        )

        substituicoes = {
            ".": " ",
            "-": " ",
            "_": " ",
            "/": " ",
            "\\": " ",
            ":": " ",
        }

        for antigo, novo in substituicoes.items():

            texto = texto.replace(
                antigo,
                novo,
            )

        return " ".join(
            texto.split()
        )


    @classmethod
    def valor_valido(
        cls,
        valor,
    ):
        """
        Determina se um valor textual é realmente utilizável.

        Evita que respostas como:

            N/D
            Unknown
            None
            Null
            Desconhecido
            Speed: 0

        sobrescrevam uma informação válida já obtida.
        """

        if valor is None:

            return False

        texto = str(
            valor
        ).strip()

        if not texto:

            return False

        normalizado = cls.normalizar_texto(
            texto
        )

        invalidos = {
            "",
            "n d",
            "nd",
            "na",
            "n a",
            "nao informado",
            "nao disponivel",
            "desconhecido",
            "unknown",
            "none",
            "null",
            "nil",
            "undefined",
            "speed",
            "speed 0",
        }

        if normalizado in invalidos:

            return False

        if normalizado.startswith(
            "speed "
        ):

            restante = normalizado[6:].strip()

            if restante in (
                "",
                "0",
            ):

                return False

        return True


    @staticmethod
    def converter_numero(
        valor,
    ):
        """
        Conversão segura para número.

        Mantém None quando a conversão não é possível.
        """

        if valor is None:

            return None

        if isinstance(
            valor,
            bool,
        ):

            return float(
                int(valor)
            )

        try:

            return float(
                valor
            )

        except (
            TypeError,
            ValueError,
        ):

            return None


    # ========================================================
    # FABRICANTE
    # ========================================================

    @classmethod
    def detectar_fabricante(
        cls,
        modelo,
    ):

        texto = cls.normalizar_texto(
            modelo
        )

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

    @classmethod
    def modelo_valido(
        cls,
        modelo,
    ):

        if modelo is None:

            return False

        texto = str(
            modelo
        ).strip()

        if not texto:

            return False

        normalizado = cls.normalizar_texto(
            texto
        )

        valores_invalidos = {
            "",
            "speed",
            "speed 0",
            "0",
            "n d",
            "nd",
            "desconhecido",
            "unknown",
            "none",
            "null",
            "nil",
            "undefined",
        }

        if normalizado in valores_invalidos:

            return False

        if normalizado.startswith(
            "speed "
        ):

            return False

        return True


    # ========================================================
    # FAMÍLIA
    # ========================================================

    @classmethod
    def detectar_familia(
        cls,
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
            cls.normalizar_texto(
                partes[0]
            )
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

    @classmethod
    def detectar_tipo(
        cls,
        fabricante,
        modelo,
    ):

        texto = cls.normalizar_texto(
            modelo
        )

        fabricante_normalizado = (
            cls.normalizar_texto(
                fabricante
            )
        )

        if fabricante_normalizado == "lexmark":

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

        if fabricante_normalizado == "epson":

            return "Impressora Epson"

        if fabricante_normalizado == "brother":

            return "Impressora Brother"

        if fabricante_normalizado == "canon":

            return "Impressora Canon"

        if fabricante_normalizado == "hp":

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

        # Prioriza identificação de hardware (SNMP / PJL) caso o modelo atual
        # seja desconhecido ou tenha vindo de fallback impreciso.
        promover_hardware = (
            origem in ("SNMP", "PJL")
            and modelo_novo
            and (
                not self.modelo_valido(modelo_atual)
                or str(modelo_atual).strip().lower() in ("desconhecido", "none", "", "impressora")
                or (not str(modelo_atual).lower().startswith("lexmark") and str(modelo_novo).lower().startswith("lexmark"))
            )
        )

        if promover_hardware:

            modelo_final = (
                str(
                    modelo_novo
                ).strip()
            )

        elif self.modelo_valido(
            modelo_atual
        ):

            modelo_final = (
                str(
                    modelo_atual
                ).strip()
            )

        elif modelo_novo:

            modelo_final = (
                str(
                    modelo_novo
                ).strip()
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

        if not self.valor_valido(
            serial_novo
        ):

            serial_novo = None

        else:

            serial_novo = str(
                serial_novo
            ).strip()

        if serial_novo:

            serial_final = (
                serial_novo
            )

        elif self.valor_valido(
            serial_atual
        ):

            serial_final = str(
                serial_atual
            ).strip()

        else:

            serial_final = (
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

        if self.valor_valido(
            firmware_novo
        ):

            firmware_final = str(
                firmware_novo
            ).strip()

        elif self.valor_valido(
            firmware_atual
        ):

            firmware_final = str(
                firmware_atual
            ).strip()

        else:

            firmware_final = (
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

        contador_novo_valido = (
            contador_novo is not None
        )

        if contador_novo_valido:

            if isinstance(
                contador_novo,
                str,
            ):

                contador_novo_valido = (
                    self.valor_valido(
                        contador_novo
                    )
                )

        if contador_novo_valido:

            if origem == "SYSDEBUG":

                self.origem_contador = (
                    "SYSDEBUG"
                )

            elif (
                self.origem_contador
                != "SYSDEBUG"
            ):

                self.origem_contador = (
                    origem
                )

            contador_final = (
                contador_novo
            )

        else:

            contador_final = (
                contador_atual
            )


        # ----------------------------------------------------
        # FABRICANTE
        # ----------------------------------------------------

        fabricante_novo = dados.get(
            "fabricante"
        )

        if self.valor_valido(
            fabricante_novo
        ):

            fabricante = str(
                fabricante_novo
            ).strip()

        else:

            fabricante = (
                self.identificacao.get(
                    "fabricante"
                )
            )

            if not self.valor_valido(
                fabricante
            ):

                fabricante = (
                    self.detectar_fabricante(
                        modelo_final
                    )
                )

        if not self.valor_valido(
            fabricante
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
                serial_final,

            "firmware":
                firmware_final,

            "contador":
                contador_final,
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
        Executa uma função potencialmente bloqueante em uma
        thread daemon.

        A thread não pode ser interrompida à força pelo Python.
        Porém, o Device abandona a espera após o timeout e
        continua a coleta das demais fontes.

        Isso impede que PJL/SYSDEBUG bloqueados parem todo o
        diagnóstico.

        A função também suporta retorno awaitable, caso alguma
        implementação futura seja assíncrona.
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

                valor = funcao()

                if inspect.isawaitable(
                    valor
                ):

                    try:

                        novo_loop = (
                            asyncio.new_event_loop()
                        )

                        try:

                            asyncio.set_event_loop(
                                novo_loop
                            )

                            valor = (
                                novo_loop.run_until_complete(
                                    valor
                                )
                            )

                        finally:

                            novo_loop.close()

                    except Exception:

                        raise

                resultado["valor"] = (
                    valor
                )

            except Exception as erro:

                resultado["erro"] = erro

            finally:

                resultado["terminou"] = True

                try:

                    loop.call_soon_threadsafe(
                        concluido.set
                    )

                except Exception:

                    concluido.set()

        thread = threading.Thread(
            target=executar,
            daemon=True,
            name=(
                f"PrinterAssistant-{nome}"
            ),
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

                # Preserva o retorno bruto completo.

                self.raw_sysdebug = (
                    dados.copy()
                )

                if isinstance(
                    dados.get("sysdebug_filtered"),
                    dict,
                ):
                    self.sysdebug_filtered = (
                        dados["sysdebug_filtered"].copy()
                    )

                self.normalizar_identificacao(
                    dados,
                    "SYSDEBUG",
                )

                self.conectividade[
                    "sysdebug"
                ] = True

                # SYSDEBUG normalmente é obtido pela
                # interface web/debug da impressora.

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

                    self.modelo_valido(
                        dados.get(
                            "modelo"
                        )
                    )

                    or

                    self.valor_valido(
                        dados.get(
                            "serial"
                        )
                    )

                    or

                    dados.get(
                        "contador"
                    )
                    is not None
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

    @classmethod
    def tipo_consumivel(
        cls,
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

            texto = cls.normalizar_texto(
                tipo
            )

            if texto in (
                "toner",
                "cartucho",
                "cartridge",
            ):

                return "toner"

            if texto in (
                "unidade imagem",
                "unidade de imagem",
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

        texto = cls.normalizar_texto(
            nome
        )


        if (
            "maintenance kit"
            in texto
            or
            "kit manutencao"
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
            "unidade imagem"
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
    # ORDENAR SUPRIMENTOS PADRÃO
    # ========================================================

    @classmethod
    def ordenar_supplies(
        cls,
        supplies,
    ):
        """
        Mantém a ordem padrão da interface:

            1. Toner
            2. Unidade de imagem
            3. Fusor

        A função não altera os dados individuais dos
        suprimentos.
        """

        ordem = {
            "toner": 0,
            "unidade_imagem": 1,
            "fusor": 2,
        }

        return sorted(
            supplies,
            key=lambda supply: ordem.get(
                cls.tipo_consumivel(
                    supply
                ),
                99,
            ),
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

                chaves_normalizadas = {

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

                    chaves_normalizadas
                )


                possui_serial = bool(

                    {
                        "serial",
                        "numero serie",
                        "serial number",
                        "supply serial",
                        "consumable serial",
                    }

                    &

                    chaves_normalizadas
                )


                eh_container_raiz = bool(
                    {
                        "consumiveis",
                        "supplies",
                        "identificacao",
                        "conectividade",
                    }
                    &
                    chaves_normalizadas
                )


                if (
                    not eh_container_raiz
                    and
                    (
                        possui_identificacao
                        or
                        possui_serial
                    )
                ):

                    encontrados.append(
                        objeto
                    )


                for chave_filha, valor in (
                    objeto.items()
                ):
                    if cls.normalizar_texto(chave_filha) == "sysdebug filtered":
                        continue

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

    @classmethod
    def extrair_serial_supply(
        cls,
        supply,
    ):

        if not isinstance(
            supply,
            dict,
        ):

            return None


        # Primeiro tenta as chaves conhecidas
        # diretamente.

        possiveis = (

            "numero_serie",
            "numero série",
            "serial",
            "serial_number",
            "serial number",
            "supply_serial",
            "consumable_serial",
            "supply serial",
            "consumable serial",
        )


        for chave in possiveis:

            valor = supply.get(
                chave
            )

            if cls.valor_valido(
                valor
            ):

                return str(
                    valor
                ).strip()


        # ----------------------------------------------------
        # Segunda tentativa:
        # procura pela chave normalizada.
        # ----------------------------------------------------

        for chave, valor in supply.items():

            chave_normalizada = (
                cls.normalizar_texto(
                    chave
                )
            )

            if chave_normalizada in (
                "numero serie",
                "serial",
                "serial number",
                "supply serial",
                "consumable serial",
            ):

                if cls.valor_valido(
                    valor
                ):

                    return str(
                        valor
                    ).strip()


        return None


    # ========================================================
    # EXTRAIR NOME SUPPLY
    # ========================================================

    @classmethod
    def extrair_nome_supply(
        cls,
        supply,
    ):

        if not isinstance(
            supply,
            dict,
        ):

            return ""


        possiveis = (

            "nome",
            "name",
            "descricao",
            "description",
        )


        for chave in possiveis:

            valor = supply.get(
                chave
            )

            if cls.valor_valido(
                valor
            ):

                return str(
                    valor
                ).strip()


        # Compatibilidade com chaves
        # com acentos / underscore / espaços.

        for chave, valor in supply.items():

            chave_normalizada = (
                cls.normalizar_texto(
                    chave
                )
            )

            if chave_normalizada in (
                "nome",
                "name",
                "descricao",
                "description",
            ):

                if cls.valor_valido(
                    valor
                ):

                    return str(
                        valor
                    ).strip()


        return ""


    # ========================================================
    # ASSOCIAR SERIAIS SYSDEBUG -> SNMP
    # ========================================================

    def associar_seriais_sysdebug(
        self,
        dados_sysdebug,
    ):

        if not dados_sysdebug:

            return

        if isinstance(
            dados_sysdebug,
            dict,
        ) and isinstance(
            dados_sysdebug.get("sysdebug_filtered"),
            dict,
        ):
            self.sysdebug_filtered = (
                dados_sysdebug["sysdebug_filtered"].copy()
            )


        candidatos_brutos = (
            self.extrair_supplies_sysdebug(
                dados_sysdebug
            )
        )


        if not candidatos_brutos:

            return


        serial_maquina = str(
            self.identificacao.get("serial") or ""
        ).strip()

        candidatos = []


        for item in candidatos_brutos:

            serial = (
                self.extrair_serial_supply(
                    item
                )
            )

            tipo = (
                self.tipo_consumivel(
                    item
                )
            )

            if not serial and tipo != "fusor":
                continue

            if (
                serial
                and serial_maquina
                and serial_maquina.lower() not in ("desconhecido", "none", "")
                and serial.strip().upper() == serial_maquina.upper()
            ):
                continue

            nome = (
                self.extrair_nome_supply(
                    item
                )
            )

            candidatos.append(
                {
                    "serial":
                        serial,

                    "tipo":
                        tipo,

                    "nome":
                        self.normalizar_texto(
                            nome
                        ),

                    "part_number":
                        item.get("part_number")
                        if isinstance(item, dict)
                        else None,

                    "page_count":
                        item.get("page_count")
                        if isinstance(item, dict)
                        else None,

                    "consumido":
                        item.get("consumido")
                        if isinstance(item, dict)
                        else None,

                    "rotacoes":
                        (item.get("rotacoes") or item.get("rotations"))
                        if isinstance(item, dict)
                        else None,

                    "capacidade":
                        item.get("capacidade")
                        if isinstance(item, dict)
                        else None,

                    "restante":
                        item.get("restante")
                        if isinstance(item, dict)
                        else None,

                    "nivel":
                        item.get("nivel")
                        if isinstance(item, dict)
                        else None,
                }
            )


        if not candidatos:

            return


        usados = set()


        for supply in self.supplies:

            if not isinstance(
                supply,
                dict,
            ):

                continue


            tipo_supply = (
                self.tipo_consumivel(
                    supply
                )
            )


            # ------------------------------------------------
            # FUSOR
            # ------------------------------------------------
            #
            # Regra da interface:
            # fusor não exibe número de série, mas recebe
            # métricas reais de consumo do SysDebug.
            #
            if tipo_supply == "fusor":
                supply["numero_serie"] = None


            nome_supply = (
                self.normalizar_texto(
                    self.extrair_nome_supply(
                        supply
                    )
                )
            )


            escolhido = None


            # ------------------------------------------------
            # 1. CORRESPONDÊNCIA EXATA POR TIPO
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
            # 2. CORRESPONDÊNCIA POR NOME
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


                    if not nome_supply:

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


            # ------------------------------------------------
            # 3. SE NÃO HOUVER TIPO NEM NOME,
            #    NÃO FORÇA ASSOCIAÇÃO.
            # ------------------------------------------------

            if escolhido is None:

                continue


            numero, candidato = (
                escolhido
            )


            if tipo_supply != "fusor":
                supply["numero_serie"] = candidato.get("serial")
            else:
                supply["numero_serie"] = None

            pn_atual = str(supply.get("part_number") or "").strip()
            if candidato.get("part_number") and (not pn_atual or (serial_maquina and serial_maquina.upper() in pn_atual.upper())):
                supply["part_number"] = candidato["part_number"]

            # Métricas reais de consumo do SysDebug
            if candidato.get("page_count") is not None:
                supply["consumido"] = candidato["page_count"]
            elif candidato.get("consumido") is not None:
                supply["consumido"] = candidato["consumido"]

            if candidato.get("rotacoes") is not None:
                supply["rotacoes"] = candidato["rotacoes"]
                supply["drum_rotations"] = candidato["rotacoes"]

            if candidato.get("capacidade") is not None:
                supply["capacidade"] = candidato["capacidade"]

            if candidato.get("restante") is not None:
                supply["restante"] = candidato["restante"]

            if candidato.get("nivel") is not None:
                supply["nivel"] = candidato["nivel"]
                supply["percentual"] = candidato["nivel"]

            usados.add(
                numero
            )


        # Enriquecimento complementar direto a partir de self.sysdebug_filtered
        if isinstance(self.sysdebug_filtered, dict) and self.sysdebug_filtered:
            filt = self.sysdebug_filtered
            for supply in self.supplies:
                if not isinstance(supply, dict):
                    continue
                tipo = self.tipo_consumivel(supply)
                if tipo == "unidade_imagem":
                    if filt.get("drum_serial") and not supply.get("numero_serie"):
                        supply["numero_serie"] = filt["drum_serial"]
                    pn_drum = str(supply.get("part_number") or "").strip()
                    if filt.get("drum_part_number") and (not pn_drum or (serial_maquina and serial_maquina.upper() in pn_drum.upper())):
                        supply["part_number"] = filt["drum_part_number"]
                    if filt.get("drum_page_count") is not None:
                        supply["consumido"] = filt["drum_page_count"]
                    if filt.get("drum_rotations") is not None:
                        supply["rotacoes"] = filt["drum_rotations"]
                        supply["drum_rotations"] = filt["drum_rotations"]
                    if filt.get("drum_life_remaining") is not None:
                        supply["nivel"] = filt["drum_life_remaining"]
                        supply["percentual"] = filt["drum_life_remaining"]
                elif tipo == "toner":
                    if filt.get("toner_serial") and not supply.get("numero_serie"):
                        supply["numero_serie"] = filt["toner_serial"]
                    pn_toner = str(supply.get("part_number") or "").strip()
                    if filt.get("toner_part_number") and (not pn_toner or (serial_maquina and serial_maquina.upper() in pn_toner.upper())):
                        supply["part_number"] = filt["toner_part_number"]
                    if filt.get("toner_page_count") is not None:
                        supply["consumido"] = filt["toner_page_count"]
                    if filt.get("toner_pages_remaining") is not None:
                        supply["restante"] = filt["toner_pages_remaining"]
                    if filt.get("toner_max_capacity") is not None:
                        supply["capacidade"] = filt["toner_max_capacity"]
                    if filt.get("toner_life_remaining") is not None:
                        supply["nivel"] = filt["toner_life_remaining"]
                        supply["percentual"] = filt["toner_life_remaining"]


    # ========================================================
    # NORMALIZAR SUPPLY RECEBIDO DO SNMP
    # ========================================================

    @classmethod
    def normalizar_supply_snmp(
        cls,
        supply,
    ):
        """
        Normalização de segurança do objeto recebido do SNMP.

        O SNMP moderno é responsável pelo significado dos
        valores quantitativos.

        Se o SNMP moderno já entregar:

            percentual = 73

        esse valor é preservado.

        Se existir:

            nivel = 73

        também é preservado.

        Compatibilidade antiga:

        Se uma implementação anterior ainda entregar:

            capacidade = 10000
            nivel = 7300

        o Device mantém a compatibilidade e pode calcular
        percentual = 73.

        Isso não interfere no SNMP moderno.

        Valores negativos especiais do Printer-MIB não são
        convertidos silenciosamente em percentuais.
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


        capacidade_num = (
            cls.converter_numero(
                capacidade
            )
        )

        nivel_num = (
            cls.converter_numero(
                nivel
            )
        )

        percentual_num = (
            cls.converter_numero(
                percentual
            )
        )


        # ----------------------------------------------------
        # SNMP MODERNO
        # ----------------------------------------------------

        if (
            percentual_num is not None
            and
            0 <= percentual_num <= 100
        ):

            resultado[
                "percentual"
            ] = percentual_num

            if (
                nivel_num is None
                or
                0 <= nivel_num <= 100
            ):

                resultado[
                    "nivel"
                ] = percentual_num

            return resultado


        # ----------------------------------------------------
        # SNMP MODERNO COM NIVEL JÁ NORMALIZADO
        # ----------------------------------------------------

        if (
            percentual_num is None
            and
            nivel_num is not None
            and
            0 <= nivel_num <= 100
        ):

            resultado[
                "percentual"
            ] = nivel_num

            resultado[
                "nivel"
            ] = nivel_num

            return resultado


        # ----------------------------------------------------
        # COMPATIBILIDADE COM RETORNO ANTIGO
        # ----------------------------------------------------

        if (
            nivel_num is not None
            and
            capacidade_num is not None
            and
            capacidade_num > 0
            and
            nivel_num >= 0
            and
            nivel_num > 100
            and
            nivel_num <= capacidade_num
        ):

            percentual_calculado = (
                nivel_num
                /
                capacidade_num
                *
                100
            )


            percentual_calculado = max(
                0,
                min(
                    100,
                    percentual_calculado,
                ),
            )


            if (
                percentual_num is None
                or
                not (
                    0
                    <= percentual_num
                    <= 100
                )
            ):

                resultado[
                    "percentual"
                ] = percentual_calculado


            resultado[
                "nivel"
            ] = resultado.get(
                "percentual",
                percentual_calculado,
            )


            # ------------------------------------------------
            # RESTANTE
            # ------------------------------------------------

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
                    *
                    percentual_calculado
                    /
                    100
                )


            # ------------------------------------------------
            # CONSUMIDO
            # ------------------------------------------------

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
                    -
                    resultado[
                        "restante"
                    ]
                )


            return resultado


        # ----------------------------------------------------
        # VALOR ESPECIAL / DESCONHECIDO
        # ----------------------------------------------------

        if nivel_num is not None:

            if nivel_num < 0:

                if (
                    resultado.get(
                        "percentual"
                    )
                    is None
                ):

                    resultado[
                        "percentual"
                    ] = None

                resultado[
                    "nivel"
                ] = None


        return resultado


    # ========================================================
    # SNMP
    # ========================================================

    async def coletar_snmp(
        self,
    ):

        # ----------------------------------------------------
        # 1. IDENTIFICAÇÃO DIRETA DO EQUIPAMENTO VIA SNMP
        # ----------------------------------------------------
        # Consulta modelo, serial e contador pelas MIBs padrão e Lexmark.
        # Funciona mesmo que a impressora esteja sem toner, sem fotocondutor ou sem papel.
        try:
            ident_snmp = await coletar_identificacao_snmp(self.ip)
            if isinstance(ident_snmp, dict) and ident_snmp.get("ativo"):
                self.conectividade["snmp"] = True
                self.normalizar_identificacao(ident_snmp, "SNMP")
                if ident_snmp.get("modelo"):
                    print(f"[DEVICE] Modelo identificado via SNMP: {ident_snmp['modelo']}")
                if ident_snmp.get("serial"):
                    print(f"[DEVICE] Serial identificado via SNMP: {ident_snmp['serial']}")
        except Exception as erro_ident:
            print(f"[DEVICE] Aviso identificação SNMP: {erro_ident}")

        print(
            "[DEVICE] Consultando suprimentos via SNMP..."
        )


        try:

            # ------------------------------------------------
            # Primeiro tenta preservar o comportamento atual.
            #
            # coletar_supplies() é tratado como coroutine
            # quando o módulo SNMP atual assim define.
            # ------------------------------------------------

            resultado = coletar_supplies(
                self.ip
            )


            if inspect.isawaitable(
                resultado
            ):

                dados = await asyncio.wait_for(
                    resultado,
                    timeout=TIMEOUT_SNMP,
                )

            else:

                # Compatibilidade caso coletar_supplies()
                # seja alterado para função síncrona no futuro.

                dados = await self.executar_com_timeout(
                    lambda: resultado,
                    TIMEOUT_SNMP,
                    "SNMP",
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


        if not isinstance(
            dados,
            (list, tuple),
        ):

            print(
                "[DEVICE] SNMP retornou formato "
                "de suprimentos inválido."
            )

            return self.supplies


        novos_supplies = []


        for supply in dados:

            if not isinstance(
                supply,
                dict,
            ):

                continue


            supply_normalizado = (
                self.normalizar_supply_snmp(
                    supply
                )
            )


            if supply_normalizado is None:

                continue


            supply = (
                supply_normalizado
            )


            # ------------------------------------------------
            # FILTRO DOS CONSUMÍVEIS PADRÃO
            # ------------------------------------------------
            #
            # A interface trabalha somente com:
            #
            #   toner
            #   unidade de imagem
            #   fusor
            #
            # Itens auxiliares retornados pelo SNMP, como:
            #
            #   ADF Kit
            #   Roller Kit
            #   Staples
            #   Hole Punch
            #
            # não fazem parte da lista de consumíveis
            # apresentada pelo Printer Assistant.
            #
            # Valores quantitativos dos itens aceitos não são
            # modificados aqui.
            #

            tipo_supply = (
                self.tipo_consumivel(
                    supply
                )
            )

            if tipo_supply not in (
                "toner",
                "unidade_imagem",
                "fusor",
            ):

                continue


            # ------------------------------------------------
            # SERIAL
            # ------------------------------------------------
            #
            # SNMP não define aqui o serial de consumível.
            #
            # O serial será associado posteriormente a partir
            # do SYSDEBUG.
            #
            # Se o SNMP eventualmente devolver um serial,
            # ele é preservado temporariamente somente se já
            # existir. A associação oficial continua sendo
            # feita pelo SYSDEBUG.
            #

            supply[
                "numero_serie"
            ] = None


            # ------------------------------------------------
            # FUSOR
            # ------------------------------------------------

            if (
                tipo_supply
                ==
                "fusor"
            ):

                supply[
                    "numero_serie"
                ] = None


            novos_supplies.append(
                supply
            )


        # ----------------------------------------------------
        # ORDEM PADRÃO
        # ----------------------------------------------------
        #
        # Toner
        # Unidade de imagem
        # Fusor
        #

        self.supplies = (
            self.ordenar_supplies(
                novos_supplies
            )
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


        # ----------------------------------------------------
        # ORDEM FINAL DOS CONSUMÍVEIS
        # ----------------------------------------------------
        #
        # Garante a ordem padrão mesmo depois da associação
        # dos seriais vindos do SYSDEBUG.
        #

        self.supplies = (
            self.ordenar_supplies(
                self.supplies
            )
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

            "sysdebug_filtered":
                (
                    self.sysdebug_filtered.copy()

                    if isinstance(
                        self.sysdebug_filtered,
                        dict,
                    )

                    else {}
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

        try:

            contador_num = int(
                float(
                    contador
                )
            )

            print(
                "Contador:",
                f"{contador_num:,}".replace(
                    ",",
                    ".",
                )
            )

        except (
            TypeError,
            ValueError,
        ):

            print(
                "Contador:",
                contador
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


        # ----------------------------------------------------
        # NÍVEL
        # ----------------------------------------------------

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
                    f"    Nível: "
                    f"{float(nivel):g} %"
                )

            except (
                TypeError,
                ValueError,
            ):

                print(
                    f"    Nível: "
                    f"{nivel} %"
                )


        # ----------------------------------------------------
        # CONDIÇÃO
        # ----------------------------------------------------

        print(
            "    Condição:",
            supply.get(
                "condicao",
                "N/D",
            )
        )


        # ----------------------------------------------------
        # CAPACIDADE
        # ----------------------------------------------------

        print(
            "    Capacidade:",
            supply.get(
                "capacidade",
                "N/D",
            )
        )


        # ----------------------------------------------------
        # RESTANTE
        # ----------------------------------------------------

        print(
            "    Restante:",
            supply.get(
                "restante",
                "N/D",
            )
        )


        # ----------------------------------------------------
        # CONSUMIDO
        # ----------------------------------------------------

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

            print(
                "    Nº série:",
                supply.get(
                    "numero_serie"
                )
                or
                "N/D"
            )


        # ----------------------------------------------------
        # GARANTIA
        # ----------------------------------------------------

        if (
            tipo_supply
            ==
            "unidade_imagem"
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