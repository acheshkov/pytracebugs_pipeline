#! /bin/sh

paper=zephyr_survey_mdpi

# https://tex.stackexchange.com/questions/53235/why-does-latex-bibtex-need-three-passes-to-clear-up-all-warnings
pdflatex ${paper}
bibtex ${paper}
pdflatex ${paper}
pdflatex ${paper}
