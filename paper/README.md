# Paper: FaceNet resilience in *Das Boot*

LaTeX source of the course paper *Evaluating FaceNet resilience under extreme
physical and environmental stress: A case study based on Das Boot* (Key Topics
in Artificial Intelligence, Open Universiteit), written in the ICML 2021 format.

## Contents

| File / folder    | Purpose                                                        |
|------------------|----------------------------------------------------------------|
| `main.tex`       | The paper itself                                               |
| `references.bib` | BibTeX entries for every `\cite{...}` in `main.tex`            |
| `figures/`       | Images used in the paper (currently two placeholders)          |
| `.gitignore`     | Keeps LaTeX build artefacts (`*.aux`, `*.log`, PDF, ...) out of git |

## Required: ICML 2021 style files

`main.tex` needs two files from the official ICML 2021 template. They are
**not** included in this repository yet:

- `icml2021.sty`
- `icml2021.bst`

Download `icml2021_style.zip` from the ICML 2021 author instructions
(<https://icml.cc/Conferences/2021/StyleAuthorInstructions>) and copy those
two files into this folder (next to `main.tex`).

## Building the PDF

```bash
cd paper
latexmk -pdf main.tex
```

Without `latexmk`: run `pdflatex main`, `bibtex main`, `pdflatex main`,
`pdflatex main`.

## Open items

- Abstract, Methods and Experimental Results still contain template text.
- `figures/example_plot.png` and `figures/example_pipeline.png` are
  placeholders; replace them with the real figures (or change the file names
  in `main.tex`).
- Author block: "Student Number 1" still needs the real student number.
- `references.bib`: the entry `cheng2024` needs checking (see the note above
  that entry).
