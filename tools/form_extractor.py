import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin


def extrair_forms(url):

    print("=" * 60)
    print("EXTRAINDO FORMULARIOS")
    print("=" * 60)
    print(url)

    try:
        r = requests.get(
            url,
            timeout=10
        )

    except Exception as e:
        print("ERRO:", e)
        return []


    html = r.text

    soup = BeautifulSoup(
        html,
        "html.parser"
    )

    encontrados = []


    # procura tags form normais

    forms = soup.find_all(
        "form"
    )


    for form in forms:

        dados = {}


        dados["action"] = urljoin(
            url,
            form.get(
                "action",
                ""
            )
        )


        dados["method"] = form.get(
            "method",
            "GET"
        ).upper()



        campos = []


        for campo in form.find_all(
            [
                "input",
                "select",
                "textarea",
                "button"
            ]
        ):

            nome = campo.get(
                "name"
            )


            if nome:


                campo_info = {

                    "nome": nome,

                    "tipo": campo.get(
                        "type",
                        campo.name
                    ),

                    "valor": campo.get(
                        "value",
                        ""
                    )
                }



                # captura opções de SELECT

                if campo.name == "select":

                    opcoes = []


                    for opt in campo.find_all(
                        "option"
                    ):

                        opcoes.append(
                            {
                                "valor":
                                    opt.get(
                                        "value"
                                    ),

                                "texto":
                                    opt.text.strip()
                            }
                        )


                    campo_info["opcoes"] = opcoes



                campos.append(
                    campo_info
                )



        dados["campos"] = campos



        # captura scripts da página

        scripts = soup.find_all(
            "script"
        )

        js = []


        for script in scripts:

            if script.text.strip():

                js.append(
                    script.text.strip()
                )


        dados["scripts"] = js



        encontrados.append(
            dados
        )



    # procura também links posttest/postpf

    links = soup.find_all(
        "a",
        href=True
    )


    for link in links:

        href = link["href"]


        if (
            "post" in href.lower()
            or
            "postpf" in href.lower()
        ):

            encontrados.append(
                {
                    "action":
                        urljoin(
                            url,
                            href
                        ),

                    "method":
                        "POST",

                    "campos":
                        [],

                    "scripts":
                        []
                }
            )



    return encontrados




if __name__ == "__main__":


    url = input(
        "URL da impressora: "
    )


    forms = extrair_forms(
        url
    )


    print()


    print("=" * 60)

    print(
        "FORMULARIOS ENCONTRADOS:",
        len(forms)
    )

    print("=" * 60)



    for i, f in enumerate(
        forms,
        1
    ):

        print()

        print(
            "[FORM]",
            i
        )


        print(
            "ACTION:",
            f["action"]
        )


        print(
            "METHOD:",
            f["method"]
        )


        print(
            "\nCAMPOS:"
        )


        for c in f["campos"]:

            print(
                "   ",
                c
            )



        print()

        print(
            "SCRIPTS:"
        )


        for s in f.get(
            "scripts",
            []
        ):

            print(
                s[:500]
            )