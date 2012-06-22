import os

arquivao = open(raw_input('Digite o nome do arquivo: '), 'r').read()

for f in os.listdir('.'):
    if not os.path.isdir(f) and open(f, 'r').read().lstrip().rstrip() in arquivao:
        print f
