
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

La variante [voyage autonome sans boussole](examples/voyage-autonome-sans-boussole.ts) remplace la mesure de l'angle par un pivot temporisé. Le premier pivot utilise une consigne moteur de 55/255 et une hypothèse de 1 seconde pour 90° ; le réessai utilise 65/255 et 400 ms pour 90°, d'après l'observation d'un pivot trop long à cette vitesse. La durée est proportionnelle à un angle choisi entre 100° et 170°. Écran LED orienté vers l'avant, la détection de choc utilise uniquement le freinage sur Z ; les chocs latéraux sur X sont désactivés par `ACTIVER_CHOC_LATERAL = false` mais restent mesurés pour le diagnostic. Elle ignore les 800 premières millisecondes après un démarrage des moteurs. Pour limiter les fausses alertes dues aux vibrations, il faut **deux échantillons consécutifs de même sens** au-dessus de 900 milli-g (espacés de 80 ms au maximum) : un choc plus bref peut donc passer inaperçu. La console série donne toutes les 200 ms les pics `|dX|`, `freinZ`, `accelZ` et les longueurs de séries `suiteX`, `suiteFrein` ; elle donne `dX` et `dZ` signés lors d'un choc confirmé. Elle affiche aussi la distance ultrason et son interprétation toutes les 500 ms pendant l'avance.

Entre 60 cm et 10 cm, elle ralentit et amorce un virage de plus en plus serré en avançant, avec le NeoPixel latéral correspondant clignotant orange ; à 60 cm ou plus, elle roule droit et éteint le clignotant après 500 ms de voie libre confirmée. Le programme affecte le pixel 3 à gauche et le pixel 1 à droite du robot : inversez `PIXEL_GAUCHE` et `PIXEL_DROIT` si leur disposition est différente. À 10 cm ou moins, le robot s'arrête, recule brièvement puis pivote, comme en cas de choc. Il vérifie ensuite deux mesures consécutives : si l'obstacle persiste, il essaie une seule fois un pivot plus rapide et plus court, puis s'arrête en sécurité s'il est toujours bloqué ou si la distance ne peut pas être confirmée (0 = aucun écho). Durant un choc ou la procédure d'évitement rapproché, les deux NeoPixels latéraux et les deux phares RGB clignotent orange comme des warnings ; les phares RGB ne sont pas indépendants. En avance normale, 0 entraîne encore la vitesse maximale, sans confirmer que la voie est libre pour l'extinction du clignotant. Le symbole de la vache apparaît sur l'écran LED quand le robot est soulevé et s'efface à sa remise au sol, sans effacer le symbole d'arrêt de sécurité. Un obstacle peut rester visible même après un vrai pivot ; sans capteur de rotation, l'angle et le mouvement réels ne peuvent pas être confirmés. Si un démarrage produit un grand `freinZ` au lieu d'`accelZ`, inversez `SENS_FREINAGE_Z`. Étalonnez `VITESSE_PIVOT`, `VITESSE_PIVOT_REESSAI`, `MS_PAR_90_DEGRES`, `MS_PAR_90_DEGRES_REESSAI` et `SEUIL_CHOC` sur le robot.

Le programme émet aussi toutes les secondes `Etat`, `horsSol`, `ligneG` et `ligneD`, même à l'arrêt : `horsSol=true` signifie qu'il attend que les deux capteurs restent blancs pendant une seconde. Ouvrez le moniteur série USB puis réinitialisez la micro:bit si vous voulez voir le message initial. Si aucun état périodique n'arrive, vérifiez le transfert du programme et la connexion série USB avant de conclure à une panne de capteur.

