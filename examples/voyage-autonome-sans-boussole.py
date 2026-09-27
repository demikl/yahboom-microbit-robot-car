# Bonjour Oceane ! Copie ce fichier SEUL dans l'editeur Python de MakeCode,
# apres avoir importe l'extension Yahboom de ce depot.
# Ce n'est pas le MicroPython classique : MakeCode fournit ici basic, input,
# RobotCapteurs, RobotActionneurs et RobotAfficheurs.
# Pose le robot droit au depart : les inclinaisons sont comparees a sa pose initiale.
# Premier essai : roues decollees du sol, avec un adulte a proximite.
#
# Repere "blocs -> Python" : def cree un bloc personnalise ; if / elif / else
# font des choix ; les lignes decalees vers la droite appartiennent au bloc.
# class fabrique un personnage qui garde ses propres souvenirs (self.xxx).
# __init__ est execute quand on cree le personnage ; self veut dire "moi".
# return quitte une fonction (parfois en rapportant une valeur).
# True / False veulent dire vrai / faux. Les noms TOUT_EN_MAJUSCULES sont
# des reglages a etalonner : ne les modifie pas tous a la fois !

# Vitesses des moteurs : l'extension attend une valeur entre 0 et 255.
VITESSE_MIN = 45                 # Rouler lentement pres d'un obstacle.
VITESSE_MAX = 110                # Rouler quand la route parait degagee.
VITESSE_PIVOT = 65               # Consigne constante pour chaque pivot.
VITESSE_RECUL = 55               # Vitesse de la courte marche arriere.
VARIATION_CHAMP_MAX = 35         # Variation maximale de la norme X/Z en %.
PAS_MAGNETIQUE_MAX = 30          # Saut d'angle maximal entre deux lectures.
MS_SANS_ROTATION = 500          # Arret si aucune rotation magnetique mesuree.

# Un choc est un changement BRUSQUE d'acceleration, mesure en milli-g.
SEUIL_CHOC = 900                 # Valeur a depasser deux fois pour confirmer.
ACTIVER_CHOC_LATERAL = False     # False : observer X sans reagir aux chocs de cote.
SENS_FREINAGE_Z = 1             # Inverser en -1 si le freinage pointe vers -Z.
SEUIL_INCLINAISON = 30          # Ecart en degres sur pitch ou roll.
MS_INCLINAISON = 200            # Eviter qu'une breve secousse suspende le robot.
MS_PIVOT_MAX = 3000            # Limite de securite du pivot mesure.

# L'ultrason mesure des centimetres ; 0 signifie qu'il n'a recu aucun echo.
DISTANCE_OBSTACLE = 10          # A 10 cm ou moins : arret, recul, pivot.
DISTANCE_RALENTISSEMENT = 60    # Entre 10 et 60 cm : ralentir et devier.

# MS signifie millisecondes : 1000 ms = 1 seconde.
MS_PAUSE_CHOC = 200             # Rester arrete avant de reculer.
MS_RECUL = 350                  # Duree de la marche arriere.
MS_VERIFICATION = 900           # Temps maximal pour confirmer la voie apres pivot.
MS_ENTRE_MESURES = 150          # Espacement des lectures ultrason.
MS_AVANT_CHOC = 800             # Ignorer les secousses du demarrage des moteurs.
MS_NOIR = 200                   # Deux capteurs noirs pendant 200 ms : suspension.
MS_BLANC = 1000                 # Deux capteurs blancs pendant 1 s : reprise.
MS_BOUCLE = 20                  # Petite pause entre deux tours de la boucle du trajet.
MS_VOIE_LIBRE = 500            # Attendre avant d'eteindre le clignotant.
MS_CLIGNOTANT = 400            # Duree de la phase allumee (puis 400 ms eteinte).
COULEUR_CLIGNOTANT = 0xFF8000  # Rouge + vert en notation hexadecimale = orange.
PIXEL_GAUCHE = 3               # Numero du NeoPixel sur le cote gauche.
PIXEL_DROIT = 1                # Numero du NeoPixel sur le cote droit.
PIXEL_DIAGNOSTIC = 2           # Reste allume pour montrer la cause de l'arret.
DIAG_AUCUN = 0x000000          # Eteint : trajet normal.
DIAG_INCLINAISON = 0x00FFFF    # Cyan : robot penche.
DIAG_SOL = 0x0000FF            # Bleu : deux capteurs de ligne noirs.
DIAG_CHOC = 0xFF0000           # Rouge : choc confirme.
DIAG_OBSTACLE = 0xFF8000       # Orange : obstacle proche.
DIAG_MAGNETIQUE = 0x8000FF     # Violet : mesure magnetique invalide.
DIAG_DISTANCE = 0xFFFF00       # Jaune : verification ultrason echouee.
DIAG_PIVOT = 0xFF0080          # Rose : delai maximal du pivot depasse.
DIAG_BOUTONS = 0xFFFFFF        # Blanc : arret demande par A+B.
MESURES_CONFIRMATION = 2       # Deux lectures coherentes avant de decider.

# Les nombres suivants sont des etiquettes pour les etapes du voyage.
# Une seule etape est active a la fois : c'est comme un bloc "si... sinon si".
AVANCE = 0                      # Le robot roule et observe.
PAUSE_CHOC = 1                  # Il attend, immobile, avant de reculer.
RECULE = 2                      # Il fait marche arriere.
PIVOTE = 3                      # Il tourne sur place.
ARRET_SECURITE = 4              # Il ne repartira qu'apres Reset.
VERIFIE_DISTANCE = 5            # Il controle l'espace apres un pivot.


