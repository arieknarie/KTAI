# Tuned: FaceNet zo goed mogelijk afgesteld

> **De vraag.** Hoe goed kan FaceNet de vier personen herkennen met de best mogelijke instellingen?
>
> **Het antwoord.** Goed. De score per gezicht gaat van 0,074 naar **0,808** met alleen foto's, en van 0,308 naar **0,874** met foto's en stills. Dit zijn de hoogste scores op deze filmpjes. Worden de instellingen op andere filmpjes gekozen, dan is de score 0,766 en 0,834.

![Hetzelfde stukje film twee keer: links FaceNet standaard met veel rode namen, rechts FaceNet afgesteld met alleen groene namen](../fotos/basis_tegen_tuned.gif)

*Hetzelfde stukje film, links met FaceNet standaard en rechts met FaceNet afgesteld. Groen betekent dat de naam klopt, rood dat de naam niet klopt.*

Wat de woorden betekenen, staat in [de woordenlijst](../README.md#woordenlijst).

**In deze uitleg:**
[Wat we gedaan hebben](#wat-we-gedaan-hebben) ·
[Wat we afstellen](#wat-we-afstellen) ·
[Een eerlijke schatting](#een-eerlijke-schatting) ·
[De beste instellingen](#de-beste-instellingen) ·
[Wat eruit kwam](#wat-eruit-kwam) ·
[Wat dit betekent](#wat-dit-betekent) ·
[De filmpjes](#de-filmpjes) ·
[Zelf draaien](#zo-draai-je-het-op-een-mac-en-op-windows)


## Wat we gedaan hebben

In de [basis](../basis/README.md) staat FaceNet standaard ingesteld. Hier zoeken we de best mogelijke instellingen, en doen we daarna hetzelfde als bij de basis: dezelfde twee meetmethodes, een map `resultaten`, een filmpje en een uitleg. Dat doen we voor twee sets voorbeeldfoto's:

- [Alleen foto's](resultaten/fotos/README.md)
- [Foto's + stills](resultaten/fotos_en_kostuum/README.md)

| Stap | Wat er gebeurt | Script |
|---|---|---|
| 1 | FaceNet maakt van elk kader en elk voorbeeld een vector, voor elk model en elke manier van uitsnijden. | [`stap_1_vectoren.py`](stap_1_vectoren.py) |
| 2 | Afstellen: alle combinaties van instellingen worden geprobeerd, en de beste wint. | [`stap_2_afstellen.py`](stap_2_afstellen.py) |
| 3 | Herkennen met de beste instellingen. | [`stap_3_herkennen.py`](stap_3_herkennen.py) |
| 4 | Meten met methode 1 (per beeld). | [`stap_4_methode_1_per_beeld.py`](stap_4_methode_1_per_beeld.py) |
| 5 | Meten met methode 2 (per gezicht). | [`stap_5_methode_2_per_gezicht.py`](stap_5_methode_2_per_gezicht.py) |
| 6 | Het filmpje maken. | [`stap_6_filmpje.py`](stap_6_filmpje.py) |
| 7 | De uitleg bij de uitkomsten schrijven, met de echte getallen. | [`stap_7_uitleg.py`](stap_7_uitleg.py) |

Wat de twee meetmethodes zijn en waarom we methode 2 kiezen, staat in [Zo meten we hoe goed FaceNet is](../README.md#zo-meten-we-hoe-goed-facenet-is).


## Wat we afstellen

We proberen alle combinaties van de instellingen hieronder. Dat zijn 384 combinaties per set voorbeelden, elk met 200 drempels. De combinatie met de hoogste score volgens methode 2 wint. De instellingen staan in [`instellingen.py`](instellingen.py).

| Instelling | Wat we proberen | Wat het betekent |
|---|---|---|
| **Model** | Facenet, Facenet512 | Twee versies van FaceNet: 128 of 512 getallen per gezicht. |
| **Extra ruimte** (marge) | 0%, 10%, 20%, 30% | Hoeveel extra van het beeld rond het kader FaceNet te zien krijgt. |
| **Lichter maken** | nee, ja | Een donker gezicht eerst lichter maken (maal 1 tot 5), net als *Beeld lichter* in de labelapp. |
| **Soort afstand** | genormaliseerd, cosinus, gewoon | Drie manieren om te meten hoe ver twee vectoren uit elkaar liggen. |
| **Vergelijken met** | de beste foto, het gemiddelde | Vergelijkt FaceNet een kader met de meest gelijkende foto van een persoon, of met het gemiddelde van alle foto's van die persoon? |
| **Naam in een beeld** | mag vaker, elk één keer | Mag dezelfde naam twee keer in één beeld staan? |
| **Beslissen** | per kader, per track | Krijgt elk kader los een naam, of krijgt de hele track samen één naam? |
| **Drempel** | 200 waarden | Vanaf welke afstand een kader *iemand anders* is. |

Twee van die instellingen kun je zien.

![Hetzelfde gezicht met 0 tot 30% extra ruimte, en daaronder lichter gemaakt](../fotos/marge_en_lichter.jpg)

*Extra ruimte en lichter maken op een echt gezicht. Van links naar rechts krijgt FaceNet meer van het beeld om het gezicht te zien. De onderste rij is lichter gemaakt. Veel scènes in de film zijn erg donker, en FaceNet ziet daardoor weinig van een gezicht. Blauw is wat het beste werkt.*

![Eén track: per kader wisselt de naam, per track is er één naam](../fotos/per_track.jpg)

*Per kader of per track beslissen. Dit is één track met hetzelfde gezicht. De balk *per kader* laat beeld voor beeld zien wat FaceNet zegt als elk kader los beslist: soms de juiste naam (blauw), soms een verkeerde naam (oranje) en soms geen naam (grijs). Bij *per track* tellen alle kaders samen: het gemiddelde is betrouwbaarder dan één los beeld, en de hele track krijgt de juiste naam.*

![De hoogste score per keuze bij het afstellen, met foto's en stills](resultaten/fotos_en_kostuum/afstellen_per_instelling.png)

*Zo lees je dit plaatje: elk blok is één instelling. De balken laten zien hoe hoog de score kan worden met elke keuze. Blauw is de keuze van de winnaar. Hoe groter het verschil tussen de balken, hoe belangrijker die instelling is.*


## Een eerlijke schatting

De winnende instellingen zijn gekozen op dezelfde beelden als waarop we meten. Daardoor is de score te gunstig. Daarom rekenen we ook een eerlijke schatting uit (*leave-one-fragment-out*): we kiezen de instellingen steeds op zeven filmpjes en meten op het achtste.

![Acht rondes: in elke ronde wordt op zeven filmpjes afgesteld en op het achtste gemeten](../fotos/eerlijke_schatting.png)

*Elke regel is één ronde, met foto's + stills. Op de grijze filmpjes kiezen we de instellingen, op het oranje filmpje meten we. Rechts staat de score op dat filmpje. Video 3 en Video 8 zijn het moeilijkst.*


## De beste instellingen

| Instelling | Alleen foto's | Foto's + stills |
|---|---|---|
| Model | Facenet | Facenet512 |
| Extra ruimte | 20% | 20% |
| Lichter maken | ja | ja |
| Soort afstand | genormaliseerd | genormaliseerd |
| Vergelijken met | de beste foto | het gemiddelde |
| Naam in een beeld | elk één keer | elk één keer |
| Beslissen | per track | per track |
| Drempel | 1,0684 | 1,1076 |

Dit zijn de keuzes die het meeste helpen bij foto's + stills:

| Keuze | Score met deze keuze | Hoogste score zonder deze keuze |
|---|---|---|
| Donkere gezichten lichter maken | 0,874 | 0,775 |
| Vergelijken met het gemiddelde van de foto's | 0,874 | 0,773 |
| Per track beslissen | 0,874 | 0,816 |
| 20% extra ruimte om het kader | 0,874 | 0,801 (geen extra ruimte) |

Lichter maken en per track beslissen helpen in beide sets. Dat past bij deze film: de scènes zijn donker, en een hele track geeft meer informatie dan één beeld.

Bij [één gemiddelde vector](../gemiddelde_vector/README.md) zagen we dat het gemiddelde bij de standaarddrempel juist slechter werkt. Met een eigen drempel wint het gemiddelde hier wel.


## Wat eruit kwam

| Experiment | Score per gezicht (methode 2) | Eerlijke schatting | Score per beeld (methode 1) | Gezichten met de juiste naam | Namen die kloppen |
|---|---|---|---|---|---|
| Basis, foto's | 0,074 | | 0,078 | 4% | 93% |
| **Tuned, foto's** | **0,808** | 0,766 | 0,829 | 72% | 92% |
| Basis, foto's + stills | 0,308 | | 0,636 | 40% | 25% |
| **Tuned, foto's + stills** | **0,874** | 0,834 | 0,893 | 81% | 95% |

![Vier grafieken met de afstanden van goede en foute kaders, en de drempel](../fotos/drempel.png)

*Waarom afstellen zo helpt: kijk naar de twee grafieken onderaan. Blauw zijn kaders waarbij de dichtstbijzijnde persoon klopt, oranje zijn kaders waarbij die niet klopt. Na het afstellen liggen blauw en oranje aan weerszijden van de drempel. Bij de basis (bovenaan) lopen ze door elkaar.*

![De tijdlijn met de best afgestelde FaceNet: de ground truth en FaceNet liggen dicht bij elkaar](resultaten/fotos_en_kostuum/methode_1_tijdlijn.png)

*De tijdlijn met de best afgestelde FaceNet (foto's + stills). Elke regel is een persoon, en de tijd loopt van links naar rechts. Zwart is wanneer de persoon echt in beeld is, rood wanneer FaceNet de persoon ziet. Rood loopt nu bijna overal gelijk met zwart. Vergelijk dat met [de tijdlijn van de basis](../basis/resultaten/fotos_en_kostuum/methode_1_tijdlijn.png).*

![Per kader: wie het echt is tegen de naam van FaceNet, met de best afgestelde FaceNet](resultaten/fotos_en_kostuum/methode_2_verwarring.png)

*Zo lees je dit plaatje: elke rij is wie het echt is, elke kolom is de naam die FaceNet geeft. De hoge percentages staan nu op de schuine lijn: dat is goed. In de onderste rij staan de meeste kaders van figuranten en dingen die geen gezicht zijn, nu terecht bij* iemand anders*.*

### De score per filmpje

*Algemeen beste* is de winnaar over alle filmpjes. *Eerlijke schatting* is de instelling die op de andere filmpjes gekozen is. *Beste voor dit filmpje* is de instelling die alleen op dat filmpje het best werkt (`beste_per_filmpje.csv`).

Met alleen foto's:

| Filmpje | Algemeen beste | Eerlijke schatting | Beste voor dit filmpje |
|---|---|---|---|
| Video 1 | 0,797 | 0,721 | 0,872 |
| Video 2 | 0,838 | 0,711 | 0,850 |
| Video 3 | 0,968 | 0,946 | 0,969 |
| Video 4 | 0,972 | 0,972 | 0,997 |
| Video 5 | 0,716 | 0,716 | 0,900 |
| Video 6 | 0,788 | 0,469 | 0,852 |
| Video 7 | 0,818 | 0,818 | 0,860 |
| Video 8 | 0,414 | 0,414 | 0,572 |

Met foto's + stills:

| Filmpje | Algemeen beste | Eerlijke schatting | Beste voor dit filmpje |
|---|---|---|---|
| Video 1 | 0,856 | 0,856 | 0,887 |
| Video 2 | 0,871 | 0,871 | 0,892 |
| Video 3 | 0,924 | 0,638 | 0,971 |
| Video 4 | 0,997 | 0,997 | 0,997 |
| Video 5 | 0,957 | 0,957 | 0,974 |
| Video 6 | 0,839 | 0,839 | 0,855 |
| Video 7 | 0,850 | 0,850 | 0,863 |
| Video 8 | 0,655 | 0,588 | 0,671 |


## Wat dit betekent

- **Afstellen maakt het verschil.** De score gaat van 0,308 naar 0,874 met foto's + stills, en van 0,074 naar 0,808 met alleen foto's. Ook de eerlijke schattingen blijven hoog (0,834 en 0,766).
- **Foto's + stills blijft het beste**, maar met goede instellingen komen de gewone foto's al een heel eind.
- **Johann blijft het moeilijkst** (score 0,374 met foto's + stills). Johann is veruit het minst in beeld, en de herkenning mist Johann vaak.
- **Video 8 blijft het zwakst.** Daar wisselt het beeld heel vaak.

Let op: bij *per track beslissen* gebruiken we de tracks uit het labelen. Die zijn automatisch gemaakt, maar 44 tracks zijn bij het controleren met de hand geknipt.


## De filmpjes

Klik op GitHub op de link en daarna op *View raw* om een filmpje te downloaden.

- [Filmpje met alleen foto's](resultaten/fotos/filmpje.mp4)
- [Filmpje met foto's + stills](resultaten/fotos_en_kostuum/filmpje.mp4)


## Zo draai je het op een Mac en op Windows

Doe dit vanuit de map `experimenten`. Installeren hoeft één keer, zie [Installeren op Mac en Windows](../README.md#installeren-op-mac-en-windows).

Op een Mac:

```bash
.venv/bin/python tuned/draai_alles.py
```

Op Windows:

```bat
.venv\Scripts\python tuned\draai_alles.py
```

Dit draait alle stappen voor beide sets. Eén set kan ook, door er `--voorbeelden fotos` of `--voorbeelden fotos_en_kostuum` achter te zetten. Stap 1 duurt ongeveer een uur. De vectoren worden bewaard in `tussenbestanden/`, en daarna duurt alles nog een paar minuten.
