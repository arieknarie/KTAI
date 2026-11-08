r"""Stap 2: herkennen. Elk gezicht in de filmpjes wordt vergeleken met de voorbeelden uit stap 1.

Invoer:  de kaders uit het labelen (labelen/output/stap_0_voorbereiding/tracks/detections_0.3.csv), de filmpjes en de
         voorbeelden uit stap 1.
Uitvoer: resultaten/<set>/voorspellingen.csv: per kader het fragment, het bestand, het beeld, de tijd, de track, het kader,
         wie FaceNet zegt dat het is (facenet), de dichtstbijzijnde persoon (dichtstbij), de afstand (afstand) en de
         voorbeeldfoto die de doorslag gaf (foto).

Van elk kader maakt FaceNet een vector. Het kader krijgt de naam van het voorbeeld met de kleinste afstand, als die afstand
kleiner is dan de drempel; anders is het "iemand anders". De vectoren van alle kaders worden één keer gemaakt en bewaard in
tussenbestanden/ (gaat niet mee naar GitHub), want ze hangen niet af van de voorbeelden.

Gebruik (vanuit de map experimenten, na stap 1):
    Mac:     .venv/bin/python basis/stap_2_herkennen.py --voorbeelden fotos
    Windows: .venv\Scripts\python basis\stap_2_herkennen.py --voorbeelden fotos
"""

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))   # zodat de map gedeeld/ gevonden wordt

from gedeeld.facenet import box_vectors, load_detections
from gedeeld.herkennen import example_distances, predictions
from gedeeld.paden import EXAMPLE_SETS
from instellingen import DREMPEL, MARGIN, METRIC, MODEL, folder


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--voorbeelden", choices=EXAMPLE_SETS, default="fotos", help="welke set voorbeeldfoto's")
    args = parser.parse_args()
    out, title = folder(args.voorbeelden), EXAMPLE_SETS[args.voorbeelden]
    examples = pd.read_csv(out / "voorbeelden.csv")
    refs = examples[[f"v{i}" for i in range(128)]].to_numpy(dtype=np.float32)
    detections = load_detections()
    boxes = box_vectors(detections, [(MODEL, MARGIN)])[(MODEL, MARGIN)]
    distance = example_distances(boxes, refs, METRIC)
    nearest = distance.argmin(axis=1)
    best = distance[np.arange(len(distance)), nearest]
    found = predictions(detections, examples["persoon"].to_numpy()[nearest], best, DREMPEL, examples["bestand"].to_numpy()[nearest])
    found.to_csv(out / "voorspellingen.csv", index=False, lineterminator="\n")
    print(f"{len(found)} kaders vergeleken met {len(refs)} voorbeelden")
    print(found["facenet"].value_counts().to_string())


if __name__ == "__main__":
    main()
