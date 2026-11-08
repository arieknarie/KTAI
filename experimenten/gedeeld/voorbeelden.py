"""De voorbeeldfoto's: welke gezichten FaceNet als voorbeeld van de vier personen krijgt.

De gewone foto's staan in labelen/invoer/pictures/personal/. Het gezicht is het kader uit automatic_labels.csv (foto's met
één gezicht; de mapnaam is de persoon), of bij de twee foto's met meer mensen het kader uit de ground truth van het
labelen. De stills (beelden uit de film, met de personen in kostuum) staan in labelen/invoer/pictures/inCharacter/; de
gezichten daarop komen uit de ground truth. De drie stills die (bijna) een beeld uit een van de filmpjes zijn (kolom
uit_video in stills_index.csv) doen niet mee: een beeld uit de video mag geen voorbeeld zijn.
"""

import cv2
import numpy as np
import pandas as pd

from gedeeld.paden import AUTOMATIC_LABELS, GROUND_TRUTH_PHOTOS, NAMES, PERSONS, STILLS_INDEX

COLUMNS = ["persoon", "bestand", "x", "y", "w", "h"]


def rows(example_set: str) -> pd.DataFrame:
    """Per voorbeeld de persoon, het bestand (ten opzichte van labelen/invoer/) en het kader."""
    auto = pd.read_csv(AUTOMATIC_LABELS)
    truth = pd.read_csv(GROUND_TRUTH_PHOTOS)
    photos = truth[truth["item"].str.startswith("photo:")]
    found = []
    if example_set in ("fotos", "fotos_en_kostuum"):
        found.append(auto.assign(persoon=auto["label"].map(PERSONS), bestand=auto["source"])[COLUMNS])
        found.append(photos.assign(bestand=photos["item"].str.removeprefix("photo:"))[COLUMNS])
    if example_set in ("fotos_en_kostuum", "alleen_kostuum"):
        stills = pd.read_csv(STILLS_INDEX).set_index("still")
        faces = truth[truth["item"].str.startswith("still:")].copy()
        names = faces["item"].str.removeprefix("still:")
        faces["bestand"] = stills.loc[names, "bestand"].to_numpy()
        found.append(faces[stills.loc[names, "uit_video"].isna().to_numpy()][COLUMNS])
    return pd.concat(found, ignore_index=True)


def sheet(table: pd.DataFrame, faces: list, path) -> None:
    """Alle voorbeelden als kleine plaatjes, per persoon op een eigen regel."""
    tile, per_row, lines = 96, 14, []
    for person in NAMES:
        chosen = [cv2.resize(face, (tile, tile), interpolation=cv2.INTER_AREA)
                  for face, name in zip(faces, table["persoon"]) if name == person]
        bar = np.full((26, tile * per_row, 3), 255, np.uint8)
        cv2.putText(bar, f"{person}: {len(chosen)} voorbeelden", (4, 19), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 0, 0), 1, cv2.LINE_AA)
        lines.append(bar)
        for i in range(0, len(chosen), per_row):
            part = chosen[i:i + per_row]
            lines.append(np.hstack(part + [np.full((tile, tile, 3), 255, np.uint8)] * (per_row - len(part))))
    ok, data = cv2.imencode(".jpg", np.vstack(lines), [cv2.IMWRITE_JPEG_QUALITY, 88])
    path.write_bytes(data.tobytes())
