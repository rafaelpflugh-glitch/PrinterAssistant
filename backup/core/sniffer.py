import requests
from bs4 import BeautifulSoup


class FormSniffer:


    def __init__(self, ip):

        self.ip = ip



    def analisar(self, endpoint):


        url = f"http://{self.ip}{endpoint}"


        print()

        print(
            f"Lendo {url}"
        )


        r = requests.get(
            url,
            timeout=10
        )


        if r.status_code != 200:

            print(
                "Erro:",
                r.status_code
            )

            return []



        soup = BeautifulSoup(
            r.text,
            "html.parser"
        )


        formularios = []



        for form in soup.find_all("form"):


            dados = {


                "pagina": endpoint,


                "action": form.get("action"),


                "method": form.get(
                    "method",
                    "GET"
                ).upper(),


                "inputs": [],


                "hidden": [],


                "buttons": [],


                "selects": []


            }



            for inp in form.find_all("input"):


                item = {


                    "type": inp.get("type"),


                    "name": inp.get("name"),


                    "value": inp.get("value")


                }


                dados["inputs"].append(item)



                if inp.get("type") == "hidden":

                    dados["hidden"].append(item)




            for button in form.find_all(
                ["button","input"]
            ):


                tipo = button.get("type")


                if tipo in [
                    "submit",
                    "button"
                ]:


                    dados["buttons"].append({


                        "name":
                            button.get("name"),


                        "value":
                            button.get("value"),


                        "text":
                            button.text.strip()


                    })




            for select in form.find_all(
                "select"
            ):


                opcoes=[]


                for option in select.find_all(
                    "option"
                ):


                    opcoes.append({


                        "value":
                            option.get("value"),


                        "text":
                            option.text.strip()


                    })



                dados["selects"].append({


                    "name":
                        select.get("name"),


                    "options":
                        opcoes


                })




            formularios.append(
                dados
            )



        return formularios