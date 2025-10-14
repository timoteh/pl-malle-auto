# 🔗 Script d'automatisation Dofus pour se faire PL au Malléfisk et avoir moins envie de mourir.

> ⚠️ **ATTENTION**: CECI EST UNIQUEMENT À DES FINS ÉDUCATIVES ET EST INTERDIT PAR ANKAMA  
> ⚠️ **WARNING**: THIS IS FOR EDUCATIONAL PURPOSES ONLY AND IS PROHIBITED BY ANKAMA

## 📋 Description

Ceci est un script d'automatisation pour Dofus qui permet de répéter automatiquement le donjon malléfisk pour se faire PL. Il utilise la détection d'images par OpenCV pour surveiller l'état du jeu et effectuer des actions automatiques.

### Fonctionnalités

- ✅ Détection automatique de la fin de combat
- ✅ Relancement automatique du donjon
- ✅ Détection du level up avec fermeture automatique
- ✅ Gestion du rejoin automatique
- ✅ Compteur de combats en overlay
- ✅ Système de watchdog pour détecter les blocages
- ✅ Redémarrage automatique après 30 minutes
- ✅ Gestion des erreurs et retry automatique

## 🛠️ Prérequis

- Python 3.7+
- Windows 10/11
- Les bibliothèques suivantes :
  - `pyautogui` - Automatisation de la souris et du clavier
  - `opencv-python` (cv2) - Détection d'images
  - `numpy` - Traitement des données
  - `Pillow` - Manipulation d'images
  - `keyboard` - Gestion du clavier

## 📦 Installation

1. **Cloner le dépôt**

2. **Installer les dépendances**
   ```bash
   pip install pyautogui opencv-python numpy Pillow keyboard
   ```

## 🎮 Utilisation

### Lancement du script

```bash
python main.py
```

Le script va :
1. Charger les images de référence depuis le dossier `images/`
2. Créer un overlay avec un compteur de combats en haut à droite de l'écran
3. Surveiller l'écran toutes les 3 secondes
4. Détecter automatiquement les différents états du jeu et agir en conséquence

### Arrêter le script

Appuyez sur `Ctrl+C` dans le terminal pour arrêter proprement le script.

## ⚙️ Configuration

Toutes les configurations se trouvent au début du fichier `main.py` :

### Paramètres principaux

```python
# Chemins des images de référence
IMAGE_LEVEL = "./images/image_lvl.PNG"        # Image du level up
IMAGE_JOIN = "./images/image_join_2.PNG"      # Image du bouton rejoin
IMAGE_OUT_FIGHT = "./images/image_out.PNG"    # Image hors combat
IMAGE_IN_FIGHT = "./images/image_fight.PNG"   # Image en combat

# Régions de surveillance (x, y, largeur, hauteur)
OUT_FIGHT_REGION = (655, 961, 31, 29)         # Zone pour détecter la fin de combat
IN_FIGHT_REGION = (655, 961, 31, 29)          # Zone pour détecter le combat
LVL_REGION = (841, 342, 156, 30)              # Zone pour détecter le level up
JOIN_REGION = (8, 492, 36, 39)                # Zone pour détecter le bouton rejoin

# Seuils de confiance (0.0 à 1.0)
CONFIDENCE = 0.7          # Seuil général
LVL_CONFIDENCE = 0.6      # Seuil pour le level up (plus strict)

# Délais
CHECK_INTERVAL = 3        # Intervalle entre chaque vérification (secondes)
CLICK_DELAY = 2.5         # Délai entre les clics (secondes)
CLICK_DELAY_SMALLER = 1.5 # Délai réduit pour certains clics

# Debug
DEBUG_MODE = False        # Active les messages de debug détaillés
```

### Positions de clics

Les positions de clics sont configurables pour s'adapter à votre configuration :

