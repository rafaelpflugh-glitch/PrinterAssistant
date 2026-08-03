import requests
from pathlib import Path


class Hermes:

    def __init__(self):

        self.url = "http://localhost:11434/api/generate"

        self.model = "hermes3:latest"

        self.system = Path(
            "prompts/hermes_system.txt"
        ).read_text(
            encoding="utf-8"
        )

    # ---------------------------------------------

    def ask(self, prompt):

        full_prompt = f"""

{self.system}

----------------------------

{prompt}

"""

        body = {

            "model": self.model,

            "prompt": full_prompt,

            "stream": False

        }

        r = requests.post(

            self.url,

            json=body,

            timeout=180

        )

        return r.json()["response"]