
"""
============================================================
PRINTER ASSISTANT
HTTP TOOL
============================================================

Executa requisições HTTP contra a impressora atualmente
conectada.

O IP é obtido da Session.
============================================================
"""

import requests

from core.result import ToolResult


class HTTPTool:

    name = "http"
    category = "Comunicação"
    icon = "🌐"

    description = (
        "Executa requisições HTTP na impressora."
    )

    # ========================================================
    # CONSTRUTOR
    # ========================================================

    def __init__(self):

        self.actions = {
            "get": self.get,
            "post": self.post,
        }

    # ========================================================
    # ACTIONS
    # ========================================================

    def has_action(self, action):

        return action in self.actions

    # ========================================================
    # CAPABILITIES
    # ========================================================

    def capabilities(self):

        return [
            "http_get",
            "http_post",
        ]

    # ========================================================
    # EXECUTE
    # ========================================================

    def execute(
        self,
        session,
        action,
        **kwargs
    ):

        if action not in self.actions:

            return ToolResult.erro(
                self.name,
                action,
                f"Ação HTTP '{action}' não encontrada."
            ).to_dict()

        try:

            return self.actions[action](
                session,
                **kwargs
            )

        except Exception as erro:

            return ToolResult.erro(
                self.name,
                action,
                str(erro)
            ).to_dict()

    # ========================================================
    # URL
    # ========================================================

    @staticmethod
    def montar_url(
        session,
        endpoint
    ):

        if not session:

            raise RuntimeError(
                "Sessão não disponível."
            )

        if not getattr(
            session,
            "ip",
            None
        ):

            raise RuntimeError(
                "Nenhuma impressora conectada."
            )

        if not endpoint:

            raise ValueError(
                "Endpoint não informado."
            )

        endpoint = str(
            endpoint
        ).strip()

        # ----------------------------------------------------
        # URL completa
        # ----------------------------------------------------

        if endpoint.startswith(
            "http://"
        ):

            return endpoint

        if endpoint.startswith(
            "https://"
        ):

            return endpoint

        # ----------------------------------------------------
        # Endpoint relativo
        # ----------------------------------------------------

        if not endpoint.startswith(
            "/"
        ):

            endpoint = "/" + endpoint

        return (
            f"http://{session.ip}"
            f"{endpoint}"
        )

    # ========================================================
    # GET
    # ========================================================

    def get(
        self,
        session,
        endpoint,
        timeout=15,
        **kwargs
    ):

        url = self.montar_url(
            session,
            endpoint
        )

        print()
        print("[HTTP] GET")
        print(f"[HTTP] {url}")

        resposta = requests.get(
            url,
            timeout=timeout,
            **kwargs
        )

        resultado = {

            "success":
                resposta.ok,

            "tool":
                self.name,

            "action":
                "get",

            "method":
                "GET",

            "url":
                url,

            "status_code":
                resposta.status_code,

            "content_type":
                resposta.headers.get(
                    "Content-Type"
                ),

            "headers":
                dict(
                    resposta.headers
                ),

            "text":
                resposta.text,

            "encoding":
                resposta.encoding,

        }

        if resposta.ok:

            print(
                f"[HTTP] OK - "
                f"{resposta.status_code}"
            )

        else:

            print(
                f"[HTTP] HTTP "
                f"{resposta.status_code}"
            )

        return resultado

    # ========================================================
    # POST
    # ========================================================

    def post(
        self,
        session,
        endpoint,
        timeout=15,
        **kwargs
    ):

        url = self.montar_url(
            session,
            endpoint
        )

        print()
        print("[HTTP] POST")
        print(f"[HTTP] {url}")

        resposta = requests.post(
            url,
            timeout=timeout,
            **kwargs
        )

        resultado = {

            "success":
                resposta.ok,

            "tool":
                self.name,

            "action":
                "post",

            "method":
                "POST",

            "url":
                url,

            "status_code":
                resposta.status_code,

            "content_type":
                resposta.headers.get(
                    "Content-Type"
                ),

            "headers":
                dict(
                    resposta.headers
                ),

            "text":
                resposta.text,

            "encoding":
                resposta.encoding,

        }

        if resposta.ok:

            print(
                f"[HTTP] OK - "
                f"{resposta.status_code}"
            )

        else:

            print(
                f"[HTTP] HTTP "
                f"{resposta.status_code}"
            )

        return resultado

    # ========================================================
    # INFO
    # ========================================================

    def info(self):

        return {

            "name":
                self.name,

            "category":
                self.category,

            "description":
                self.description,

            "icon":
                self.icon,

            "capabilities":
                self.capabilities(),

            "actions":
                list(
                    self.actions.keys()
                ),

        }