class SentinelleDuSol:
    # La sentinelle lit les deux capteurs de ligne sous le robot.
    def __init__(self):
        self.hors_sol = True             # Au depart, ne pas rouler avant de verifier le sol.
        self.debut_noir = -1             # Heure du premier "deux noirs" ; -1 = pas commence.
        self.debut_blanc = -1            # Heure du premier "deux blancs" ; -1 = pas commence.
        self.debut_inclinaison = -1      # Debut d'une inclinaison durable.
        self.incline = False            # Le robot a bascule depuis sa pose initiale.
        self.pitch_initial = None       # Pose de reference au premier controle du sol.
        self.roll_initial = None
        self.ligne_gauche_noire = False  # Derniere couleur vue a gauche.
        self.ligne_droite_noire = False  # Derniere couleur vue a droite.

    def inspecter_le_sol(self, maintenant):
        # maintenant est le temps ecoule depuis Reset (en ms).
        # Retour : -1 = souleve, 1 = repose, 0 = aucun changement.
        self.ligne_gauche_noire = RobotCapteurs.line_is_black(MotorSide.LEFT)
        self.ligne_droite_noire = RobotCapteurs.line_is_black(MotorSide.RIGHT)
        pitch = input.rotation(Rotation.PITCH)
        roll = input.rotation(Rotation.ROLL)
        if self.pitch_initial is None:
            self.pitch_initial = pitch
            self.roll_initial = roll
        # L'ecart circulaire evite un faux basculement au passage de 180 a -180.
        ecart_pitch = abs((pitch - self.pitch_initial + 180) % 360 - 180)
        ecart_roll = abs((roll - self.roll_initial + 180) % 360 - 180)
        penche = ecart_pitch >= SEUIL_INCLINAISON or ecart_roll >= SEUIL_INCLINAISON
        if penche:
            if self.debut_inclinaison < 0:
                self.debut_inclinaison = maintenant
            if maintenant - self.debut_inclinaison >= MS_INCLINAISON:
                self.incline = True
        else:
            self.debut_inclinaison = -1
            self.incline = False

        if self.incline:
            self.debut_blanc = -1
            if not self.hors_sol:
                self.hors_sol = True
                return -1
            return 0

        # "and" signifie que les DEUX capteurs doivent voir du noir.
        if self.ligne_gauche_noire and self.ligne_droite_noire:
            self.debut_blanc = -1
            if self.debut_noir < 0:
                self.debut_noir = maintenant
            # Une seule lecture noire ne suffit pas : il faut attendre 200 ms.
            if not self.hors_sol and maintenant - self.debut_noir >= MS_NOIR:
                self.hors_sol = True
                return -1
        else:
            self.debut_noir = -1

        if self.hors_sol:
            # Pour repartir, les DEUX capteurs doivent voir du blanc et le robot etre droit.
            if not self.ligne_gauche_noire and not self.ligne_droite_noire and not penche:
                if self.debut_blanc < 0:
                    self.debut_blanc = maintenant
                if maintenant - self.debut_blanc >= MS_BLANC:
                    self.hors_sol = False
                    self.debut_blanc = -1
                    return 1
            else:
                self.debut_blanc = -1
        return 0


