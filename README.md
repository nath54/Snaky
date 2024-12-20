# Projet Snaky

## 0. Membres du groupe

- CERISARA Nathan
- JACQUET Ysée

## 1. Introduction

L'objectif de ce Projet était donc de réaliser une implémentation du jeu de Snake (un serpent sur une grille 2d qui doit manger des pommes) avec une librairie graphique comme Tkinter ou bien Pygame, puis de faire un apprentissage génétique pour créer des bots qui apprennent à jouer au jeu.

Ceci a donc été réalisé, et ce projet a été encore plus ambitieux, car il a permis de base pour développer la librairie graphique de Nathan (`lib_nadisplay.py`), qui a donc été utilisée ici pour la partie graphique.

*Note: La librairie `lib_nadisplay.py` est en fait plus un moteur d'application, qui contient une partie graphique, car gestion de threads, d'évenements, et de variables globales.*


## 2. Avertissements


Par **manque de temps**:

- L'aspect graphique de l'application n'a pas pu être développé, donc c'est un peu moche, mais au moins c'est fonctionnel
- Taille de la fenêtre (flexible, mais pas trop), donc l'affichage ne marche pas bien si on redimensionne la fenêtre en trop petit
- Potentiels bugs dans l'application: quitter et relancer. Il n'y a normalement pas de bugs qui empĉhe complètement l'utilisation de l'application
- Tous les paramètres de jeu ne sont pas encore bien customisables
- Une campagne et une histoire avaient été imaginées, mais pas eu le temps de la mettre dans le jeu (*__plot de l'histoire:__ Un petit serpent a vu un jour un impressionnant dragon chinois volant dans le ciel, et il voulu devenir un dragon lui aussi. Il part donc à l'aventure découvrir le monde, et essayer de trouver comment devenir lui aussi un grand dragon chinois volant*).
- Il n'y a malheureusement qu'une seule carte disponible dans le jeu.
- Les bots ne sont malheureusement pas aussi bon que souhaité ou alors ca prends vraiment bcp de temps pour trouver un bon bot par apprentissage génétique / alors la structure utilisée ne le permet pas.

Aussi:
- L'entièreté du développement et des tests ont été réalisés sur Linux, la réelle compatibilité sur Windows de la librairie `lib_nadisplay.py` reste encore à ce jour inconnue.
- S'il y a des soucis de performances, vous pouvez essayer de changer les paramètres suivant pour avoir une expérience plus agréable :
    * la taille de la grille
    * le nombre de joueurs / de bots
    * la vitesse des serpents

## 3. Mise en place

### 3.1. Environnement virtuel (Optionnel)

