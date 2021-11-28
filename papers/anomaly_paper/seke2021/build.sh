#! /bin/sh

paper=anomaly_vae

# https://tex.stackexchange.com/questions/53235/why-does-latex-bibtex-need-three-passes-to-clear-up-all-warnings
pdflatex --shell-escape ${paper}.tex
biber ${paper}
pdflatex --shell-escape ${paper}.tex
pdflatex --shell-escape ${paper}.tex