class VigieDesChocs:
    # La vigie compare deux lectures de l'accelerometre pour reperer un choc.
    def __init__(self):
        self.x = 0                          # Premiere lecture de l'axe gauche/droite.
        self.z = 0                          # Premiere lecture de l'axe avant/arriere.
        self.choc_detecte = False           # Alerte envoyee au capitaine.
        self.detection_active_apres = 0     # Heure a partir de laquelle on ecoute les chocs.
        self.pic_lateral = 0                # Plus grand |changement X| du rapport.
        self.pic_freinage = 0               # Plus grand freinage Z du rapport.
        self.pic_acceleration = 0           # Plus grande acceleration Z opposee.
        self.prochain_rapport = 0           # Heure du prochain bilan serie (toutes les 200 ms).
        self.serie_laterale = 0             # Chocs de cote consecutifs et de meme sens.
        self.sens_lateral = 0               # Sens du dernier choc de cote (-1, 0 ou 1).
        self.serie_freinage = 0             # Freinages consecutifs assez forts.
        self.dernier_echantillon = 0        # Heure de la derniere lecture examinee.
        self.pic_serie_laterale = 0         # Plus longue serie X dans le rapport.
        self.pic_serie_freinage = 0         # Plus longue serie Z dans le rapport.

    def preparer_le_depart(self):
        # Au demarrage des moteurs, leurs vibrations ne sont pas des collisions.
        self.choc_detecte = False
        self.detection_active_apres = input.running_time() + MS_AVANT_CHOC

    def oublier_le_choc(self):
        # Efface une alerte deja prise en charge par le capitaine.
        self.choc_detecte = False

    def reposer_les_instruments(self):
        # Si on ne roule pas, les anciens pics et series ne comptent plus.
        self.pic_lateral = 0
        self.pic_freinage = 0
        self.pic_acceleration = 0
        self.serie_laterale = 0
        self.serie_freinage = 0
        self.sens_lateral = 0
        self.dernier_echantillon = 0
        self.pic_serie_laterale = 0
        self.pic_serie_freinage = 0
        self.prochain_rapport = 0

    def prendre_premier_echantillon(self):
        # Le capitaine lui laissera 15 ms avant de lui demander la seconde lecture.
        self.x = input.acceleration(Dimension.X)
        self.z = input.acceleration(Dimension.Z)

    def ausculter_la_route(self, etat, hors_sol):
        # Axe X = gauche/droite ; axe Z = avant/arriere (ecran vers l'avant).
        # Deux photos a 15 ms d'intervalle donnent le changement d'acceleration.
        # etat et hors_sol sont lus APRES la pause : une urgence prime sur le choc.
        delta_x = input.acceleration(Dimension.X) - self.x  # Difference entre les deux X.
        delta_z = input.acceleration(Dimension.Z) - self.z  # Difference entre les deux Z.
        lateral = abs(delta_x)                    # abs enleve le signe : force de cote.
        freinage = SENS_FREINAGE_Z * delta_z       # Freinage vers l'avant.
        maintenant = input.running_time()         # Heure de cette mesure.

        if hors_sol or etat != AVANCE:
            self.reposer_les_instruments()
            return

        # max garde la plus grande valeur observee pour le journal serie.
        self.pic_lateral = max(self.pic_lateral, lateral)
        self.pic_freinage = max(self.pic_freinage, freinage)
        self.pic_acceleration = max(self.pic_acceleration, -freinage)
        if self.prochain_rapport == 0:
            self.prochain_rapport = maintenant + 200

        # Pour eviter une fausse alerte, deux fortes mesures proches sont exigees.
        if maintenant >= self.detection_active_apres and not self.choc_detecte:
            # Si plus de 80 ms separent les mesures, la serie recommence a zero.
            if self.dernier_echantillon == 0 or maintenant - self.dernier_echantillon > 80:
                self.serie_laterale = 0
                self.serie_freinage = 0
                self.sens_lateral = 0
            self.dernier_echantillon = maintenant
            if lateral >= SEUIL_CHOC:
                # La valeur 1 / -1 indique le sens de la secousse sur X.
                sens = 1 if delta_x > 0 else -1
                # "A if condition else B" est un petit bloc si/sinon sur une ligne.
                self.serie_laterale = self.serie_laterale + 1 if sens == self.sens_lateral else 1
                self.sens_lateral = sens
            else:
                self.serie_laterale = 0
                self.sens_lateral = 0
            self.serie_freinage = self.serie_freinage + 1 if freinage >= SEUIL_CHOC else 0
            self.pic_serie_laterale = max(self.pic_serie_laterale, self.serie_laterale)
            self.pic_serie_freinage = max(self.pic_serie_freinage, self.serie_freinage)

            # Les chocs X sont traces, mais desactives par defaut pour la reaction.
            if (ACTIVER_CHOC_LATERAL and self.serie_laterale >= MESURES_CONFIRMATION) or self.serie_freinage >= MESURES_CONFIRMATION:
                self.choc_detecte = True
                # Etiquette pour indiquer quel type de choc a ete confirme.
                type_choc = "lateral" if ACTIVER_CHOC_LATERAL and self.serie_laterale >= MESURES_CONFIRMATION else "avant"
                # str transforme les nombres en texte pour le moniteur serie.
                serial.write_line("Choc confirme " + type_choc + " : dX=" + str(delta_x) +
                                  " dZ=" + str(delta_z) + " mg (seuil " +
                                  str(SEUIL_CHOC) + " x" + str(MESURES_CONFIRMATION) + ")")
        else:
            self.serie_laterale = 0
            self.serie_freinage = 0
            self.sens_lateral = 0
            self.dernier_echantillon = 0

        if maintenant >= self.prochain_rapport:
            # Le rapport montre meme les secousses qui n'ont pas declenche d'alerte.
            detection = "active" if maintenant >= self.detection_active_apres else "ignoree"
            serial.write_line("200 ms : |dX|=" + str(self.pic_lateral) +
                              " freinZ=" + str(self.pic_freinage) +
                              " accelZ=" + str(self.pic_acceleration) + " mg" +
                              " suiteX=" + str(self.pic_serie_laterale) +
                              " suiteFrein=" + str(self.pic_serie_freinage) +
                              " detection=" + detection)
            self.pic_lateral = 0
            self.pic_freinage = 0
            self.pic_acceleration = 0
            self.pic_serie_laterale = 0
            self.pic_serie_freinage = 0
            self.prochain_rapport = maintenant + 200


