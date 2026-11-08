"""De uitleg (README.md) bij de uitkomsten van één set voorbeelden, met de echte getallen uit de resultaten."""

import pandas as pd

from gedeeld.meten import comma


def number(n: int) -> str:
    return f"{int(n):,}".replace(",", ".")


def _pct(value: float) -> str:
    return "-" if pd.isna(value) else comma(float(value), 1) + "%"


def write(out, heading: str, intro: str, settings: list, command: str, extra: str = "") -> None:
    """Schrijft README.md in de map met uitkomsten. `settings` is een lijst (naam, waarde). `command` is de opdracht om deze
    uitkomsten opnieuw te maken, met / als scheidingsteken; voor Windows worden de schuine strepen omgedraaid."""
    one, two = pd.read_csv(out / "methode_1_tabel.csv"), pd.read_csv(out / "methode_2_tabel.csv")
    lines = [f"# {heading}", "", intro, "", "## De instellingen", "", "| Instelling | Waarde |", "|---|---|"]
    lines += [f"| {name} | {value} |" for name, value in settings]
    lines += ["", "## Methode 1: per beeld", "",
              "We weten wie er in elk beeld te zien is, en tellen per persoon in hoeveel beelden FaceNet die persoon ziet. "
              "*Goed* is een beeld waarin FaceNet de persoon terecht ziet, *fout* een beeld waarin FaceNet de persoon ten "
              "onrechte ziet, en *gemist* een beeld waarin de persoon wel staat maar FaceNet de persoon niet ziet. Waar in het "
              "beeld FaceNet de persoon ziet, maakt bij deze methode niet uit.", "",
              "| Acteur | Ground truth (beelden) | FaceNet (beelden) | Foutmarge | Goed | Fout | Gemist | Precisie | Recall | F1 |",
              "|---|---|---|---|---|---|---|---|---|---|"]
    for r in one.itertuples():
        bold = "**" if r.acteur == "samen" else ""
        lines.append(f"| {bold}{r.acteur}{bold} | {number(r.ground_truth)} | {number(r.ai_voorspelling)} | {_pct(r.foutmarge_procent)} | "
                     f"{number(r.goed)} | {number(r.fout)} | {number(r.gemist)} | {comma(r.precisie)} | {comma(r.recall)} | {bold}{comma(r.f1)}{bold} |")
    lines += ["", "![Tijdlijn: wanneer elke acteur te zien is, volgens de ground truth en volgens FaceNet](methode_1_tijdlijn.png)", "",
              "## Methode 2: per gezicht", "",
              "We weten ook waar elk gezicht staat. Een naam van FaceNet telt alleen als goed als het kader met die naam minstens "
              "30% overlapt met het kader van die persoon in de ground truth. *Gemist* is verdeeld in: geen kader van de detector "
              "op die plek, wel een kader maar geen naam, of wel een kader maar een andere naam.", "",
              "| Acteur | Gezichten | Goed | Fout benoemd | Gemist | waarvan geen kader | waarvan geen naam | waarvan andere naam | Precisie | Recall | F1 |",
              "|---|---|---|---|---|---|---|---|---|---|---|"]
    for r in two.itertuples():
        bold = "**" if r.acteur == "samen" else ""
        lines.append(f"| {bold}{r.acteur}{bold} | {number(r.gezichten)} | {number(r.goed)} | {number(r.fout_benoemd)} | {number(r.gemist)} | "
                     f"{number(r.geen_kader)} | {number(r.geen_naam)} | {number(r.andere_naam)} | {comma(r.precisie)} | {comma(r.recall)} | {bold}{comma(r.f1)}{bold} |")
    lines += ["", "![Per kader: wie het echt is tegen de naam die FaceNet geeft](methode_2_verwarring.png)", ""]
    if extra:
        lines += [extra, ""]
    lines += ["## Het filmpje", "",
              "[`filmpje.mp4`](filmpje.mp4) is alle filmpjes achter elkaar, met een vierkantje om elk gezicht dat FaceNet als een van "
              "de vier personen herkent, en de naam erbij.", "",
              "## De bestanden in deze map", "",
              "| Bestand | Wat erin staat |", "|---|---|",
              "| `voorspellingen.csv` | Per kader wie FaceNet zegt dat het is (`facenet`), de dichtstbijzijnde persoon (`dichtstbij`), de afstand (`afstand`) en de voorbeeldfoto die de doorslag gaf (`foto`). |",
              "| `gebruik_per_foto.csv` | Per voorbeeldfoto hoe vaak die foto de doorslag gaf, en hoe vaak dat goed of fout was. |",
              "| `methode_1_tabel.csv`, `methode_1_tabel.png`, `methode_1_tijdlijn.png` | De uitkomst van methode 1. |",
              "| `methode_2_tabel.csv`, `methode_2_tabel.png` | De uitkomst van methode 2. |",
              "| `methode_2_verwarring.csv`, `methode_2_verwarring.png` | Per kader wie het echt is tegen de naam van FaceNet. |",
              "| `methode_2_overlap.csv` | De uitkomst van methode 2 bij andere grenzen voor de overlap. |",
              "| `filmpje.mp4` | Het filmpje. |", "",
              "## Zo maak je dit opnieuw", "",
              "Vanuit de map `experimenten` (installeren: zie [de uitleg over alle experimenten](" + "../" * (len(out.relative_to(out.parents[2]).parts)) + "README.md)).", "",
              "Op een Mac:", "", "```bash", f".venv/bin/python {command}", "```", "",
              "Op Windows:", "", "```bat", ".venv\\Scripts\\python " + command.replace("/", "\\"), "```", ""]
    (out / "README.md").write_bytes("\n".join(lines).encode("utf-8"))
