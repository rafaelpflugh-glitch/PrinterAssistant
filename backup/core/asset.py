import json
from pathlib import Path
from datetime import datetime


# ============================================================
# CONFIGURAÇÃO
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent

ASSETS_DIR = BASE_DIR / "assets"


# ============================================================
# UTILIDADES
# ============================================================

def garantir_diretorio():
    ASSETS_DIR.mkdir(
        parents=True,
        exist_ok=True
    )


def limpar_nome_arquivo(texto):
    if not texto:
        return "desconhecido"

    caracteres_invalidos = '<>:"/\\|?*'

    for caractere in caracteres_invalidos:
        texto = texto.replace(
            caractere,
            "_"
        )

    return texto.strip()


# ============================================================
# CAMINHO DO ATIVO
# ============================================================

def caminho_ativo(serial):
    garantir_diretorio()

    serial = limpar_nome_arquivo(
        serial
    )

    return ASSETS_DIR / (
        f"ativo_{serial}.json"
    )


# ============================================================
# CRIAR / ATUALIZAR ATIVO
# ============================================================

def salvar_ativo(
    identificacao,
    conectividade=None,
    supplies=None
):
    """
    Cria ou atualiza o cadastro permanente
    de uma impressora.

    O número de série é a identidade principal.
    """

    serial = identificacao.get(
        "serial"
    )

    if not serial:
        raise ValueError(
            "Número de série não informado."
        )

    caminho = caminho_ativo(
        serial
    )

    agora = datetime.now().strftime(
        "%d/%m/%Y %H:%M:%S"
    )

    # --------------------------------------------------------
    # Carregar ativo existente
    # --------------------------------------------------------

    if caminho.exists():

        with open(
            caminho,
            "r",
            encoding="utf-8"
        ) as arquivo:

            ativo = json.load(
                arquivo
            )

    else:

        ativo = {

            "ativo": {

                "criado_em": agora,

                "atualizado_em": agora,

                "identificacao": {},

                "conectividade": {},

                "historico_contador": [],

                "historico_ip": [],

                "supplies": []

            }

        }


    dados = ativo["ativo"]


    # --------------------------------------------------------
    # Identificação
    # --------------------------------------------------------

    dados["identificacao"].update({

        "fabricante":
            identificacao.get(
                "fabricante"
            ),

        "modelo":
            identificacao.get(
                "modelo"
            ),

        "familia":
            identificacao.get(
                "familia"
            ),

        "tipo":
            identificacao.get(
                "tipo"
            ),

        "serial":
            serial

    })


    # --------------------------------------------------------
    # Contador
    # --------------------------------------------------------

    contador = identificacao.get(
        "contador"
    )

    if contador is not None:

        historico = dados[
            "historico_contador"
        ]

        ultima_leitura = (
            historico[-1]["contador"]
            if historico
            else None
        )

        # Evita registrar novamente
        # o mesmo contador.

        if contador != ultima_leitura:

            registro = {

                "data": agora,

                "contador": contador

            }

            if ultima_leitura is not None:

                registro[
                    "diferenca"
                ] = contador - ultima_leitura

            else:

                registro[
                    "diferenca"
                ] = None


            historico.append(
                registro
            )


    # --------------------------------------------------------
    # Conectividade
    # --------------------------------------------------------

    if conectividade:

        dados[
            "conectividade"
        ].update(
            conectividade
        )


        ip = conectividade.get(
            "ip"
        )

        if ip:

            historico_ip = dados[
                "historico_ip"
            ]

            ultimo_ip = (
                historico_ip[-1]["ip"]
                if historico_ip
                else None
            )

            if ip != ultimo_ip:

                historico_ip.append({

                    "data": agora,

                    "ip": ip

                })


    # --------------------------------------------------------
    # Suprimentos
    # --------------------------------------------------------

    if supplies is not None:

        dados["supplies"] = supplies


    # --------------------------------------------------------
    # Atualização
    # --------------------------------------------------------

    dados["atualizado_em"] = agora


    # --------------------------------------------------------
    # Salvar
    # --------------------------------------------------------

    with open(
        caminho,
        "w",
        encoding="utf-8"
    ) as arquivo:

        json.dump(

            ativo,

            arquivo,

            indent=4,

            ensure_ascii=False

        )


    return ativo


# ============================================================
# CARREGAR ATIVO
# ============================================================

def carregar_ativo(serial):

    caminho = caminho_ativo(
        serial
    )

    if not caminho.exists():
        return None

    with open(
        caminho,
        "r",
        encoding="utf-8"
    ) as arquivo:

        return json.load(
            arquivo
        )


# ============================================================
# LISTAR ATIVOS
# ============================================================

def listar_ativos():

    garantir_diretorio()

    ativos = []

    for arquivo in ASSETS_DIR.glob(
        "ativo_*.json"
    ):

        try:

            with open(
                arquivo,
                "r",
                encoding="utf-8"
            ) as f:

                dados = json.load(f)

                ativos.append(
                    dados
                )

        except (
            json.JSONDecodeError,
            OSError
        ):

            continue


    return ativos


# ============================================================
# TESTE
# ============================================================

if __name__ == "__main__":

    print("=" * 60)

    print(
        "PRINTER ASSISTANT - TESTE DE ATIVO"
    )

    print("=" * 60)

    exemplo = {

        "fabricante":
            "Lexmark",

        "modelo":
            "MX611dhe",

        "familia":
            "MX",

        "tipo":
            "Multifuncional Laser Mono",

        "serial":
            "701644HH03ND3",

        "contador":
            137954

    }


    conectividade = {

        "ip":
            "192.168.14.134",

        "snmp":
            True,

        "pjl":
            True,

        "web":
            True,

        "raw":
            True,

        "ipp":
            True

    }


    ativo = salvar_ativo(

        exemplo,

        conectividade,

        []

    )


    print()

    print(
        "Ativo salvo com sucesso."
    )

    print()

    print(
        "Arquivo:"
    )

    print(
        caminho_ativo(
            exemplo["serial"]
        )
    )

    print()

    print(
        json.dumps(
            ativo,
            indent=4,
            ensure_ascii=False
        )
    )