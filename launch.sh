#!/bin/bash

# Active l'environnement virtuel Python
source .venv/bin/activate

# Création du dossier de sortie
mkdir -p exec

# Compilation du programme
python3 nanoc.py > exec/simple.nasm
nasm -f elf64 exec/simple.nasm
gcc -no-pie exec/simple.o 
mv a.out exec/

# Exécution avec les paramètres passés au script
./exec/a.out "$1" "$2"

