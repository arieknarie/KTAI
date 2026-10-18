# De eerdere steekproef

In deze map staat een oudere controle van het volgen van gezichten in de
filmfragmenten. We bewaren die controle als geschiedenis; de uitkomsten gelden
niet meer voor de huidige bestanden van het project.


## Waar deze controle over ging

In stap 1 volgt de computer elk gevonden gezicht van beeld tot beeld. Zo'n
gevolgd gezicht heet een track. In stap 2 kiest de labelaar (de persoon die
met de hand vastlegt wie er in beeld is) per track één keer wie het is, en die
keuze geldt voor alle beelden van de track. Zo ontstaat het antwoordenblad:
de tabel waarmee we straks het herkenningsprogramma nakijken. Springt het
kader (de rechthoek om het gezicht) halverwege de track naar een ander
gezicht, dan krijgt een deel van de beelden de verkeerde naam op het
antwoordenblad. Met de controle zochten we zulke fouten.

Deze controle hoorde bij de vorige manier van volgen, versie 4 (zie
[Stap 1](../../../docs/stap1_gezichten_vinden_en_volgen.md)). Toen bekeken we
niet alle tracks, maar een steekproef:

- 215 tracks van 5 beelden of langer: alle 95 tracks van 100 beelden of
  langer, 60 willekeurige tracks van 25 tot 99 beelden en 60 willekeurige
  tracks van 5 tot 24 beelden;
- 150 willekeurige korte tracks van 1 tot 4 beelden.

Wat eruit kwam:

- In 12 van de 215 tracks stond het kader voor een deel op een ander gezicht
  of op iets dat geen gezicht is. Die 12 tracks zijn op 14 plekken in stukken
  geknipt.
- Ook na het knippen zouden bij versie 4 naar schatting ongeveer 220 van de
  43.414 gevonden gezichten (0,5%) de verkeerde naam krijgen. In de tracks
  die niet of maar kort bekeken waren, konden namelijk nog fouten zitten.
- Een track sprong vooral in drukke scènes, met veel gezichten dicht bij
  elkaar, naar een ander gezicht over. Ook kan een kader aan het begin of het
  eind van een track op iets anders staan, zoals een lamp of een achterhoofd.
- Ongeveer 4 van de 10 korte tracks waren echte gezichten. Daarom labelen we
  alle tracks, ook tracks van één beeld.

Bij de huidige manier van volgen (versie 5) horen andere tracks met andere
nummers, dus de oordelen in deze map gelden niet meer. Daarom is bij versie 5
elke track van twee beelden of langer opnieuw bekeken: 1.828 tracks, en niet
meer een steekproef. Hoe dat ging, staat in
[Controle van het volgen](../../../docs/stap1_controle.md); de oordelen staan
in `data/audit/controle_alle_tracks.csv`.


## Wat er in deze map staat

- `tracks_01.jpg` tot en met `tracks_22.jpg`: van elk van de 215 tracks 8
  uitsneden (kleine stukjes beeld rond het kader), verdeeld over de hele
  track. Het oordeel per track staat in `controle_tracks.csv`.
- `short_01.jpg` tot en met `short_05.jpg`: van elk van de 150 korte tracks
  één uitsnede. Het oordeel per track staat in `controle_korte_tracks.csv`.
- `audit_index.csv`: welke track op welk plaatje staat.
- `audit_tracks.py`: het programma dat deze plaatjes maakte. Het werkt niet
  meer, omdat de tracks van versie 4 vervangen zijn door die van versie 5. Het
  hoort daarom ook niet meer bij de programma's in `code/`.

De tracknummers in deze bestanden zijn de nummers van versie 4. Hetzelfde
nummer kan in de huidige bestanden bij een andere track horen.
