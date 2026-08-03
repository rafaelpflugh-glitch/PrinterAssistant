from core.session import criar_sessao
from modules.pjl import PJL


# ============================================================
# TESTE PJL - PRINTER ASSISTANT
# ============================================================
#
# Testa o módulo PJL usando a impressora ativa
# armazenada em session.json
#
# Fluxo:
#
# Session
#    |
#    v
# PJL Module
#    |
#    v
# Impressora TCP 9100
#
# ============================================================


def titulo(texto):

    print()
    print("=" * 70)
    print(texto)
    print("=" * 70)
    print()



def main():


    titulo(
        "TESTE PJL"
    )


    # --------------------------------------------------------
    # Carregar sessão
    # --------------------------------------------------------

    sessao = criar_sessao()


    carregou = sessao.carregar()


    if not carregou:

        print(
            "Erro carregando session.json"
        )

        return



    if not sessao.existe():

        print(
            "Nenhuma impressora ativa."
        )

        print(
            "Execute main.py primeiro."
        )

        return



    # --------------------------------------------------------
    # Mostrar impressora
    # --------------------------------------------------------

    sessao.mostrar()



    # --------------------------------------------------------
    # Criar PJL
    # --------------------------------------------------------

    print()

    print(
        "Criando módulo PJL..."
    )


    pjl = PJL(
        sessao
    )


    # --------------------------------------------------------
    # Testes
    # --------------------------------------------------------


    testes = [

        (
            "IDENTIFICAÇÃO",
            pjl.info_id
        ),

        (
            "PRODINFO",
            pjl.prodinfo
        ),

        (
            "PAGECOUNT",
            pjl.pagecount
        ),

        (
            "STATUS",
            pjl.status
        ),

        (
            "MEMORY",
            pjl.memory
        ),

    ]



    for nome, funcao in testes:


        print()

        print("-" * 70)

        print(
            nome
        )

        print("-" * 70)


        try:

            resposta = funcao()


            print(
                resposta
            )


        except Exception as erro:


            print()

            print(
                "ERRO:"
            )

            print(
                erro
            )



    titulo(
        "TESTE FINALIZADO"
    )



if __name__ == "__main__":

    main()