La [version Python MakeCode sans boussole](examples/voyage-autonome-sans-boussole.py) conserve ce comportement dans un programme autonome à copier **seul** dans l'éditeur Python d'un nouveau projet MakeCode, après import de cette extension. Ce n'est pas un programme MicroPython natif : ses appels `RobotCapteurs`, `RobotActionneurs` et `RobotAfficheurs` dépendent de l'extension MakeCode. Le `CapitaineDuVoyage` coordonne la `SentinelleDuSol` (suspension et reprise), la `VigieDesChocs` (accéléromètre), l'`EclaireurUltrason` (distance et virage préventif), le `MecanicienDesRoues` (moteurs) et le `SignaleurDesLumieres` (voyants et écran). Chaque personnage expose des méthodes en français sans accents. A+B impose un arrêt définitif jusqu'au bouton Reset ; comme dans l'exemple TypeScript, le robot reprend automatiquement après une seconde avec les deux capteurs blancs. Gardez les premiers essais roues décollées du sol et étalonnez les mêmes seuils, vitesses et durées de pivot sur le robot.

Les commentaires de ce fichier s'adressent aux débutants venant de la programmation par blocs : commencez par les repères Python et les réglages en tête de fichier, puis suivez les personnages jusqu'aux trois boucles `basic.forever` à la fin. Chaque variable importante, chaque méthode et les décisions de sécurité sont expliquées sur place ; les commentaires ne changent pas le comportement du robot.

### Apprendre progressivement

Chaque fichier ci-dessous est un **programme complet et indépendant**, à copier seul dans l'éditeur JavaScript d'un nouveau projet MakeCode après import de l'extension. Ne copiez pas les cinq fichiers dans un même projet : ils redéfinissent les mêmes réglages et les mêmes boutons. Chaque étape ajoute une idée à la précédente :

1. [01 — avancer et s'arrêter](examples/apprendre-01-avancer.ts) : bouton A pour partir, B pour s'arrêter, ultrason pour arrêter devant un obstacle. `0` (aucun écho) provoque aussi l'arrêt.
2. [02 — nommer les actions](examples/apprendre-02-fonctions.ts) : même comportement, avec des réglages et de petites fonctions `avancer`, `arreter` et `obstacleDevant`.
3. [03 — les étapes du voyage](examples/apprendre-03-etapes.ts) : ajouter les étapes `Arret`, `Avance`, `Pivote` et `Urgence`. Un obstacle déclenche un pivot temporisé ; après deux pivots sans voie libre, le robot s'arrête.
4. [04 — sol et vitesse](examples/apprendre-04-capteurs.ts) : ne démarrer que lorsque les deux capteurs voient du blanc depuis une seconde, s'arrêter dès qu'un capteur voit du noir, et ralentir près d'un obstacle. Après une suspension, il faut de nouveau appuyer sur A.
5. [05 — une classe](examples/apprendre-05-classe.ts) : **même comportement que l'étape 4**, mais les souvenirs et les actions du robot sont rassemblés dans `RobotVoyageur`, toujours dans un seul fichier. C'est un choix pédagogique, pas une obligation de MakeCode.

Dans ces cinq étapes, A démarre (si les conditions le permettent), B arrête et A+B déclenche un arrêt d'urgence qui nécessite Reset. Les étapes 1 et 2 n'utilisent **pas** les capteurs de sol : faites les premiers essais roues décollées du sol, sous surveillance. À partir de l'étape 3, la durée du pivot est une estimation à étalonner : elle ne mesure pas l'angle réellement parcouru. L'étape 4 et la classe ne détectent pas les chocs et ne font pas la vérification ultrason après pivot de la version avancée. Pour étudier ces fonctions et les diagnostics série, passez ensuite à [la version avancée sans boussole](examples/voyage-autonome-sans-boussole.ts).

Dans la version avancée, `EtatTrajet` nomme les étapes ; les constantes en haut du fichier regroupent les principaux seuils et durées. `vitessePourDistance` décide de la vitesse, tandis que `reglerRoues` envoie la commande aux moteurs. Son comportement reste différent des étapes pédagogiques en cas d'absence d'écho **pendant l'avance** : elle conserve la vitesse maximale (voir ci-dessus). Tester tous ces programmes roues décollées du sol avant de les laisser rouler.

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
