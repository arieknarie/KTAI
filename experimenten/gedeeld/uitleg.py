"""De uitleg (README.md) bij de uitkomsten van één set voorbeelden, met de echte getallen uit de resultaten."""

import os

import pandas as pd

from gedeeld.meten import comma
from gedeeld.paden import EXPERIMENTEN


def number(n: int) -> str:
    return f"{int(n):,}".replace(",", ".")


def share(part: float, whole: float) -> str:
    return f"{100 * part / whole:.0f}%" if whole else "0%"


def _pct(value: float) -> str:
    return "-" if pd.isna(value) else comma(float(value), 1) + "%"


def _table(heads: list, data: pd.DataFrame, cells) -> list:
    """Een tabel met een rij per persoon; de rij met alle vier samen is vetgedrukt."""
    lines = ["| " + " | ".join(heads) + " |", "|" + "---|" * len(heads)]
    for r in data.itertuples():
        bold = "**" if r.acteur == "samen" else ""
        name = "alle vier samen" if r.acteur == "samen" else r.acteur
        lines.append("| " + " | ".join(f"{bold}{value}{bold}" for value in [name] + cells(r)) + " |")
    return lines


def write(out, heading: str, intro: str, settings: list, command: str, extra: str = "") -> None:
    """Schrijft README.md in de map met uitkomsten. `settings` is een lijst (naam, waarde). `command` is de opdracht om deze
    uitkomsten opnieuw te maken, met / als scheidingsteken; voor Windows worden de schuine strepen omgedraaid."""
    two = pd.read_csv(out / "methode_2_tabel.csv")
    one = pd.read_csv(out / "methode_1_tabel.csv") if (out / "methode_1_tabel.csv").exists() else None     # methode 1 staat alleen bij de basis
    total = two[two["acteur"] == "samen"].iloc[0]
    people = two[two["acteur"] != "samen"]
    best, worst = people.loc[people["f1"].idxmax()], people.loc[people["f1"].idxmin()]
    named = total["goed"] + total["fout_benoemd"]
    home = os.path.relpath(EXPERIMENTEN / "README.md", out).replace(os.sep, "/")
    lines = [f"# {heading}", "", intro, "",
             f"> **In het kort.** De score per gezicht is **{comma(total['f1'])}**. De score is een cijfer van 0 tot 1: bij 1 vindt FaceNet alle gezichten en klopt elke naam.",
             ">",
             f"> - Van de {number(total['gezichten'])} gezichten krijgen er {number(total['goed'])} de juiste naam ({share(total['goed'], total['gezichten'])}).",
             f"> - FaceNet zette {number(named)} namen in de filmpjes, en daarvan klopten er {number(total['goed'])} ({share(total['goed'], named)}).",
             f"> - Het best herkend: {best['acteur']} (score {comma(best['f1'])}). Het slechtst herkend: {worst['acteur']} (score {comma(worst['f1'])}).",
             "",
             "**Het filmpje:** [`filmpje.mp4`](filmpje.mp4) laat alle fragmenten achter elkaar zien, met een vierkantje om elk gezicht dat FaceNet als een van de vier personen herkent. "
             "Klik op GitHub op de link en daarna op *View raw* om het filmpje te downloaden.", "",
             f"Wat de woorden betekenen, staat in [de woordenlijst]({home}#woordenlijst). Hoe we meten, staat bij [Zo meten we hoe goed FaceNet is]({home}#zo-meten-we-hoe-goed-facenet-is).", "",
             "", "## De instellingen", "",
             "Dit zijn de instellingen waarmee deze uitkomsten gemaakt zijn.", "",
             "| Instelling | Waarde |", "|---|---|"]
    lines += [f"| {name} | {value} |" for name, value in settings]
    lines += ["", "![Alle voorbeeldfoto's in deze set, per persoon](voorbeelden.jpg)", "",
              "*De voorbeelden in deze set. Elk klein plaatje is precies wat FaceNet van een voorbeeld te zien krijgt.*", "",
              "", "## Methode 2: per gezicht" if one is not None else "## De score per gezicht", "",
              "Dit is de maat waarmee we FaceNet beoordelen. We weten waar elk gezicht staat. Een naam telt alleen als goed als het kader met die naam "
              "minstens 30% overlapt met het gezicht van die persoon.", "",
              "**De score per persoon.** Precisie zegt hoe vaak een naam klopt. Recall zegt hoeveel van de echte gezichten de juiste naam krijgen. De score (F1) is die twee samen.", ""]
    lines += _table(["Persoon", "Score (F1)", "Precisie", "Recall"], two, lambda r: [comma(r.f1), comma(r.precisie), comma(r.recall)])
    lines += ["", "**De aantallen.** *Goed* is een gezicht met de juiste naam. *Naam op de verkeerde plek* is een kader met een naam dat niet op het gezicht van die persoon ligt. *Gemist* is een gezicht zonder de juiste naam.", ""]
    lines += _table(["Persoon", "Gezichten", "Goed", "Naam op de verkeerde plek", "Gemist"], two, lambda r: [number(r.gezichten), number(r.goed), number(r.fout_benoemd), number(r.gemist)])
    lines += ["", "**Waarom een gezicht gemist wordt.** Soms heeft de detector op die plek geen kader gevonden. Soms is er wel een kader, maar geeft FaceNet geen naam of een andere naam.", ""]
    lines += _table(["Persoon", "Geen kader", "Wel kader, geen naam", "Wel kader, andere naam"], two, lambda r: [number(r.geen_kader), number(r.geen_naam), number(r.andere_naam)])
    lines += ["", "![Per kader: wie het echt is tegen de naam die FaceNet geeft](methode_2_verwarring.png)", "",
              "*Zo lees je dit plaatje: elke rij is wie het echt is, elke kolom is de naam die FaceNet geeft. Bij een goed resultaat staan de hoge percentages op de schuine lijn van linksboven naar rechtsonder. "
              "De onderste rij zijn kaders die op geen van de vier personen liggen: figuranten en dingen die geen gezicht zijn. Daar hoort alles in de laatste kolom te staan.*", ""]
    lines += ["![Tijdlijn per gezicht: wanneer elke persoon echt in beeld is, en wanneer FaceNet de naam goed of op een verkeerde plek zet](methode_2_tijdlijn.png)", "",
              "*Zo lees je dit plaatje: elke regel is een persoon, en van links naar rechts loopt de tijd in het filmpje. Zwart is wanneer de persoon echt in beeld is. Groen is wanneer FaceNet de juiste naam op het gezicht van die persoon zet. "
              "Rood is wanneer FaceNet die naam op een verkeerde plek zet. Hoe meer groen gelijk loopt met zwart en hoe minder rood er is, hoe beter.*", ""]
    if extra:
        lines += [extra, ""]
    if one is not None:
        lines += ["", "## Methode 1: per beeld", "",
                  "Deze maat staat in de opdracht, maar is te gunstig: een naam op het verkeerde gezicht telt ook als goed. Daarom laten we deze maat alleen bij de basis zien. We weten wie er in elk beeld te zien is, en tellen per persoon in hoeveel beelden FaceNet die persoon ziet. Waar in het beeld FaceNet de persoon ziet, maakt niet uit.", ""]
        lines += _table(["Persoon", "Score (F1)", "Precisie", "Recall"], one, lambda r: [comma(r.f1), comma(r.precisie), comma(r.recall)])
        lines += ["", "**De aantallen.** De *foutmarge* zegt hoeveel procent het aantal beelden van FaceNet afwijkt van het echte aantal beelden. *Goed* is een beeld waarin FaceNet de persoon terecht ziet, *fout* een beeld waarin FaceNet de persoon ten onrechte ziet, en *gemist* een beeld waarin de persoon wel staat maar FaceNet de persoon niet ziet.", ""]
        lines += _table(["Persoon", "Echt in beeld", "FaceNet ziet", "Foutmarge", "Goed", "Fout", "Gemist"], one,
                        lambda r: [number(r.ground_truth), number(r.ai_voorspelling), _pct(r.foutmarge_procent), number(r.goed), number(r.fout), number(r.gemist)])
        lines += ["", "![Tijdlijn: wanneer elke persoon te zien is, volgens de ground truth en volgens FaceNet](methode_1_tijdlijn.png)", "",
                  "*Zo lees je dit plaatje: elke regel is een persoon, en van links naar rechts loopt de tijd in het filmpje. Zwart is wanneer de persoon echt in beeld is, rood is wanneer FaceNet de persoon ziet. "
                  "Lopen zwart en rood gelijk, dan klopt het. Rood zonder zwart betekent dat FaceNet de persoon ten onrechte ziet, en zwart zonder rood dat FaceNet de persoon mist.*", ""]
    lines += ["", "## De bestanden in deze map", "",
              "| Bestand | Wat erin staat |", "|---|---|",
              "| `voorspellingen.csv` | Elk kader op een regel: wie FaceNet zegt dat het is (`facenet`), de persoon die het dichtstbij is (`dichtstbij`), de afstand (`afstand`) en de voorbeeldfoto die het meest op het kader lijkt (`foto`). |",
              "| `gebruik_per_foto.csv` | Per voorbeeldfoto hoe vaak die foto het meest op een kader leek, en hoe vaak de naam dan goed of fout was. |",
              "| `voorbeelden.csv`, `voorbeelden.jpg` | De voorbeelden in deze set. |" if (out / "voorbeelden.csv").exists() else "| `voorbeelden.jpg` | De voorbeelden in deze set. |",
              ] + (["| `methode_1_tabel.csv`, `methode_1_tabel.png`, `methode_1_tijdlijn.png` | De uitkomst van methode 1. |"] if one is not None else []) + [
              "| `methode_2_tabel.csv`, `methode_2_tabel.png`, `methode_2_tijdlijn.png` | De uitkomst per gezicht. |",
              "| `methode_2_verwarring.csv`, `methode_2_verwarring.png` | Per kader wie het echt is tegen de naam van FaceNet. |",
              "| `methode_2_overlap.csv` | De uitkomst van methode 2 als de grens voor de overlap anders is. |",
              "| `filmpje.mp4` | Het filmpje met de namen van FaceNet. |", "",
              "", "## Zo maak je dit opnieuw", "",
              f"Doe dit vanuit de map `experimenten`. Installeren hoeft één keer, zie [Installeren op Mac en Windows]({home}#installeren-op-mac-en-windows).", "",
              "Op een Mac:", "", "```bash", f".venv/bin/python {command}", "```", "",
              "Op Windows:", "", "```bat", ".venv\\Scripts\\python " + command.replace("/", "\\"), "```", ""]
    (out / "README.md").write_bytes("\n".join(lines).encode("utf-8"))
