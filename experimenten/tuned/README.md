# Tuned: FaceNet zo goed mogelijk afgesteld

In de [basis](../basis/README.md) staat FaceNet standaard ingesteld. In dit experiment zoeken we de **best mogelijke instellingen**, en doen we daarna precies hetzelfde als bij de basis: dezelfde twee meetmethodes, een map `resultaten`, een filmpje en een uitleg. Ook dit is gedaan voor twee sets voorbeeldfoto's:

- [Alleen foto's](resultaten/fotos/README.md)
- [Foto's + stills in kostuum](resultaten/fotos_en_kostuum/README.md)

![De tijdlijn met de best afgestelde FaceNet: de ground truth en FaceNet liggen dicht bij elkaar](resultaten/fotos_en_kostuum/methode_1_tijdlijn.png)

*De tijdlijn met de best afgestelde FaceNet (foto's + stills). Zwart is de ground truth, rood is FaceNet.*


## Wat we doen, in het kort

| Stap | Wat er gebeurt | Code |
|---|---|---|
| 1 | FaceNet maakt van elk kader en elk voorbeeld een vector, voor elk model en elke manier van uitsnijden. | [`stap_1_vectoren.py`](stap_1_vectoren.py) |
| 2 | Afstellen: alle combinaties van instellingen worden geprobeerd, en de beste wint. | [`stap_2_afstellen.py`](stap_2_afstellen.py) |
| 3 | Herkennen met de beste instellingen. | [`stap_3_herkennen.py`](stap_3_herkennen.py) |
| 4 | Meten met methode 1 (per beeld). | [`stap_4_methode_1_per_beeld.py`](stap_4_methode_1_per_beeld.py) |
| 5 | Meten met methode 2 (per gezicht). | [`stap_5_methode_2_per_gezicht.py`](stap_5_methode_2_per_gezicht.py) |
| 6 | Het filmpje. | [`stap_6_filmpje.py`](stap_6_filmpje.py) |
| 7 | De uitleg bij de uitkomsten, met de echte getallen. | [`stap_7_uitleg.py`](stap_7_uitleg.py) |

De twee meetmethodes zijn dezelfde als bij de basis, met dezelfde code ([`../gedeeld/meten.py`](../gedeeld/meten.py)). Wat ze meten en waarom, staat in [de uitleg van de basis](../basis/README.md#de-twee-meetmethodes).


## Hoe we afgesteld hebben

We proberen alle combinaties van de instellingen hieronder: 384 combinaties per set voorbeelden, elk met 200 drempels. De instellingen staan in [`instellingen.py`](instellingen.py). De winnaar is de combinatie met de hoogste F1 volgens **methode 2 (per gezicht)**, onze keuze voor de beste maat.

| Instelling | Wat we proberen | Wat het betekent |
|---|---|---|
| Model | Facenet, Facenet512 | 128 of 512 getallen per gezicht |
| Marge | 0%, 10%, 20%, 30% | hoeveel extra ruimte om het kader FaceNet te zien krijgt |
| Lichter maken | nee, ja | een donker gezicht eerst lichter maken (factor 1 tot 5), net als *Beeld lichter* in de labelapp |
| Afstand | genormaliseerde Euclidische afstand, cosinusafstand, Euclidische afstand | de drie afstanden van deepface |
| Per persoon | meest gelijkende foto, gemiddelde van de foto's | waarmee een kader vergeleken wordt |
| Toewijzen | elk kader los, per beeld elke persoon hoogstens één keer | of dezelfde naam twee keer in een beeld mag staan |
| Beslissen | per kader, per track | per track krijgt elk kader de gemiddelde afstand van de hele track, dus één naam voor de hele track |
| Drempel | 200 waarden | vanaf welke afstand een kader *iemand anders* is |

**Een eerlijke schatting.** De winnaar is gekozen op dezelfde beelden als waarop we meten, en dan is de score te gunstig. Daarom rekenen we ook een eerlijke schatting uit: voor elk filmpje kiezen we de beste instelling op de andere zeven filmpjes, en meten we op dat ene filmpje (*leave-one-fragment-out*). Die F1 staat hieronder als *eerlijke schatting*.

![De beste F1 per keuze bij het afstellen, met foto's en stills](resultaten/fotos_en_kostuum/afstellen_per_instelling.png)

*Per instelling de beste F1 per keuze (foto's + stills). Hoe groter het verschil, hoe belangrijker die instelling.*


## De beste instellingen

| Instelling | Alleen foto's | Foto's + stills |
|---|---|---|
| Model | Facenet | Facenet512 |
| Marge | 20% | 20% |
| Lichter maken | ja | ja |
| Afstand | genormaliseerde Euclidische afstand | genormaliseerde Euclidische afstand |
| Per persoon | meest gelijkende foto | gemiddelde van de foto's |
| Toewijzen | per beeld elke persoon één keer | per beeld elke persoon één keer |
| Beslissen | per track | per track |
| Drempel | 1,0684 | 1,1076 |

**Wat het meeste helpt** (de beste F1 met en zonder die keuze, foto's + stills):

| Keuze | Met | Zonder |
|---|---|---|
| Donkere gezichten lichter maken | 0,874 | 0,775 |
| Per persoon het gemiddelde van de foto's | 0,874 | 0,773 |
| Beslissen per track | 0,874 | 0,816 |
| 20% extra ruimte om het kader | 0,874 | 0,801 (geen extra ruimte) |

Lichter maken en per track beslissen helpen in beide sets. Dat past bij deze film: de scènes zijn donker, en over een hele track heen is er meer informatie dan in één beeld. Bij één gemiddelde vector zagen we in [dat experiment](../gemiddelde_vector/README.md) dat die bij de standaarddrempel juist slechter werkt; met een eigen drempel wint de gemiddelde vector wel bij foto's + stills.


## De uitkomsten

| Experiment | Methode 1: precisie | recall | **F1** | Methode 2: precisie | recall | **F1** | Eerlijke schatting (methode 2) |
|---|---|---|---|---|---|---|---|
| Basis, foto's | 0,986 | 0,041 | **0,078** | 0,929 | 0,038 | **0,074** | |
| **Tuned, foto's** | 0,948 | 0,736 | **0,829** | 0,924 | 0,718 | **0,808** | 0,766 |
| Basis, foto's + stills | 0,645 | 0,626 | **0,636** | 0,251 | 0,398 | **0,308** | |
| **Tuned, foto's + stills** | 0,972 | 0,825 | **0,893** | 0,952 | 0,807 | **0,874** | 0,834 |

![Per kader: wie het echt is tegen de naam van FaceNet, met de best afgestelde FaceNet](resultaten/fotos_en_kostuum/methode_2_verwarring.png)

Per filmpje (F1 met methode 2). *Algemeen beste* is de winnaar over alle filmpjes, *eerlijke schatting* is de instelling die op de andere filmpjes gekozen is, en *beste voor dit filmpje* is de instelling die alleen op dat filmpje het best werkt (`beste_per_filmpje.csv`):

| Filmpje | Foto's: algemeen beste | eerlijke schatting | beste voor dit filmpje | Foto's + stills: algemeen beste | eerlijke schatting | beste voor dit filmpje |
|---|---|---|---|---|---|---|
| Video 1 | 0,797 | 0,721 | 0,872 | 0,856 | 0,856 | 0,887 |
| Video 2 | 0,838 | 0,711 | 0,850 | 0,871 | 0,871 | 0,892 |
| Video 3 | 0,968 | 0,946 | 0,969 | 0,924 | 0,638 | 0,971 |
| Video 4 | 0,972 | 0,972 | 0,997 | 0,997 | 0,997 | 0,997 |
| Video 5 | 0,716 | 0,716 | 0,900 | 0,957 | 0,957 | 0,974 |
| Video 6 | 0,788 | 0,469 | 0,852 | 0,839 | 0,839 | 0,855 |
| Video 7 | 0,818 | 0,818 | 0,860 | 0,850 | 0,850 | 0,863 |
| Video 8 | 0,414 | 0,414 | 0,572 | 0,655 | 0,588 | 0,671 |

**Wat dit betekent.**

- **Afstellen maakt het verschil.** Per gezicht gaat de F1 van 0,308 naar 0,874 met foto's + stills, en van 0,074 naar 0,808 met alleen foto's. Ook de eerlijke schattingen blijven hoog (0,834 en 0,766).
- **Foto's + stills blijft het beste**, maar met goede instellingen komen de gewone foto's al een heel eind.
- **Johann blijft het moeilijkst** (F1 per gezicht 0,374): Johann is veruit het minst in beeld, en de herkenning mist Johann vaak. Ook **Video 8** blijft het zwakst; daar wisselt het beeld heel vaak.

Let op: bij *per track beslissen* gebruiken we de tracks uit het labelen. Die zijn automatisch gemaakt, maar 44 tracks zijn bij het controleren met de hand geknipt.


## De filmpjes

- [Alleen foto's](resultaten/fotos/filmpje.mp4)
- [Foto's + stills in kostuum](resultaten/fotos_en_kostuum/filmpje.mp4)


## Zo draai je het op een Mac en op Windows

Doe dit vanuit de map `experimenten`. Installeren hoeft één keer, zie [de uitleg over alle experimenten](../README.md#installeren-op-mac-en-windows). Voor de filmpjes is ook ffmpeg nodig (Mac: `brew install ffmpeg`, Windows: `winget install Gyan.FFmpeg`).

Op een Mac:

```bash
.venv/bin/python tuned/draai_alles.py
```

Op Windows:

```bat
.venv\Scripts\python tuned\draai_alles.py
```

Dit draait alle stappen voor beide sets (met `--voorbeelden fotos` of `--voorbeelden fotos_en_kostuum` erachter alleen die set). Stap 1 duurt ongeveer een uur; de vectoren worden bewaard in `tussenbestanden/` (gaat niet mee naar GitHub), dus daarna duurt alles nog een paar minuten.
