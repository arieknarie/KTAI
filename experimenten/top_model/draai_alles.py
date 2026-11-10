r"""Draait alle stappen van het top model achter elkaar.

Gebruik (vanuit de map experimenten):
    Mac:     .venv/bin/python top_model/draai_alles.py
    Windows: .venv\Scripts\python top_model\draai_alles.py
"""

import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
STEPS = ["stap_1_vectoren", "stap_2_afstellen", "stap_3_herkennen", "stap_4_meten_per_gezicht", "stap_5_filmpje", "stap_6_uitleg"]


def main() -> None:
    for step in STEPS:
        print(f"--- {step}", flush=True)
        subprocess.run([sys.executable, str(HERE / f"{step}.py")], check=True)


if __name__ == "__main__":
    main()
