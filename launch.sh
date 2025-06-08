#!/bin/bash

source .venv/bin/activate

mkdir -p exec
python nanoc.py > exec/code.c
nasm -f elf64 exec/code.c
gcc -no-pie exec/code.o 
mv a.out exec/
./exec/a.out
