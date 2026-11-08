r"""Draait alle stappen van de basis achter elkaar, voor beide sets voorbeelden (of alleen voor --voorbeelden <set>).

Gebruik (vanuit de map experimenten):
    Mac:     .venv/bin/python basis/draai_alles.py
    Windows: .venv\Scripts\python basis\draai_alles.py
"""

import argparse
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
STEPS = ["stap_1_voorbeelden", "stap_2_herkennen", "stap_3_methode_1_per_beeld", "stap_4_methode_2_per_gezicht", "stap_5_filmpje", "stap_6_uitleg"]


def main() -> None:
    parser = argparse.ArgumentParser(description="Alle stappen van de basis")
    parser.add_argument("--voorbeelden", choices=["fotos", "fotos_en_kostuum", "alleen_kostuum"], help="alleen deze set voorbeelden")
    args = parser.parse_args()
    for example_set in ([args.voorbeelden] if args.voorbeelden else ["fotos", "fotos_en_kostuum"]):
        for step in STEPS:
            print(f"--- {example_set}: {step}", flush=True)
            subprocess.run([sys.executable, str(HERE / f"{step}.py"), "--voorbeelden", example_set], check=True)


if __name__ == "__main__":
    main()
