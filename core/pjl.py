
import socket
import re


# ============================================================
# PRINTER ASSISTANT - MÓDULO PJL
# ============================================================
#
# Responsabilidade:
#
# - conectar na porta RAW 9100
# - enviar comandos PJL
# - coletar identificação
# - coletar contador
# - coletar configuração
# - extrair modelo e número de série
#
# IMPORTANTE:
# O IP NÃO é fixo.
# O endereço da impressora é informado quando a classe é criada.
#
# Também mantemos a função coletar_identificacao(ip)
# para compatibilidade com módulos antigos do projeto.
# ============================================================


PORTA_PADRAO = 9100
TIMEOUT_PADRAO = 5


# ============================================================
# CLASSE PJL
# ============================================================

class PJLPrinter:

    def __init__(
        self,
        ip,
        porta=PORTA_PADRAO,
        timeout=TIMEOUT_PADRAO
    ):

        self.ip = ip
        self.porta = porta
        self.timeout = timeout


    # ========================================================
    # ENVIO PJL
    # ========================================================

    def enviar(self, comando):

        resposta = b""

        dados = b"\033%-12345X"

        dados += comando.encode(
            "ascii",
            errors="ignore"
        )

        dados += b"\r\n"

        dados += b"\033%-12345X"

        sock = None

        try:

            sock = socket.socket(
                socket.AF_INET,
                socket.SOCK_STREAM
            )

            sock.settimeout(
                self.timeout
            )

            sock.connect(
                (
                    self.ip,
                    self.porta
                )
            )

            sock.sendall(
                dados
            )

            while True:

                try:

                    parte = sock.recv(
                        4096
                    )

                except socket.timeout:

                    break

                if not parte:

                    break

                resposta += parte

                if len(parte) < 4096:

                    break


        except Exception as erro:

            print(
                f"[PJL] Erro em {self.ip}: {erro}"
            )

            return ""


        finally:

            if sock:

                try:

                    sock.close()

                except:

                    pass


        return resposta.decode(
            "latin1",
            errors="ignore"
        )


    # ========================================================
    # TESTAR CONEXÃO
    # ========================================================

    def testar_conexao(self):

        try:

            with socket.create_connection(
                (
                    self.ip,
                    self.porta
                ),
                timeout=self.timeout
            ):

                return True


        except:

            return False


    # ========================================================
    # INFO ID
    # ========================================================

    def info_id(self):

        return self.enviar(
            "@PJL INFO ID"
        )


    # ========================================================
    # PAGECOUNT
    # ========================================================

    def pagecount(self):

        return self.enviar(
            "@PJL INFO PAGECOUNT"
        )


    # ========================================================
    # CONFIG
    # ========================================================

    def info_config(self):

        return self.enviar(
            "@PJL INFO CONFIG"
        )


    # ========================================================
    # IDENTIFICAÇÃO COMPLETA
    # ========================================================

    def coletar_identificacao(self):

        resultado = {

            "modelo": None,
            "serial": None,
            "contador": None

        }


        # ----------------------------------------------------
        # TESTA CONEXÃO
        # ----------------------------------------------------

        if not self.testar_conexao():

            return resultado


        # ----------------------------------------------------
        # COLETA PJL
        # ----------------------------------------------------

        id_resp = self.info_id()

        page_resp = self.pagecount()

        config_resp = self.info_config()


        # ====================================================
        # MODELO
        # ====================================================

        modelo = self._extrair_modelo(
            id_resp
        )

        if modelo:

            resultado["modelo"] = modelo


        # ====================================================
        # CONTADOR
        # ====================================================

        contador = self._extrair_contador(
            page_resp
        )

        if contador is not None:

            resultado["contador"] = contador


        # ====================================================
        # SERIAL
        # ====================================================

        serial = self._extrair_serial(
            config_resp
        )

        if serial:

            resultado["serial"] = serial


        return resultado


    # ========================================================
    # EXTRAIR MODELO
    # ========================================================

    @staticmethod
    def _extrair_modelo(resposta):

        if not resposta:

            return None


        padroes = [

            r'"([^"]+)"',

            r'MODEL(?:\s+NAME)?\s*=\s*"?([^"\r\n]+)',

            r'PRODUCT\s*=\s*"?([^"\r\n]+)',

            r'DESCRIPTION\s*=\s*"?([^"\r\n]+)'

        ]


        for padrao in padroes:

            resultado = re.search(
                padrao,
                resposta,
                re.IGNORECASE
            )

            if resultado:

                valor = resultado.group(1).strip()

                if valor:

                    return valor


        return None


    # ========================================================
    # EXTRAIR CONTADOR
    # ========================================================

    @staticmethod
    def _extrair_contador(resposta):

        if not resposta:

            return None


        padroes = [

            r'PAGECOUNT\s+(\d+)',

            r'PAGECOUNT\s*=\s*(\d+)',

            r'PAGE_COUNT\s*=\s*(\d+)',

            r'PAGES\s*=\s*(\d+)'

        ]


        for padrao in padroes:

            resultado = re.search(
                padrao,
                resposta,
                re.IGNORECASE
            )

            if resultado:

                try:

                    return int(
                        resultado.group(1)
                    )

                except:

                    pass


        return None


    # ========================================================
    # EXTRAIR SERIAL
    # ========================================================

    @staticmethod
    def _extrair_serial(resposta):

        if not resposta:

            return None


        padroes = [

            r'SERIAL NUMBER\s*=\s*(\S+)',

            r'SERIALNUMBER\s*=\s*(\S+)',

            r'SERIAL\s*=\s*(\S+)',

            r'SERIAL NUMBER:\s*(\S+)'

        ]


        for padrao in padroes:

            resultado = re.search(
                padrao,
                resposta,
                re.IGNORECASE
            )

            if resultado:

                valor = resultado.group(1).strip()

                if valor:

                    return valor


        return None


    # ========================================================
    # COLETA COMPLETA
    # ========================================================

    def coletar(self):

        identificacao = self.coletar_identificacao()


        conectado = (

            identificacao.get("modelo") is not None
            or identificacao.get("serial") is not None
            or identificacao.get("contador") is not None
        )


        return {

            "ip": self.ip,

            "porta": self.porta,

            "conectado": conectado,

            "modelo": identificacao.get(
                "modelo"
            ),

            "serial": identificacao.get(
                "serial"
            ),

            "contador": identificacao.get(
                "contador"
            )

        }


