
> Ouvrir cette page à [https://demikl.github.io/yahboom-microbit-robot-car/](https://demikl.github.io/yahboom-microbit-robot-car/)

# Yahboom Microbit Robot Car extension for Makecode

La [voiture robot Yahboom m:bit](http://www.yahboom.net/study/Bitbot) dispose d'une [extension officielle](https://github.com/lzty634158/yahboom_mbit_en). Cette extension propose des blocs plus directs pour les composants déjà câblés sur le robot : aucune pin n'est à sélectionner.

![robot picture](https://category.yahboom.net/cdn/shop/products/Yahboom-micro-bit-smart-robot-car-bitbot-with-IR-and-APP-for-Micro-bit-V2-V1.5-yahboom-1671099012.jpg?v=1671099014)

## Blocs disponibles

* **Moteurs** : avancer, reculer, tourner avec une roue, pivoter ou s'arrêter ; piloter aussi chaque moteur indépendamment. Vitesse de 0 à 255 et durée facultative en millisecondes (0 = fonctionnement continu). Une nouvelle commande sur un moteur annule son arrêt différé précédent.
* **Servo-moteurs** : positionner les connecteurs J2, J3 et J4 entre 0° et 180°, couper leur signal ou réactiver leur dernière position (90° au départ).
* **PWM** : régler les sorties L9, L10 et L11 de 0 à 100 %, les couper ou restaurer leur dernier réglage (100 % au départ).
* **Phares** : choisir une couleur et une luminosité de 0 à 100 %, ou éteindre les deux phares RGB.
* **Neopixels** : choisir la couleur des trois pixels intégrés ou d'un pixel numéroté de 1 à 3, ou les éteindre.
* **Capteurs** : distance en centimètres du module ultrason branché sur J5 (0 si aucun écho), lecture noir/blanc des capteurs de ligne gauche et droit, détection d'obstacle à l'avant. Ces lectures ne modifient pas les LEDs témoins.

Le [schéma de la carte](docs/mbit_SCH.jpg) et l'[extension Yahboom](https://github.com/lzty634158/yahboom_mbit_en) déterminent les affectations : contrôleur PCA9685 à l'adresse 0x41, moteurs sur les canaux 12–15, phares sur 0–2, servos sur 3–5, PWM sur 9–11, trois pixels sur P16, ultrason sur P14/P15, capteurs de ligne sur P2/P1 et détecteur d'obstacle sur P9/P3.

## Exemple

Le programme [voyage autonome](examples/voyage-autonome.ts) est à copier dans l'éditeur JavaScript d'un **nouveau projet MakeCode après import de l'extension**. Il utilise l'accéléromètre pour les chocs, l'ultrason pour adapter la vitesse, la boussole pour les virages et les deux capteurs de ligne pour arrêter le robot lorsqu'il est soulevé. Il n'utilise pas le capteur d'obstacle IR. Calibrez la boussole au démarrage et faites les premiers essais roues décollées du sol ; les moteurs peuvent fausser le cap magnétique. Le seuil de choc et les vitesses sont à ajuster sur le robot. L'exemple ne fait pas partie des fichiers de l'extension compilée.

La variante [voyage autonome sans boussole](examples/voyage-autonome-sans-boussole.ts) remplace la mesure de l'angle par un pivot temporisé : consigne moteur 25/255, et hypothèse de 1 seconde pour 90°. La durée est proportionnelle à un angle choisi entre 100° et 170°. Écran LED orienté vers l'avant, la détection de choc utilise uniquement le freinage sur Z ; les chocs latéraux sur X sont désactivés par `ACTIVER_CHOC_LATERAL = false` mais restent mesurés pour le diagnostic. Elle ignore les 800 premières millisecondes après un démarrage des moteurs. Pour limiter les fausses alertes dues aux vibrations, il faut **deux échantillons consécutifs de même sens** au-dessus de 900 milli-g (espacés de 80 ms au maximum) : un choc plus bref peut donc passer inaperçu. La console série donne toutes les 200 ms les pics `|dX|`, `freinZ`, `accelZ` et les longueurs de séries `suiteX`, `suiteFrein` ; elle donne `dX` et `dZ` signés lors d'un choc confirmé. Elle affiche aussi la distance ultrason et son interprétation toutes les 500 ms pendant l'avance. Sous 10 cm, le robot tente un pivot puis vérifie deux mesures consécutives : si l'obstacle persiste, il essaie une seule fois à vitesse 65/255, puis s'arrête en sécurité s'il est toujours bloqué ou si la distance ne peut pas être confirmée (0 = aucun écho). En avance normale, 0 entraîne encore la vitesse maximale. Un obstacle peut rester visible même après un vrai pivot ; sans capteur de rotation, l'angle et le mouvement réels ne peuvent pas être confirmés. Si un démarrage produit un grand `freinZ` au lieu d'`accelZ`, inversez `SENS_FREINAGE_Z`. Étalonnez `VITESSE_PIVOT`, `VITESSE_PIVOT_REESSAI`, `MS_PAR_90_DEGRES` et `SEUIL_CHOC` sur le robot.

## Utiliser comme extension

Ce dépôt peut être ajouté en tant qu'**extension** dans MakeCode.

* ouvrir [https://makecode.microbit.org/](https://makecode.microbit.org/)
* cliquez sur **Nouveau projet**
* cliquez sur **Extensions** dans le menu engrenage
* recherchez **https://github.com/demikl/yahboom-microbit-robot-car** et importez

## Éditer ce projet

Éditer ce dépôt dans MakeCode.

* ouvrir [https://makecode.microbit.org/](https://makecode.microbit.org/)
* cliquez sur **Importer** puis cliquez sur **Importer l'URL**
* collez **https://github.com/demikl/yahboom-microbit-robot-car** et cliquez sur importer

#### Métadonnées (utilisées pour la recherche, le rendu)

* for PXT/microbit
<script src="https://makecode.com/gh-pages-embed.js"></script><script>makeCodeRender("{{ site.makecode.home_url }}", "{{ site.github.owner_name }}/{{ site.github.repository_name }}");</script>
