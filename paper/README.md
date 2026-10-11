# paper

De LaTeX-bron van de paper *Evaluating FaceNet resilience under extreme
physical and environmental stress: A case study based on Das Boot*, in de
opmaak van ICML 2021.

## Bestanden

| Bestand / map | Doel |
|---|---|
| `main.tex` | de paper zelf; commentaar bovenaan geeft de status per sectie |
| `references.bib` | de bronnen; elke `\cite{...}` in `main.tex` moet hier staan |
| `figures/` | de afbeeldingen in de paper (nu nog twee voorbeeldplaatjes) |
| `.gitignore` | houdt LaTeX-bijproducten (`*.aux`, `*.log`, de PDF, …) buiten git |

## Stijlbestanden

`main.tex` heeft twee bestanden uit het officiële ICML 2021-template nodig.
Die staan **nog niet** in deze repository:

- `icml2021.sty`
- `icml2021.bst`

Download `icml2021_style.zip` via de ICML 2021-auteursinstructies
(<https://icml.cc/Conferences/2021/StyleAuthorInstructions>) en zet die twee
bestanden in deze map, naast `main.tex`.

## Compileren

```bash
cd paper
latexmk -pdf main.tex
```

Zonder `latexmk`: `pdflatex main`, `bibtex main`, `pdflatex main`,
`pdflatex main`.

## Nog te doen

- Abstract, Methods en Experimental Results bevatten nog de voorbeeldtekst van
  het template.
- De grafieken voor Results staan klaar in
  [`../experiments/results/figures/`](../experiments/results/figures/) (PDF). Kopieer
  ze naar `figures/` of verwijs er direct naar.
- `figures/example_plot.png` en `figures/example_pipeline.png` zijn
  voorbeeldplaatjes; vervang ze door echte figuren.
- In het auteursblok staat nog "Student Number 1".
- `references.bib`: de bron `cheng2024` moet nog gecontroleerd worden (zie de
  opmerking bij die bron).
