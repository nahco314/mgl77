import subprocess
from typing import Optional


MAIN_EXE = "./mgl77.exe"


def main():
    process: Optional[subprocess.Popen] = None

    while True:
        if process is not None and process.poll() is not None:
            process = None

        if process is None:
            process = subprocess.Popen([MAIN_EXE])


if __name__ == '__main__':
    main()
