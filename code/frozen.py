"""Vastgelegde bestanden: controlegetallen (sha256) in checksums.sha256 in de map KTAI.

De labels, de controle van de tracks en de uitleg horen bij precies de vastgelegde uitkomsten in
data/tracks/ en labeling/items.json. Een nieuwe run (zeker op een andere computer of met andere
versies) kan andere gezichten en andere tracknummers geven. Daarom:

- controleren de scripts eerst of de bestanden waarmee ze werken nog de vastgelegde bestanden zijn
  (check_frozen);
- overschrijft een script een vastgelegd bestand niet als de nieuwe uitkomst anders is, maar schrijft
  het de nieuwe uitkomst ernaast als <naam>.nieuw.<ext> (write_frozen).

Het bestand checksums.sha256 wordt gemaakt met:
    .venv/bin/python code/check_setup.py --vastleggen
"""

import hashlib
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
CHECKSUMS = REPO / "checksums.sha256"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def frozen() -> dict:
    """{pad ten opzichte van KTAI: sha256} uit checksums.sha256 (leeg als het bestand er niet is)."""
    if not CHECKSUMS.exists():
        return {}
    pairs = (line.split(maxsplit=1) for line in CHECKSUMS.read_text(encoding="utf-8").splitlines() if line.strip())
    return {path.strip(): digest for digest, path in pairs}


def check_frozen(*relative_paths: str) -> None:
    """Stop met een duidelijke melding als een van deze bestanden niet meer het vastgelegde bestand is."""
    known = frozen()
    for relative in relative_paths:
        if relative in known and (REPO / relative).exists() and sha256(REPO / relative) != known[relative]:
            raise SystemExit(f"{relative} is niet meer het vastgelegde bestand (zie checksums.sha256). De labels en de "
                             "controle horen bij het vastgelegde bestand. Zet het vastgelegde bestand terug "
                             "(bijvoorbeeld met git checkout), of leg een bewust nieuwe versie vast met "
                             "code/check_setup.py --vastleggen.")


def write_frozen(path: Path, data: bytes, overwrite: bool = False) -> Path:
    """Schrijf `data` naar `path`. Is `path` vastgelegd en is de nieuwe inhoud anders, dan wordt `path` niet
    overschreven (tenzij overwrite) maar komt de nieuwe inhoud in <naam>.nieuw.<ext>. Geeft het pad terug
    waarin geschreven is."""
    relative = path.relative_to(REPO).as_posix()
    known = frozen()
    if relative in known and not overwrite and hashlib.sha256(data).hexdigest() != known[relative]:
        new = path.with_name(path.stem + ".nieuw" + path.suffix)
        new.write_bytes(data)
        print(f"  LET OP: {relative} is vastgelegd en de nieuwe uitkomst is anders. {relative} is niet "
              f"overschreven; de nieuwe uitkomst staat in {new.name}.")
        return new
    if not path.exists() or path.read_bytes() != data:
        path.write_bytes(data)
    return path