```python
# Clics pour relancer le donjon
RESTART_DUNGEON_CLICK_POSITIONS = [
    (874, 371),   # Clic 1
    (1111, 418),  # Clic 2
    (582, 329),   # Clic 3
    (836, 391),   # Clic 4
    (1030, 441),  # Clic 5
    (1030, 441)   # Clic 6
]

# Clics pour rejoindre
JOIN_CLICK_POSITIONS = [
    (170, 535)
]

# Clics pour redémarrer après 30 minutes
RESTART_CLICK_POSITIONS = [
    (1898, 10),   # Fermer
    (293, 450),   # Relancer
    (1034, 568)   # Confirmer
]
```

## 🎯 Obtenir les coordonnées

Utilisez l'utilitaire `get_coord` pour obtenir les coordonnées de votre écran :

```bash
cd get_coord
python main.py
```

**Instructions** :
- Déplacez votre souris sur l'écran
- Appuyez sur `s` pour sauvegarder une première position
- Appuyez sur `s` une deuxième fois pour calculer la différence entre les deux positions
- Appuyez sur `Ctrl+C` pour quitter

Cet outil est utile pour :
- Obtenir les coordonnées exactes des boutons à cliquer
- Mesurer la taille des régions à surveiller (largeur × hauteur)

## 📁 Structure du projet

```
chain_malle/
│
├── main.py                    # Script principal
├── get_coord/
│   └── main.py               # Utilitaire pour obtenir les coordonnées
├── images/
│   ├── image_lvl.PNG         # Image de référence pour le level up
│   ├── image_join.PNG        # Image de référence pour le rejoin
│   ├── image_join_2.PNG      # Image alternative pour le rejoin
│   ├── image_out.PNG         # Image de référence hors combat
│   ├── image_fight.PNG       # Image de référence en combat
│   └── image_lvl_test.PNG    # Image de test
└── README.md                 # Ce fichier
```

## 🔧 Personnalisation

### Créer vos propres images de référence

1. Faites une capture d'écran de la zone que vous voulez détecter
2. Recadrez précisément l'image pour ne garder que l'élément à détecter
3. Sauvegardez l'image au format PNG dans le dossier `images/`
4. Mettez à jour le chemin dans `main.py`

### Ajuster les régions de surveillance

1. Utilisez `get_coord/main.py` pour obtenir les coordonnées
2. Format : `(x, y, largeur, hauteur)`
   - `x, y` : position du coin supérieur gauche
   - `largeur, hauteur` : dimensions de la zone

### Ajuster les seuils de confiance

- **Trop de faux positifs** : Augmentez `CONFIDENCE` (ex: 0.8)
- **Pas assez de détections** : Diminuez `CONFIDENCE` (ex: 0.6)
- Le script utilise plusieurs méthodes de détection pour plus de fiabilité

## 🐛 Dépannage

### Le script ne détecte pas les images

1. Vérifiez que les régions de surveillance sont correctes
2. Vérifiez que les images de référence correspondent exactement à ce qui apparaît à l'écran
3. Activez le mode debug : `DEBUG_MODE = True`

### Le script est trop lent

1. Augmentez `CHECK_INTERVAL` pour vérifier moins souvent
2. Réduisez les délais `CLICK_DELAY` si votre ordinateur est rapide

### Le script se bloque

Le script intègre un système de watchdog qui détecte automatiquement les blocages après 30 secondes d'inactivité.

## 📊 Fonctionnement du script

Le script vérifie dans cet ordre :

1. **Level up** : Si détecté, appuie sur `Escape` pour fermer le layer
2. **Fin de combat** : Si détecté, lance la séquence de relance du donjon
3. **Bouton rejoin** : Si détecté, clique pour rejoindre
4. **Combat en cours** : Attend la fin du combat
5. **Recommence**

### Système de redémarrage automatique

- Après 30 minutes, Le script effectue un redémarrage complet
- Ferme le jeu
- Relance le jeu
- Reprend le farming

## ⚖️ Avertissement légal

Ce projet est fourni **uniquement à des fins éducatives**. L'utilisation de bots et scripts est contraire aux conditions d'utilisation d'Ankama et peut entraîner un bannissement permanent de votre compte. 

**Utilisez ce code à vos propres risques.**

---

*Développé pour l'apprentissage de l'automatisation et de la vision par ordinateur avec Python.*
