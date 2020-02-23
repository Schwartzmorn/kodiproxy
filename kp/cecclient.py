import subprocess


class CECClient:
    """Very basic class to switch on and off the projector"""

    def pipe(self, cmd: str):
        process = subprocess.Popen(
            ['cec-client', '-s', '-d', '1'], stdin=subprocess.PIPE)
        process.communicate(bytes(cmd, 'ascii'))

    def switch_on(self) -> None:
        self.pipe('on 0')

    def switch_off(self) -> None:
        self.pipe('standby 0')
