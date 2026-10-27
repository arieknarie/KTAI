# De opdracht

[← terug naar het overzicht](../README.md)

De opdracht *Face Recognizer* komt uit hoofdstuk 15 van het vak Key Topics in
Artificial Intelligence. De opdracht vraagt om een eenvoudig programma dat
gezichten herkent in foto's en in video. De opdracht bestaat uit zes punten.
Hieronder staat bij elk punt eerst wat de opdracht vraagt, en daarna hoe wij
dat punt invullen. Ons eigen project is ook verdeeld in zes stappen; welke
stap wat doet, staat in [het overzicht](../README.md#waar-we-nu-staan).

**1. Verzamel een kleine verzameling gezichten van minstens drie personen,
liefst van verschillende kanten gefotografeerd.**
Wij gebruiken de 23 gewone foto's van de vier acteurs in `pictures/personal/`.
Elke acteur heeft daar een eigen map, dus van elke foto weten we zeker welke
acteur erop staat. Op twee foto's staan ook andere mensen; daar wijst iemand
in stap 2 met de hand aan welk gezicht van wie is. De foto's zelf gebruiken we
in stap 3.

**2. Laat een bestaand herkenningsprogramma van elk van die gezichten een
vingerafdruk maken.**
De opdracht noemt zo'n vingerafdruk een *embedding*: een lange rij getallen
die een gezicht beschrijft. Twee foto's van dezelfde persoon geven rijen
getallen die op elkaar lijken. De vingerafdrukken van de foto's van de
acteurs worden de voorbeelden waarmee we straks vergelijken. Ook die
vingerafdrukken maken we in stap 3.

**3. Zoek in een video in elk beeld de gezichten, maak van elk gezicht een
vingerafdruk, en vergelijk die met de voorbeelden.**
Wij gebruiken acht fragmenten uit *Das Boot* als video. De gezichten in de
fragmenten hebben we al gezocht in stap 1; de vingerafdrukken maken en
vergelijken doen we in stap 4.

De opdracht schrijft voor hoe je vergelijkt: je meet de afstand tussen twee
vingerafdrukken (de genormaliseerde Euclidische afstand: je brengt beide rijen
getallen eerst op dezelfde schaal en meet dan hoe ver ze uit elkaar liggen).
Hoe kleiner de afstand, hoe meer de twee gezichten op elkaar lijken. Is de
afstand kleiner dan een grens die je zelf kiest, dan geldt het gezicht als
dezelfde persoon als het voorbeeld.

De opdracht zegt ook dat de beelden uit de video niet gebruikt mogen zijn om de
voorbeelden te maken; anders test je het herkennen op beelden die het programma
al als voorbeeld heeft gezien. Misschien gebruiken we later naast de foto's ook
losse beelden uit de film (*stills*, in `pictures/inCharacter/`) als voorbeeld.
Drie van die stills zijn (bijna) hetzelfde beeld als een beeld uit de
fragmenten, en een vierde still is een andere foto van hetzelfde moment als in
een fragment. Die vier stills mogen dan niet als voorbeeld dienen voor het
fragment waar ze bij horen (zie [stap 2](stap2_labelen.md)).

**4. Laat zien hoe vaak elke persoon in de video voorkomt.**
Dat doen we in stap 5: we tellen per persoon in hoeveel beelden van de
fragmenten die persoon te zien is.

**5. Laat een tijdlijn zien: op welke momenten iemand in beeld is.**
Ook dat doen we in stap 5: per persoon laten we zien in welke stukken van de
fragmenten die persoon in beeld is.

**6. Zoek uit wanneer het herkennen goed werkt en wanneer niet, en wat helpt.**
De opdracht stelt drie dingen voor om te onderzoeken: hoe groot het gezicht in
beeld is, onder welke hoek het gezicht gefilmd is, en welke grens je kiest bij
punt 3. Voor ons verslag onderzoeken we ook nog drie eigen dingen: wat er
gebeurt bij een lage beeldkwaliteit, bij gezichten die veranderen (baard,
vuil, vermoeidheid, wat in deze film veel voorkomt) en bij slecht licht. Dat
onderzoek doen we in stap 6.

De opdracht raadt aan om voor het zoeken van gezichten de MediaPipe Face
Detector te gebruiken, een gratis programma van Google. Wij gebruiken dat
programma in stap 1.

Onder welke hoek een gezicht gefilmd is, hoeft in stap 2 niemand met de hand
aan te geven. MediaPipe geeft bij elk gezicht ook zes punten: de twee ogen, de
neus, de mond en de twee oren. Ons plan is om uit die punten in stap 6 af te
leiden hoe ver een gezicht opzij gedraaid is; daarvoor is nu nog niets
gebouwd.

Om te kunnen controleren of het herkennen klopt, maken we eerst zelf een
antwoordenblad: een tabel die bij elk gezicht in de fragmenten zegt wie het
werkelijk is. Het antwoordenblad vraagt de opdracht niet letterlijk, maar
zonder antwoordenblad kunnen we punt 4, 5 en 6 niet controleren. Daarom is het
maken van het antwoordenblad stap 1 en 2 van dit project.

Op het antwoordenblad staan de gezichten die MediaPipe in de fragmenten vindt.
Een mens, de labelaar, bekijkt die gezichten en legt met de hand vast wie het
is. Soms mist MediaPipe een gezicht helemaal. Is dat een gezicht van een van de
vier personen, dan tekent de labelaar zelf een rechthoek om dat gezicht, en
komt ook dat gezicht op het antwoordenblad. Zo kunnen we ook tellen hoe vaak
MediaPipe de vier personen mist, in de beelden die de labelaar te zien krijgt.
Dat is één beeld per *track*: een gezicht dat de computer volgt over een reeks
beelden na elkaar. Gemiste gezichten van andere mensen (figuranten) tekent
de labelaar niet: dat zou in drukke scènes uren kosten, en
in ons project gaat het om de vier personen. Hoe het antwoordenblad er precies
uitziet, staat in [het overzicht](../README.md#hoe-het-antwoordenblad-eruitziet).