class EclaireurUltrason:
    # L'eclaireur utilise l'ultrason pour proposer vitesse et direction.
    def __init__(self):
        self.distance = 0                    # Derniere mesure en cm ; 0 = aucun echo.
        self.prochain_ultrason = 0           # Heure de la prochaine lecture en roulant.
        self.prochain_rapport = 0            # Heure du prochain message ultrason.
        self.sens_evitement = 0              # -1 = gauche ; 0 = droit ; 1 = droite.
        self.debut_voie_libre = -1           # Heure ou la distance est redevenue >= 60 cm.
        self.prochaine_verification = 0      # Heure de la prochaine lecture apres pivot.
        self.lectures_proches = 0            # Nombre d'obstacles vus a la suite.
        self.lectures_libres = 0             # Nombre de voies libres vues a la suite.
        self.vitesse_gauche = VITESSE_MAX    # Vitesse proposee pour la roue gauche.
        self.vitesse_droite = VITESSE_MAX    # Vitesse proposee pour la roue droite.

    def reprendre_la_route(self):
        # Reinitialise les anciennes mesures et le clignotant pour un nouveau depart.
        self.sens_evitement = 0
        self.debut_voie_libre = -1
        self.distance = 0
        self.prochain_ultrason = 0
        self.prochain_rapport = 0

    def scruter_la_route(self, maintenant):
        # On ne mesure pas en continu ; True signifie "nouvelle mesure faite".
        # Le capitaine verifie la securite AVANT que la mesure soit interpretee.
        if maintenant < self.prochain_ultrason:
            return False
        self.distance = RobotCapteurs.distance_cm()
        return True

    def raconter_la_route(self):
        # Appelee seulement si la mesure n'a pas ete interrompue.
        instant = input.running_time()       # Heure APRES l'appel au capteur.
        self.prochain_ultrason = instant + MS_ENTRE_MESURES
        # Un obstacle tout proche est signale tout de suite ; sinon un bilan
        # toutes les 500 ms suffit pour ne pas saturer le moniteur serie.
        if self.distance > 0 and self.distance <= DISTANCE_OBSTACLE:
            serial.write_line("Ultrason : obstacle a " + str(self.distance) +
                              " cm (<=" + str(DISTANCE_OBSTACLE) + ")")
        elif instant >= self.prochain_rapport:
            if self.distance == 0:
                situation = "aucun echo, vitesse max"
            elif self.distance < DISTANCE_RALENTISSEMENT:
                situation = "ralentissement et virage"
            else:
                situation = "voie libre, vitesse max"
            serial.write_line("Ultrason : " + str(self.distance) + " cm, " + situation)
            self.prochain_rapport = instant + 500

    def calculer_l_allure(self, maintenant):
        # Cette fonction CALCULE les vitesses, mais ne commande pas les roues.
        distance = self.distance  # Raccourci pour la derniere mesure.
        evitement_distant = distance > DISTANCE_OBSTACLE and distance < DISTANCE_RALENTISSEMENT
        if evitement_distant:
            self.debut_voie_libre = -1
            if self.sens_evitement == 0:
                # randint choisit au hasard 0 ou 1, donc un cote une seule fois.
                self.sens_evitement = -1 if randint(0, 1) == 0 else 1
        elif distance >= DISTANCE_RALENTISSEMENT:
            if self.debut_voie_libre < 0:
                self.debut_voie_libre = maintenant
            # Ne pas effacer le clignotant pour une seule mesure lointaine.
            if maintenant - self.debut_voie_libre >= MS_VOIE_LIBRE:
                self.sens_evitement = 0
        else:
            # Aucun echo ne confirme pas que la voie est libre.
            self.debut_voie_libre = -1

        # Entre 10 et 60 cm, une interpolation fait grandir progressivement
        # la vitesse de VITESSE_MIN a VITESSE_MAX ; Math.round arrondit.
        # A 0 cm (pas d'echo), le comportement de cet exemple reste vitesse max.
        if distance <= DISTANCE_OBSTACLE or distance >= DISTANCE_RALENTISSEMENT:
            vitesse = VITESSE_MAX
        else:
            vitesse = VITESSE_MIN + Math.round((distance - DISTANCE_OBSTACLE) *
                                               (VITESSE_MAX - VITESSE_MIN) /
                                               (DISTANCE_RALENTISSEMENT - DISTANCE_OBSTACLE))
        # Un supplement sur UNE roue fait tourner le robot tout en avancant.
        # Plus l'obstacle est proche, plus cette difference est grande.
        supplement = 0
        if evitement_distant:
            supplement = Math.round((DISTANCE_RALENTISSEMENT - distance) *
                                    (VITESSE_MAX - VITESSE_MIN) /
                                    (DISTANCE_RALENTISSEMENT - DISTANCE_OBSTACLE))
        self.vitesse_gauche = vitesse + (supplement if self.sens_evitement == 1 else 0)
        self.vitesse_droite = vitesse + (supplement if self.sens_evitement == -1 else 0)

    def preparer_la_verification(self):
        # Apres un pivot, oublier les lectures precedentes : il faut deux
        # NOUVELLES lectures consecutives pour prendre une decision.
        self.prochaine_verification = 0
        self.lectures_proches = 0
        self.lectures_libres = 0

    def mesurer_l_issue(self):
        # Seule la lecture a lieu ici ; le capitaine controle ensuite l'urgence.
        return RobotCapteurs.distance_cm()

    def verifier_l_issue(self, tentative, distance):
        # tentative vaut 1 (premier pivot) ou 2 (dernier essai).
        # Retour : 1 = voie libre, -1 = obstacle, 0 = pas encore confirme.
        # distance est la mesure en cm lue juste avant par mesurer_l_issue.
        self.prochaine_verification = input.running_time() + MS_ENTRE_MESURES
        suffixe = " (aucun echo)" if distance == 0 else ""  # Precision dans le journal.
        serial.write_line("Apres pivot " + str(tentative) + "/2 : " +
                          str(distance) + " cm" + suffixe)
        # Une lecture 0 n'est NI "voie libre" NI "obstacle" : elle annule
        # les series. Si la verification dure trop, le capitaine arretera.
        if distance == 0:
            self.lectures_proches = 0
            self.lectures_libres = 0
        elif distance <= DISTANCE_OBSTACLE:
            self.lectures_proches += 1
            self.lectures_libres = 0
        else:
            self.lectures_libres += 1
            self.lectures_proches = 0
        if self.lectures_libres >= MESURES_CONFIRMATION:
            return 1
        if self.lectures_proches >= MESURES_CONFIRMATION:
            return -1
        return 0