# ============================================================
# FUNÇÃO DE CONVENIÊNCIA
# ============================================================

def coletar_pjl(
    ip,
    porta=PORTA_PADRAO,
    timeout=TIMEOUT_PADRAO
):

    impressora = PJLPrinter(
        ip=ip,
        porta=porta,
        timeout=timeout
    )

    return impressora.coletar()


# ============================================================
# COMPATIBILIDADE COM MÓDULOS ANTIGOS
# ============================================================

def coletar_identificacao(
    ip,
    porta=PORTA_PADRAO,
    timeout=TIMEOUT_PADRAO
):

    impressora = PJLPrinter(
        ip=ip,
        porta=porta,
        timeout=timeout
    )

    return impressora.coletar_identificacao()


# ============================================================
# TESTE DIRETO
# ============================================================

if __name__ == "__main__":

    print("=" * 60)

    print(
        "PRINTER ASSISTANT - TESTE PJL"
    )

    print("=" * 60)


    ip = input(
        "\nDigite o IP da impressora: "
    ).strip()


    if not ip:

        print(
            "IP não informado."
        )

        raise SystemExit


    impressora = PJLPrinter(
        ip
    )


    print()

    print(
        f"Testando {ip}:9100..."
    )


    if not impressora.testar_conexao():

        print(
            "ERRO: não foi possível conectar na porta 9100."
        )

        raise SystemExit


    print(
        "Conexão RAW/PJL OK."
    )


    print()

    print(
        "Coletando identificação..."
    )


    dados = impressora.coletar()


    print()

    print("=" * 60)

    print(
        "RESULTADO"
    )

    print("=" * 60)


    for chave, valor in dados.items():

        print(
            f"{chave}: {valor}"
        )


    print()

