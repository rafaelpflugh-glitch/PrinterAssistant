class Routine:

    def __init__(self, nome):

        self.nome = nome
        self.etapas = []
        self.indice = 0

    # -----------------------------------------

    def adicionar(self, titulo, descricao="", espera=False):

        self.etapas.append({

            "titulo": titulo,
            "descricao": descricao,
            "espera": espera,
            "feito": False

        })

    # -----------------------------------------

    def mostrar(self):

        print()
        print("=" * 70)
        print(self.nome)
        print("=" * 70)

        for i, etapa in enumerate(self.etapas):

            status = "✓" if etapa["feito"] else " "

            print(f"[{status}] {i+1}. {etapa['titulo']}")

            if etapa["descricao"]:

                print("    ", etapa["descricao"])

        print()

    # -----------------------------------------

    def concluir(self, indice):

        self.etapas[indice]["feito"] = True

    # -----------------------------------------

    def terminou(self):

        return all(e["feito"] for e in self.etapas)