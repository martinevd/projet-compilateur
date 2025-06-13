# projet-compilateur

Ce projet a été réalisé par Martin EVRARD, Eliott LEBOEUF, Alexandre LAM et Paolo ESCOBAR.

Ce projet a pour objectif de créer un compilateur simple et de lui ajouter les fonctionnalités suivantes:

## Fonction :
Le langage d'entrée du spécialiseur autorise l'implémentation de fonctions.

Cette fonctionnalité a été réalisé par Martin EVRARD.

Ces fonctions peuvent être recursives, peuvent introduire des variables locales pouvant prendre le nom des variables globales (priorité aux variables locals lues), peuvent s'appeler mutellement, peuvent modifier des variables globales et peuvent retourner (ou non) un résultat.

Malheuresement, une fonction ne peut prendre qu'au plus 6 arguments. 

## Typage: 

La branche typage_statique représente l'implémentation que j'ai fait (LEBOEUF Eliott). Cette dernière permettait de réaliser différents types (int, long, ...) et d'utiliser les sous registres (eax, ax...) suivant la taille des types. Cette dernière fonctionnalité n'a pas été ajouté dans la version finale car nous n'arrivions pas à la merge (différences d'implémentations entre nos branches).


## String: 

Cette partie a été réalisée par Lam Alexandre.

Nous avons réussi à implémenter les string et on peut les concaténer, pas plus de deux en même temps, on peut trouver un caractère dans la chaîne et on arrive à calculer la longueur d'un string avec une fonction strlen.


## Double : TODO

**ATTENTION** : Le programme doit obligatoirement avoir une fonction "**exec**" afin de pouvoir l'exécuter en asm. Par ailleurs, le programme n'affiche pas le return de "exec" (s'il y en a un) dans la console, il est donc demandé d'y mettre un printf.

Pour lancer la compilation de simple.c, vous pouvez utiliser la commande `./launch.sh` avec deux arguments entiers.
