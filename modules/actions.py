import asyncio
import socket
import webbrowser
import subprocess


class PrinterActions:

    def __init__(self, session):

        self.session = session

    # --------------------------------------------------

    def _ip(self):

        if not self.session.existe():

            raise Exception(
                "Nenhuma impressora ativa."
            )

        return self.session.ip

    # --------------------------------------------------

    async def abrir_web(self):

        ip = self._ip()

        url = f"http://{ip}"

        webbrowser.open(url)

        return True

    # --------------------------------------------------

    async def ping(self):

        ip = self._ip()

        processo = await asyncio.create_subprocess_exec(

            "ping",

            "-n",

            "2",

            ip,

            stdout=asyncio.subprocess.PIPE,

            stderr=asyncio.subprocess.PIPE

        )

        stdout, stderr = await processo.communicate()

        return processo.returncode == 0

    # --------------------------------------------------

    async def raw9100(self):

        ip = self._ip()

        return await asyncio.to_thread(

            self._socket,

            ip,

            9100

        )

    # --------------------------------------------------

    async def web80(self):

        ip = self._ip()

        return await asyncio.to_thread(

            self._socket,

            ip,

            80

        )

    # --------------------------------------------------

    def _socket(self, ip, porta):

        s = socket.socket()

        s.settimeout(3)

        try:

            s.connect((ip, porta))

            return True

        except:

            return False

        finally:

            s.close()

    # --------------------------------------------------

    async def pagina_teste_windows(self):

        ip = self._ip()

        print()

        print(
            "Página teste Windows ainda será implementada."
        )

        print(
            f"Destino: {ip}"
        )

        return True

    # --------------------------------------------------

    async def pagina_configuracao(self):

        print()

        print(
            "Página configuração será implementada."
        )

        return True

    # --------------------------------------------------

    async def resumo(self):

        return {

            "Ping":

                await self.ping(),

            "RAW9100":

                await self.raw9100(),

            "WEB":

                await self.web80()

        }