class MecanicienDesRoues:
    # Seul le mecanicien commande directement les moteurs de l'extension.
    def __init__(self):
        self.vitesse_gauche = -1     # Derniere consigne envoyee ; -1 = inconnue.
        self.vitesse_droite = -1     # Idem pour le moteur droit.

    def immobiliser(self):
        # STOP arrete les deux roues ; les prochaines vitesses seront renvoyees.
        RobotActionneurs.robot_movement(MovementDirection.STOP)
        self.vitesse_gauche = -1
        self.vitesse_droite = -1

    def reculer(self):
        # Le 0 final veut dire "continuer jusqu'a une autre commande".
        # Le capitaine controlera la securite juste apres cet ordre.
        RobotActionneurs.robot_movement(MovementDirection.BACKWARD, VITESSE_RECUL, 0)

    def pivoter(self, sens, vitesse):
        # sens = horaire ou anti-horaire ; vitesse est un reglage de moteur.
        # Le capitaine controlera la securite juste apres cet ordre.
        RobotActionneurs.robot_movement(sens, vitesse, 0)
        self.vitesse_gauche = -1
        self.vitesse_droite = -1

    def regler_les_roues(self, gauche, droite):
        # gauche et droite sont les vitesses PROPOSEES par l'eclaireur.
        # True en retour signifie que les roues etaient arretees juste avant.
        if gauche == self.vitesse_gauche and droite == self.vitesse_droite:
            return False
        RobotActionneurs.change_motor(MotorSide.LEFT, MotorDirection.FORWARD, gauche, 0)
        RobotActionneurs.change_motor(MotorSide.RIGHT, MotorDirection.FORWARD, droite, 0)
        demarrage = self.vitesse_gauche < 0 and self.vitesse_droite < 0
        self.vitesse_gauche = gauche
        self.vitesse_droite = droite
        return demarrage


class SignaleurDesLumieres:
    # Le signaleur gere NeoPixels, phares et icones de l'ecran micro:bit.
    def __init__(self):
        self.mode_actuel = 3              # Mode precedent ; 3 force le premier rafraichissement.
        self.signal_allume = False        # Phase allumee ou eteinte du clignotement.
        self.debut_clignotement = 0       # Heure du dernier changement de mode.
        self.fleche_hors_sol_affichee = False  # Evite de redessiner la vache sans cesse.
        self.diagnostic = DIAG_AUCUN

    def definir_le_diagnostic(self, couleur):
        if couleur != self.diagnostic:
            self.diagnostic = couleur
            RobotAfficheurs.pixel_on(PIXEL_DIAGNOSTIC, couleur)

    def montrer_la_suspension(self):
        # La vache est le dessin choisi pour dire "robot souleve".
        if not self.fleche_hors_sol_affichee:
            basic.show_icon(IconNames.COW)
            self.fleche_hors_sol_affichee = True

    def effacer_la_suspension(self):
        # Ne rien effacer si la vache n'est pas presente : garder l'icone urgence.
        if self.fleche_hors_sol_affichee:
            self.fleche_hors_sol_affichee = False
            basic.clear_screen()

    def marquer_l_urgence(self):
        # L'icone "non" reste sur l'ecran jusqu'au Reset.
        self.fleche_hors_sol_affichee = False
        basic.show_icon(IconNames.NO)

    def agiter_les_signaux(self, hors_sol, etat, sens_evitement):
        # Parametres : hors_sol et etat viennent de la sentinelle/du capitaine ;
        # sens_evitement vient de l'eclaireur.
        # Mode 0 = eteint ; -1 = gauche ; 1 = droite ; 2 = warnings.
        mode = 0
        if not hors_sol and etat != ARRET_SECURITE:
            mode = sens_evitement if etat == AVANCE else 2
        maintenant = input.running_time()    # Heure utilisee pour clignoter.
        mode_change = mode != self.mode_actuel  # Un nouveau mode repart en phase allumee.
        if mode_change:
            self.mode_actuel = mode
            self.debut_clignotement = maintenant
        # % donne le reste d'une division : de 0 a 399 ms, allume ;
        # de 400 a 799 ms, eteint ; puis le cycle recommence.
        allume = mode != 0 and (maintenant - self.debut_clignotement) % (2 * MS_CLIGNOTANT) < MS_CLIGNOTANT
        if not mode_change and allume == self.signal_allume:
            return
        # On efface avant de rallumer uniquement les pixels utiles.
        RobotAfficheurs.pixels_off()
        if self.diagnostic != DIAG_AUCUN:
            RobotAfficheurs.pixel_on(PIXEL_DIAGNOSTIC, self.diagnostic)
        if allume:
            if mode == -1 or mode == 2:
                RobotAfficheurs.pixel_on(PIXEL_GAUCHE, COULEUR_CLIGNOTANT)
            if mode == 1 or mode == 2:
                RobotAfficheurs.pixel_on(PIXEL_DROIT, COULEUR_CLIGNOTANT)
        # Les deux phares s'allument ensemble seulement en mode warnings.
        if allume and mode == 2:
            RobotAfficheurs.big_rgb_on(COULEUR_CLIGNOTANT)
        else:
            RobotAfficheurs.big_rgb_off()
        self.signal_allume = allume


