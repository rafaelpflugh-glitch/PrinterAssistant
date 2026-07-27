import ollama


# ==================================================
# HERMES - CLIENTE OLLAMA
# ==================================================

MODELO = "hermes3:latest"


def perguntar(texto):

    try:

        resposta = ollama.chat(

            model=MODELO,

            options={

                # Hermes deve ser previsível
                "temperature": 0.0,

                # Contexto maior para suportar muitas ferramentas
                "num_ctx": 4096,

                # Mais espaço para respostas
                "num_predict": 200

            },

            messages=[

                {
                    "role": "system",
                    "content": """
Você é Hermes.

Você é um agente técnico especializado em manutenção de impressoras Lexmark.

Seu trabalho é seguir exatamente as instruções recebidas.

Quando o prompt solicitar a escolha de uma ferramenta, responda SOMENTE:

ACAO:
nome_da_ferramenta

Nunca invente nomes de ferramentas.

Nunca explique antes da ação.

Nunca escreva frases como:
- Vou executar...
- Certo...
- Ok...
- Posso fazer...

Se não existir uma ferramenta apropriada, responda normalmente ao usuário.

Se existir uma ferramenta apropriada, retorne APENAS:

ACAO:
nome_da_ferramenta
"""
                },

                {
                    "role": "user",
                    "content": texto
                }

            ]

        )

        mensagem = resposta.get("message", {}).get("content", "").strip()

        if not mensagem:
            return "Erro: Hermes retornou uma resposta vazia."

        return mensagem

    except Exception as erro:

        return f"Erro no assistente IA: {erro}"