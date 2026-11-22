#!/bin/bash
set -e
mkdir -p ../images
for f in *.tex; do
    name="${f%.tex}"
    echo "Compilando $f..."
    pdflatex -interaction=batchmode "$f" > /dev/null
    pdfcrop "${name}.pdf" "../images/${name}.pdf" > /dev/null
    echo "Gerado: ../images/${name}.pdf"
done
echo "Todas as imagens foram compiladas com sucesso!"