class CapitaineDuVoyage:
    # Le capitaine fait travailler les autres personnages dans le bon ordre.
    # Il garde en memoire l'etape du voyage : comme une machine a etats en blocs.
    def __init__(self):
        self.etat = AVANCE                         # Etape actuelle ; pas de marche tant que hors_sol.
        self.sentinelle = SentinelleDuSol()        # Personnage responsable du sol.
        self.vigie = VigieDesChocs()               # Elle signale les chocs sans piloter.
        self.eclaireur = EclaireurUltrason()       # Il propose les vitesses et les virages.
        self.mecanicien = MecanicienDesRoues()     # Il envoie les commandes aux moteurs.
        self.signaleur = SignaleurDesLumieres()    # Il commande les lumieres.
        self.fin_etape = 0                         # Heure prevue pour terminer recul/pause.
        self.fin_verification = 0                  # Limite de temps apres pivot.
        self.tentatives_pivot = 0                  # 0 avant pivot, 1 puis 2 au dernier essai.
        self.sens_pivot_precedent = MovementDirection.CLOCKWISE  # Garde le meme sens au reessai.
        self.angle_vise = 0
        self.angle_parcouru = 0
        self.champ_x = 0
        self.champ_z = 0
        self.norme_champ = 0
        self.debut_pivot = 0
        self.dernier_progres = 0

    def interruption_demandee(self):
        # "or" signifie qu'une SEULE des deux conditions suffit pour stopper.
        return self.etat == ARRET_SECURITE or self.sentinelle.hors_sol

    def declarer_l_urgence(self, message, diagnostic):
        # message indique pourquoi on s'arrete : "boutons A+B" ou une route
        # incertaine apres pivot. STOP definitif jusqu'au bouton Reset.
        if self.etat == ARRET_SECURITE:
            return
        self.etat = ARRET_SECURITE
        self.vigie.oublier_le_choc()
        self.mecanicien.immobiliser()
        self.signaleur.definir_le_diagnostic(diagnostic)
        self.signaleur.agiter_les_signaux(self.sentinelle.hors_sol, self.etat,
                                          self.eclaireur.sens_evitement)
        serial.write_line("ARRET SECURITE : " + message)
        self.signaleur.marquer_l_urgence()

    def lancer_l_evitement(self, raison, diagnostic):
        # raison est le texte "Choc" ou "Obstacle proche" pour le journal.
        # Programme une PAUSE sans bloquer le reste du robot avec un long delai.
        self.mecanicien.immobiliser()
        if self.interruption_demandee():
            return
        self.vigie.oublier_le_choc()
        self.tentatives_pivot = 0
        self.etat = PAUSE_CHOC
        self.fin_etape = input.running_time() + MS_PAUSE_CHOC
        self.signaleur.definir_le_diagnostic(diagnostic)
        serial.write_line(raison + " : arret, recul, puis pivot")

    def ordonner_un_pivot(self, reessai=False):
        # Le second pivot contourne l'obstacle avec la MEME vitesse que le premier.
        if self.interruption_demandee():
            return
        # La carte est verticale (ecran vers l'avant) : X et Z sont horizontaux.
        x = input.magnetic_force(Dimension.X)
        z = input.magnetic_force(Dimension.Z)
        if self.interruption_demandee():
            return
        norme = x * x + z * z
        if norme == 0:
            self.declarer_l_urgence("champ magnetique horizontal nul", DIAG_MAGNETIQUE)
            return
        self.angle_vise = randint(100, 170)
        if not reessai:
            # Le premier sens est aleatoire ; le deuxieme garde le meme sens.
            self.sens_pivot_precedent = (MovementDirection.CLOCKWISE if randint(0, 1) == 0
                                         else MovementDirection.COUNTER_CLOCKWISE)
        self.tentatives_pivot = 2 if reessai else 1
        self.angle_parcouru = 0
        self.champ_x = x
        self.champ_z = z
        self.norme_champ = norme
        self.etat = PIVOTE
        self.vigie.oublier_le_choc()
        self.mecanicien.pivoter(self.sens_pivot_precedent, VITESSE_PIVOT)
        # Un autre evenement peut avoir interrompu le mouvement entre-temps.
        if self.interruption_demandee() or self.etat != PIVOTE:
            self.mecanicien.immobiliser()
            return
        self.debut_pivot = input.running_time()
        self.dernier_progres = self.debut_pivot
        serial.write_line("Pivot " + str(self.tentatives_pivot) + "/2 : " +
                          "cible magnetique " + str(self.angle_vise) +
                          " degres, vitesse " + str(VITESSE_PIVOT))

    def suivre_le_pivot(self, maintenant):
        # Le delai prime sur la lecture : ne jamais prolonger un pivot bloque.
        if maintenant - self.debut_pivot >= MS_PIVOT_MAX:
            self.declarer_l_urgence("pivot non confirme dans le delai maximal", DIAG_PIVOT)
            return
        x = input.magnetic_force(Dimension.X)
        z = input.magnetic_force(Dimension.Z)
        if self.interruption_demandee() or self.etat != PIVOTE:
            self.mecanicien.immobiliser()
            return
        norme = x * x + z * z
        if (norme == 0 or
            abs(norme - self.norme_champ) * 100 > VARIATION_CHAMP_MAX * self.norme_champ):
            self.declarer_l_urgence("champ magnetique instable pendant le pivot", DIAG_MAGNETIQUE)
            return
        # atan2 du produit vectoriel et scalaire donne un pas signe sur X/Z.
        # Vu de dessus, le champ tourne dans le sens oppose au robot.
        croise = self.champ_x * z - self.champ_z * x
        scalaire = self.champ_x * x + self.champ_z * z
        pas = Math.atan2(croise, scalaire) * 180 / Math.PI
        if self.sens_pivot_precedent == MovementDirection.COUNTER_CLOCKWISE:
            pas = -pas
        if abs(pas) > PAS_MAGNETIQUE_MAX:
            self.declarer_l_urgence("saut magnetique pendant le pivot", DIAG_MAGNETIQUE)
            return
        self.angle_parcouru = max(0, self.angle_parcouru + pas)
        self.champ_x = x
        self.champ_z = z
        if pas >= 1:
            self.dernier_progres = input.running_time()
        if self.angle_parcouru >= self.angle_vise:
            self.mecanicien.immobiliser()
            if self.interruption_demandee():
                return
            self.etat = VERIFIE_DISTANCE
            self.fin_verification = input.running_time() + MS_VERIFICATION
            self.eclaireur.preparer_la_verification()
            serial.write_line("Pivot magnetique : " + str(Math.round(self.angle_parcouru)) +
                              " degres, verification ultrason")
        elif input.running_time() - self.dernier_progres >= MS_SANS_ROTATION:
            self.declarer_l_urgence("pivot sans rotation magnetique", DIAG_MAGNETIQUE)

    def reprendre_la_marche(self):
        # Repart apres une suspension ou une voie libre CONFIRMEE apres pivot.
        if self.interruption_demandee():
            return
        self.etat = AVANCE
        self.signaleur.definir_le_diagnostic(DIAG_AUCUN)
        self.tentatives_pivot = 0
        self.vigie.oublier_le_choc()
        self.eclaireur.reprendre_la_route()
        self.vigie.preparer_le_depart()
        self.mecanicien.vitesse_gauche = -1
        self.mecanicien.vitesse_droite = -1

    def raconter_le_voyage(self):
        # Traduit le numero d'etape en mots pour le moniteur serie.
        if self.etat == AVANCE:
            nom = "avance"
        elif self.etat == PAUSE_CHOC:
            nom = "pause choc"
        elif self.etat == RECULE:
            nom = "recule"
        elif self.etat == PIVOTE:
            nom = "pivote"
        elif self.etat == VERIFIE_DISTANCE:
            nom = "verifie distance"
        else:
            nom = "arret securite"
        sol = "true" if self.sentinelle.hors_sol else "false"  # Etat de la securite sol.
        gauche = "noir" if self.sentinelle.ligne_gauche_noire else "blanc"  # Capteur gauche.
        droite = "noir" if self.sentinelle.ligne_droite_noire else "blanc"  # Capteur droit.
        # La pause espace les rapports : une fois par seconde, meme a l'arret.
        serial.write_line("Etat : " + nom + " horsSol=" + sol +
                          " ligneG=" + gauche + " ligneD=" + droite)
        basic.pause(1000)

    def mener_une_etape(self):
        # Un appel = UN tour de la machine a etats, jamais tout le voyage.
        # "return" empeche de redemarrer apres l'urgence.
        if self.etat == ARRET_SECURITE:
            basic.pause(100)
            return

        maintenant = input.running_time()  # Heure utilisee pour les delais.
        changement_sol = self.sentinelle.inspecter_le_sol(maintenant)  # -1, 0 ou 1.
        if self.sentinelle.hors_sol:
            if self.sentinelle.incline:
                self.signaleur.definir_le_diagnostic(DIAG_INCLINAISON)
            elif self.sentinelle.ligne_gauche_noire and self.sentinelle.ligne_droite_noire:
                self.signaleur.definir_le_diagnostic(DIAG_SOL)
        if changement_sol == -1:
            # Sol ou inclinaison suspects : STOP et dessin de la vache.
            self.vigie.oublier_le_choc()
            self.mecanicien.immobiliser()
            self.signaleur.agiter_les_signaux(True, self.etat, self.eclaireur.sens_evitement)
            self.signaleur.montrer_la_suspension()
            serial.write_line("Suspendu : capteurs noirs ou inclinaison")

        if self.sentinelle.hors_sol:
            # Tant que les deux blancs ne sont pas confirmes, ne pas avancer.
            basic.pause(MS_BOUCLE)
            return
        if changement_sol == 1:
            # Deux blancs et robot redresse pendant 1 seconde : reprise.
            self.signaleur.effacer_la_suspension()
            self.reprendre_la_marche()
            serial.write_line("Reprise du trajet")

        # Chaque branche correspond a UNE etape, comme des blocs si / sinon si.
        # On compare l'heure actuelle a une heure limite, sans immobiliser
        # le programme avec une pause de plusieurs centaines de ms.
        if self.etat == PAUSE_CHOC:
            if maintenant >= self.fin_etape:
                self.mecanicien.reculer()
                if self.interruption_demandee():
                    self.mecanicien.immobiliser()
                    basic.pause(MS_BOUCLE)
                    return
                # Pause terminee : marche arriere pendant MS_RECUL.
                self.etat = RECULE
                self.fin_etape = input.running_time() + MS_RECUL
        elif self.etat == RECULE:
            # Marche arriere terminee : demander un pivot.
            if maintenant >= self.fin_etape:
                self.ordonner_un_pivot()
        elif self.etat == PIVOTE:
            self.suivre_le_pivot(maintenant)
        elif self.etat == VERIFIE_DISTANCE:
            # Deux mesures libres font repartir ; deux proches provoquent
            # un seul pivot de secours, puis un arret si elles restent proches.
            if maintenant >= self.eclaireur.prochaine_verification:
                distance_verifiee = self.eclaireur.mesurer_l_issue()  # cm, ou 0 sans echo.
                # Le bouton A+B peut changer l'etat pendant la lecture.
                if self.etat != VERIFIE_DISTANCE or self.sentinelle.hors_sol:
                    basic.pause(MS_BOUCLE)
                    return
                issue = self.eclaireur.verifier_l_issue(self.tentatives_pivot,
                                                        distance_verifiee)  # 1, 0 ou -1.
                if issue == 1:
                    serial.write_line("Voie libre confirmee : reprise")
                    self.reprendre_la_marche()
                elif issue == -1:
                    if self.tentatives_pivot == 1:
                        serial.write_line("Obstacle persistant : nouveau pivot magnetique")
                        self.ordonner_un_pivot(True)
                    else:
                        self.declarer_l_urgence("obstacle persistant apres pivot de secours",
                                                 DIAG_DISTANCE)
                elif input.running_time() >= self.fin_verification:
                    # Trop de mesures 0 ou contradictoires : arret prudent.
                    self.declarer_l_urgence("distance non confirmee apres pivot", DIAG_DISTANCE)
            elif maintenant >= self.fin_verification:
                self.declarer_l_urgence("distance non confirmee apres pivot", DIAG_DISTANCE)
        else:
            # Pendant AVANCE, un choc passe avant la detection ultrason.
            if self.vigie.choc_detecte:
                self.lancer_l_evitement("Choc", DIAG_CHOC)
            else:
                nouvelle_mesure = self.eclaireur.scruter_la_route(maintenant)
                if self.interruption_demandee():
                    basic.pause(MS_BOUCLE)
                    return
                if nouvelle_mesure:
                    self.eclaireur.raconter_la_route()
                if 0 < self.eclaireur.distance <= DISTANCE_OBSTACLE:
                    self.lancer_l_evitement("Obstacle proche", DIAG_OBSTACLE)
                else:
                    # L'eclaireur propose, le mecanicien actionne les roues.
                    self.eclaireur.calculer_l_allure(input.running_time())
                    demarrage = self.mecanicien.regler_les_roues(
                        self.eclaireur.vitesse_gauche, self.eclaireur.vitesse_droite)
                    if self.interruption_demandee():
                        self.mecanicien.immobiliser()
                        basic.pause(MS_BOUCLE)
                        return
                    # Ignorer les secousses pendant les 800 ms qui suivent un depart.
                    if demarrage:
                        self.vigie.preparer_le_depart()

        # Actualiser les clignotants a chaque tour, puis laisser du temps
        # aux autres boucles et aux evenements (bouton, chocs, rapport).
        self.signaleur.agiter_les_signaux(self.sentinelle.hors_sol, self.etat,
                                          self.eclaireur.sens_evitement)
        basic.pause(MS_BOUCLE)

