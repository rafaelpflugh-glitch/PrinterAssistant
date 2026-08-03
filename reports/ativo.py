from core.base_report import BaseReport


class ReportAtivo(BaseReport):


    title = "Relatório de Ativo"

    description = (
        "Etiqueta patrimonial da impressora "
        "com modelo, serial, código de barras "
        "e contador."
    )


    def generate(self, session):


        print()

        print("=" * 60)

        print("RELATÓRIO DE ATIVO")

        print("=" * 60)


        if session is None:

            print(
                "Nenhuma impressora ativa."
            )

            return False



        dados = session.mostrar()


        print()

        print(
            "Dados coletados:"
        )

        print(
            dados
        )


        print()

        print(
            "Gerador de etiqueta será integrado aqui."
        )


        return True