import subprocess
from tkinter import messagebox

class DeployService:
    """
    Motor de instalação local de impressoras no Windows.
    Utiliza perfis pré-configurados para automatizar portas TCP/IP e vinculação de drivers.
    """

    PERFIS = {
        "AGIBANK": {
            "nome_padrao": "Agibank - Lexmark TI",
            "driver": "Lexmark Universal v2",
            "comentarios": "Instalado via Printer Assistant"
        },
        "ADMINISTRATIVO": {
            "nome_padrao": "Lexmark Administrativo",
            "driver": "Lexmark Universal v2",
            "comentarios": "Setor Administrativo interno"
        }
    }

    @staticmethod
    def instalar_impressora(ip_destino, perfil_escolhido):
        perfil = DeployService.PERFIS.get(perfil_escolhido.upper())
        if not perfil:
            raise ValueError(f"Perfil '{perfil_escolhido}' não encontrado.")

        nome = perfil["nome_padrao"]
        driver = perfil["driver"]
        porta = f"IP_{ip_destino}"

        script_ps = f"""
        try {{
            Add-PrinterPort -Name "{porta}" -PrinterHostAddress "{ip_destino}" -ErrorAction Stop
            Add-Printer -Name "{nome}" -DriverName "{driver}" -PortName "{porta}" -Comment "{perfil['comentarios']}" -ErrorAction Stop
            Write-Output "SUCESSO"
        }} catch {{
            Write-Error $_.Exception.Message
        }}
        """

        try:
            resultado = subprocess.run(
                ["powershell", "-NoProfile", "-NonInteractive", "-Command", script_ps],
                capture_output=True,
                text=True,
                creationflags=subprocess.CREATE_NO_WINDOW
            )

            if "SUCESSO" in resultado.stdout:
                return True, f"Impressora '{nome}' instalada com sucesso na porta {porta}."
            else:
                erro = resultado.stderr.strip() or resultado.stdout.strip()
                return False, f"Falha na instalação via Windows:\n{erro}"

        except Exception as e:
            return False, f"Erro ao executar PowerShell: {e}"