# Une seule equipe de personnages pour tout ce programme.
capitaine = CapitaineDuVoyage()


def bouton_urgence():
    # Fonction appelee automatiquement quand on presse A+B.
    capitaine.declarer_l_urgence("boutons A+B", DIAG_BOUTONS)


def boucle_des_chocs():
    # Equivalent d'un bloc "toujours" : observer l'accelerometre.
    capitaine.vigie.prendre_premier_echantillon()
    basic.pause(15)
    # Lire l'etat APRES la pause : une urgence survenue entre deux mesures
    # empeche la vigie de compter un nouveau choc.
    capitaine.vigie.ausculter_la_route(capitaine.etat, capitaine.sentinelle.hors_sol)


def boucle_du_rapport():
    # Un autre "toujours" : raconter l'etat du robot chaque seconde.
    capitaine.raconter_le_voyage()


def boucle_du_trajet():
    # Un troisieme "toujours" : decider de la prochaine action.
    capitaine.mener_une_etape()


# On DONNE les noms de fonctions aux blocs evenementiels, sans parentheses :
# MakeCode les rappellera plus tard. Avec des parentheses, elles seraient
# executees tout de suite au lieu d'etre enregistrees !
input.on_button_pressed(Button.AB, bouton_urgence)
capitaine.mecanicien.immobiliser()
serial.write_line("Pret : poser le robot droit au sol")
basic.forever(boucle_des_chocs)
basic.forever(boucle_du_rapport)
basic.forever(boucle_du_trajet)
