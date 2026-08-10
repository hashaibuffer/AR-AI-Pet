import subprocess
import time
from pathlib import Path


def main() -> None:
    artifact = Path(__file__).parent
    python = r"D:\Espressif\python_env\idf5.5_py3.11_env\Scripts\python.exe"
    subprocess.run(
        [python, "-m", "esptool", "--port", "COM7", "--after", "hard_reset", "chip_id"],
        check=True,
        timeout=30,
    )
    time.sleep(0.2)
    log = artifact / "boot_serial.log"
    with log.open("wb") as out:
        reader = subprocess.Popen(
            [python, str(artifact / "camera_serial_reader.py"), "COM7", "18"],
            stdout=out,
            stderr=subprocess.STDOUT,
        )
        reader.wait(timeout=22)
    print(log)


if __name__ == "__main__":
    main()