Il est d'abord nécessaire d'avoir un environnement python fonctionnel (avec une version de python récente, *le projet a été développé et testé sour python3.12, les versions antérieures n'ont pas été testées*).

Il est possible (et recommandé) d'utiliser un environnement virtuel python (**venv**), qui peut se créer avec la commande :

```sh
# Il faudra peut être installer le package python3.12-venv depuis votre gestionnaire de paquet préféré.
python3.12 -m venv venv

# Il faut ensuite se connecter au venv:
source venv/bin/activate

# Pour sortie ensuite du venv
deactivate
```

### 3.2. Installation des librairies requises

Il faut ensuite installer les librairies nécessaire, cela se réaliste avec la commande suivante depuis la racine du projet:

```sh
python3.12 -m pip install -r ./requirements
```

La mise en place est maintenant terminée !

### 3.3. Lancement de l'application

L'application se lance avec la commande suivante:

```sh
python3.12 main.py
```

Et normalement, il ne devrait pas y avoir de problèmes et l'application va se lancer correctement.


## 4. Organisation du projet

Ce projet à été organisé comme suivant:

- tous les fichiers qui commencent par `lib_nadisplay` sont des fichiers de la librairie graphique, ils ne sont donc pas très importants pour le Snake en lui-même.

- tous les fichiers qui commencent par `scene_` sont des fichiers qui contiennent la définition graphique de chaque menu, et toutes les fonctions utiles et nécessaires dans leur contexte

    * La fonction qui met à jour la physique des serpents (le coeur du jeu) a pour nom `update_physic` et est dans `scene_game.py`

- le fichier `lib_snake.py` contient quelques classes associées au serpents, **dont les bots**, des fonctions pour dessiner les environnements dans la grille, et des fonctions pour changer l'apparence des serpents

- la fonction `main.py` est le point d'entrée du programme, il gère aussi d'un point de vue très très haut les différents éléments de l'application et donne la main au moteur de l'application


## 5. Base de l'application / Comment l'utiliser

TODO: à rédiger (description et fonctionnalités des différents menus pour : 1. Faire des parties normales  /  2. Entraînement de bots)

Info qui ne se devine pas facilement: le bouton `delete bad bots` supprime tous les bots qui ont un `max_score` strictement inférieur à `min_score_to_reproduce`.


## 6.  Structure des bots

Dans le jeu, un bot va choisir la prochaine direction à prendre après chaque mouvement.
Ces bots ont tous un paramètre qui s'appelle `security` activé par défaut et qui consiste à ne pas proposer le choix des directions qui entraîneraient directement la mort du serpent.

Déjà, il y a les bots suivants disponibles dans le jeu (non appris):
- Un bot complètement random : `bot_random`
- Un bot parfait : `bot_perfect`

Ensuite, j'ai testé deux versions de bots différents pour l'apprentissage génétique.

Ils ont le même contexte en entrée et la même sortie:

### 6.1. Description du contexte en entrée de ces bots:

On va prendre la matrice de la grille centrée sur la tête du serpent et avec un certain rayon (par défaut à 3).
Les obstacles prennent pour valeur `-1`, les cases vides `0`, et les cases avec des pommes `1`.

Cette matrice est ensuite applatie et on y concatène:
    - optionnellement: la direction de la ou les prochaines pommes
    - optionnellement: des valeurs aléatoires pour essayer de casser les cycles des bots (mais ca ne marche pas: possiblement un bug ou pas assez de valeurs aléatoires, ou pas assez fortes)


### 6.2. Description de la sortie de ces bots:

Ces bots renvoient ensuite en sortie un vecteur de dimension 4 (chaque dimension correspond à une direction), et on renvoie la direction correspondant à la plus grande valeur de ce vecteur.


### 6.3. Spécifités du bot version 1:

La première version testée consiste juste à une multiplication linéaire, dont la matrice des poids de dimension (taille du vecteur de contexte en entrée, 4).

- X = contexte d'entrée (n)
- Y = X * W1   avec W1 de dimension (n, 4)

Lors d'une initialisation aléatoire, on initialise cette matrice de poids avec une loi normale centrée sur 0 et de variance 1.


### 6.4. Spécifités du bot version 2:

La seconde version testée consiste à deux couches de multiplication linéaire et avec l'application d'une fonction d'activation entre les deux:

Soit:

- X = contexte d'entrée (n)
- X = X * W1   avec W1 de dimension (n, h) avec donc h un hyperparamètre qui modélise la dimension intermédiaire.
- X = MAX(X, 0)  sur chacune des composantes
- Y = X * W2   avec W2 de dimension (h, 4)


L'idée était d'avoir plus de paramètres disponibles pour essayer de pouvoir avoir plus de libertés et de possibilités pour le comportement des bots.

Lors d'une initialisation aléatoire, on initialise tous ces paramètres avec une loi normale centrée sur 0 et de variance 1.


## 7. Apprentissage génétique des bots


Une tentative d'apprentissage consiste à enchaîner un certain nombre de parties de bots, entre chaque groupe de parties, on va créer de nouveaux bots, s'il y a des bots qui ont un max_score supérieur à un seuil minimal pour pouvoir se reproduire, au hasard: soit on en prends deux et on les fusionne, soit on crée un nouveau bot en appliquant un bruit gaussien (de variance le paramètre `learning_rate`). On crée aussi de nouveaux bots complètement au hasard, et l'objectif souhaité est donc de trouver des poids qui donnent un bot qui réussit à manger pleins de pomme tout en survivant le plus possible.

Ensuite, l'idée est de manuellement enchaîner plusieurs tentatives d'apprentissage tout en augmentant graduellement le seuil de score minimal pour se reproduire, et en supprimant tous les bots qui ont un score inférieur à ce seuil.

La théorie dit qu'en explorant suffisament l'espace des possibilités, on peut avoir un bon bot ! La pratique nous dit que soit il faut être extrêmement chanceux (plus difficile que gagner au loto), ou bien explorer suffisament longtemps l'espace des paramètres possibles.


## 8. Conclusion

TODO: à rédiger
