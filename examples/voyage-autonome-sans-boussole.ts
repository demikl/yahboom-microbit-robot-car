const VITESSE_MIN = 45;
const VITESSE_MAX = 110;
const VITESSE_PIVOT = 25;
const VITESSE_PIVOT_REESSAI = 65;
const VITESSE_RECUL = 55;
const SEUIL_CHOC = 900; // Variation d'accélération, en milli-g, sur deux lectures consécutives.
const ACTIVER_CHOC_LATERAL = false;
const MS_PAR_90_DEGRES = 1000; // Hypothèse à étalonner sur le robot.
const SENS_FREINAGE_Z = 1; // Écran vers l'avant : inverser si les logs montrent le freinage en Z négatif.
const DISTANCE_OBSTACLE = 10;
const DISTANCE_RALENTISSEMENT = 60;
const MS_PAUSE_CHOC = 200;
const MS_RECUL = 350;
const MS_VERIFICATION = 900;
const MS_ENTRE_MESURES = 150;
const MS_AVANT_CHOC = 800;
const MS_NOIR = 200;
const MS_BLANC = 1000;
const MS_BOUCLE = 20;
const MS_VOIE_LIBRE = 500;
const MS_CLIGNOTANT = 400;
const COULEUR_CLIGNOTANT = 0xFF8000;
const PIXEL_GAUCHE = 1;
const PIXEL_DROIT = 3;
const MESURES_CONFIRMATION = 2;

enum EtatTrajet {
    Avance,
    PauseChoc,
    Recule,
    Pivote,
    ArretSecurite,
    VerifieDistance
}

let etat = EtatTrajet.Avance;
let horsSol = true;
let debutNoir = -1;
let debutBlanc = -1;
let finEtape = 0;
let prochainUltrason = 0;
let prochainRapportUltrason = 0;
let distance = 0;
let sensEvitement = 0;
let debutVoieLibre = -1;
let modeSignalActuel = 3;
let signalAllume = false;
let debutClignotement = 0;
let flecheHorsSolAffichee = false;
let vitesseGauche = -1;
let vitesseDroite = -1;
let chocDetecte = false;
let detectionChocActiveApres = 0;
let picLateral = 0;
let picFreinage = 0;
let picAcceleration = 0;
let prochainRapportChoc = 0;
let serieLaterale = 0;
let sensLateral = 0;
let serieFreinage = 0;
let dernierEchantillon = 0;
let picSerieLaterale = 0;
let picSerieFreinage = 0;
let tentativesPivot = 0;
let sensPivotPrecedent = MovementDirection.Clockwise;
let finVerification = 0;
let prochaineVerification = 0;
let lecturesProches = 0;
let lecturesLibres = 0;
let ligneGaucheNoire = false;
let ligneDroiteNoire = false;

function arreter(): void {
    RobotActionneurs.RobotMovement(MovementDirection.Stop);
    vitesseGauche = -1;
    vitesseDroite = -1;
}

function securite(message: string): void {
    etat = EtatTrajet.ArretSecurite;
    chocDetecte = false;
    arreter();
    actualiserSignaux();
    flecheHorsSolAffichee = false;
    serial.writeLine("ARRET SECURITE : " + message);
    basic.showIcon(IconNames.No);
}

function afficherFlecheHorsSol(): void {
    if (flecheHorsSolAffichee) return;
    basic.showIcon(IconNames.Cow);
    flecheHorsSolAffichee = true;
}

function effacerFlecheHorsSol(): void {
    if (!flecheHorsSolAffichee) return;
    flecheHorsSolAffichee = false;
    basic.clearScreen();
}

function actualiserSignaux(): void {
    let mode = 0;
    if (!horsSol && etat != EtatTrajet.ArretSecurite) {
        mode = etat == EtatTrajet.Avance ? sensEvitement : 2;
    }
    let maintenant = input.runningTime();
    let modeChange = mode != modeSignalActuel;
    if (modeChange) {
        modeSignalActuel = mode;
        debutClignotement = maintenant;
    }
    let allume = mode != 0 &&
        (maintenant - debutClignotement) % (2 * MS_CLIGNOTANT) < MS_CLIGNOTANT;
    if (!modeChange && allume == signalAllume) return;

    RobotAfficheurs.pixels_off();
    if (allume) {
        if (mode == -1 || mode == 2) RobotAfficheurs.pixel_on(PIXEL_GAUCHE, COULEUR_CLIGNOTANT);
        if (mode == 1 || mode == 2) RobotAfficheurs.pixel_on(PIXEL_DROIT, COULEUR_CLIGNOTANT);
    }
    if (allume && mode == 2) {
        RobotAfficheurs.bigRGBOn(COULEUR_CLIGNOTANT);
    } else {
        RobotAfficheurs.bigRGBOff();
    }
    signalAllume = allume;
}

function interruptionDemandee(): boolean {
    return etat == EtatTrajet.ArretSecurite || horsSol;
}

function nomEtat(): string {
    if (etat == EtatTrajet.Avance) return "avance";
    if (etat == EtatTrajet.PauseChoc) return "pause choc";
    if (etat == EtatTrajet.Recule) return "recule";
    if (etat == EtatTrajet.Pivote) return "pivote";
    if (etat == EtatTrajet.VerifieDistance) return "verifie distance";
    return "arret securite";
}

function commencerPivot(reessai: boolean = false): void {
    if (interruptionDemandee()) return;
    let angleVise = Math.randomRange(100, 170);
    if (!reessai) {
        sensPivotPrecedent = Math.randomRange(0, 1) == 0
            ? MovementDirection.Clockwise
            : MovementDirection.CounterClockwise;
    }
    tentativesPivot = reessai ? 2 : 1;
    let duree = Math.round(angleVise * MS_PAR_90_DEGRES / 90);
    let vitessePivot = reessai ? VITESSE_PIVOT_REESSAI : VITESSE_PIVOT;
    etat = EtatTrajet.Pivote;
    chocDetecte = false;

    RobotActionneurs.RobotMovement(sensPivotPrecedent, vitessePivot, 0);
    if (interruptionDemandee() || etat != EtatTrajet.Pivote) {
        arreter();
        return;
    }
    finEtape = input.runningTime() + duree;
    vitesseGauche = -1;
    vitesseDroite = -1;
    serial.writeLine("Pivot " + tentativesPivot + "/2 : " + angleVise +
        " degres estimes, " + duree + " ms, vitesse " + vitessePivot);
}

function commencerAvance(): void {
    if (interruptionDemandee()) return;
    etat = EtatTrajet.Avance;
    tentativesPivot = 0;
    chocDetecte = false;
    sensEvitement = 0;
    debutVoieLibre = -1;
    distance = 0;
    prochainUltrason = 0;
    prochainRapportUltrason = 0;
    detectionChocActiveApres = input.runningTime() + MS_AVANT_CHOC;
    vitesseGauche = -1;
    vitesseDroite = -1;
}

function vitessePourDistance(distanceMesuree: number): number {
    // Aucun écho conserve ici le comportement historique : vitesse maximale.
    if (distanceMesuree <= DISTANCE_OBSTACLE ||
        distanceMesuree >= DISTANCE_RALENTISSEMENT) return VITESSE_MAX;
    return VITESSE_MIN + Math.round(
        (distanceMesuree - DISTANCE_OBSTACLE) * (VITESSE_MAX - VITESSE_MIN) /
        (DISTANCE_RALENTISSEMENT - DISTANCE_OBSTACLE)
    );
}

function reglerRoues(gauche: number, droite: number): void {
    if (gauche == vitesseGauche && droite == vitesseDroite) return;
    RobotActionneurs.ChangeMotor(MotorSide.Left, MotorDirection.Forward, gauche, 0);
    RobotActionneurs.ChangeMotor(MotorSide.Right, MotorDirection.Forward, droite, 0);
    if (interruptionDemandee()) {
        arreter();
        return;
    }
    if (vitesseGauche < 0 && vitesseDroite < 0) {
        detectionChocActiveApres = input.runningTime() + MS_AVANT_CHOC;
    }
    vitesseGauche = gauche;
    vitesseDroite = droite;
}

// Écran vers l'avant : X est latéral, Z est longitudinal.
basic.forever(function () {
    let x = input.acceleration(Dimension.X);
    let z = input.acceleration(Dimension.Z);

    basic.pause(15);

    let suivantX = input.acceleration(Dimension.X);
    let suivantZ = input.acceleration(Dimension.Z);
    let deltaX = suivantX - x;
    let deltaZ = suivantZ - z;
    let lateral = Math.abs(deltaX);
    let freinage = SENS_FREINAGE_Z * deltaZ;

    let maintenant = input.runningTime();
    if (!horsSol && etat == EtatTrajet.Avance) {
        picLateral = Math.max(picLateral, lateral);
        picFreinage = Math.max(picFreinage, freinage);
        picAcceleration = Math.max(picAcceleration, -freinage);
        if (prochainRapportChoc == 0) prochainRapportChoc = maintenant + 200;

        if (maintenant >= detectionChocActiveApres && !chocDetecte) {
            if (dernierEchantillon == 0 || maintenant - dernierEchantillon > 80) {
                serieLaterale = 0;
                serieFreinage = 0;
                sensLateral = 0;
            }
            dernierEchantillon = maintenant;

            if (lateral >= SEUIL_CHOC) {
                let sens = deltaX > 0 ? 1 : -1;
                serieLaterale = sens == sensLateral ? serieLaterale + 1 : 1;
                sensLateral = sens;
            } else {
                serieLaterale = 0;
                sensLateral = 0;
            }
            serieFreinage = freinage >= SEUIL_CHOC ? serieFreinage + 1 : 0;
            picSerieLaterale = Math.max(picSerieLaterale, serieLaterale);
            picSerieFreinage = Math.max(picSerieFreinage, serieFreinage);

            if ((ACTIVER_CHOC_LATERAL && serieLaterale >= MESURES_CONFIRMATION) ||
                serieFreinage >= MESURES_CONFIRMATION) {
                chocDetecte = true;
                serial.writeLine("Choc confirme " +
                    (ACTIVER_CHOC_LATERAL && serieLaterale >= MESURES_CONFIRMATION ? "lateral" : "avant") +
                    " : dX=" + deltaX + " dZ=" + deltaZ + " mg (seuil " +
                    SEUIL_CHOC + " x" + MESURES_CONFIRMATION + ")");
            }
        } else {
            serieLaterale = 0;
            serieFreinage = 0;
            sensLateral = 0;
            dernierEchantillon = 0;
        }
        if (maintenant >= prochainRapportChoc) {
            serial.writeLine("200 ms : |dX|=" + picLateral +
                " freinZ=" + picFreinage + " accelZ=" + picAcceleration + " mg" +
                " suiteX=" + picSerieLaterale + " suiteFrein=" + picSerieFreinage +
                " detection=" + (maintenant >= detectionChocActiveApres ? "active" : "ignoree"));
            picLateral = 0;
            picFreinage = 0;
            picAcceleration = 0;
            picSerieLaterale = 0;
            picSerieFreinage = 0;
            prochainRapportChoc = maintenant + 200;
        }
    } else {
        picLateral = 0;
        picFreinage = 0;
        picAcceleration = 0;
        serieLaterale = 0;
        serieFreinage = 0;
        sensLateral = 0;
        dernierEchantillon = 0;
        picSerieLaterale = 0;
        picSerieFreinage = 0;
        prochainRapportChoc = 0;
    }
});

// A+B : arrêt d'urgence définitif jusqu'au bouton Reset.
input.onButtonPressed(Button.AB, function () {
    securite("boutons A+B");
});

serial.writeLine("Pret : poser le robot au sol");
basic.forever(function () {
    serial.writeLine("Etat : " + nomEtat() + " horsSol=" + horsSol +
        " ligneG=" + (ligneGaucheNoire ? "noir" : "blanc") +
        " ligneD=" + (ligneDroiteNoire ? "noir" : "blanc"));
    basic.pause(1000);
});
arreter();

basic.forever(function () {
    if (etat == EtatTrajet.ArretSecurite) {
        basic.pause(100);
        return;
    }

    let maintenant = input.runningTime();
    let noirGauche = RobotCapteurs.line_is_black(MotorSide.Left);
    let noirDroit = RobotCapteurs.line_is_black(MotorSide.Right);
    ligneGaucheNoire = noirGauche;
    ligneDroiteNoire = noirDroit;

    if (noirGauche && noirDroit) {
        debutBlanc = -1;
        if (debutNoir < 0) debutNoir = maintenant;

        if (!horsSol && maintenant - debutNoir >= MS_NOIR) {
            horsSol = true;
            chocDetecte = false;
            arreter();
            actualiserSignaux();
            afficherFlecheHorsSol();
            serial.writeLine("Suspendu : deux capteurs noirs");
        }
    } else {
        debutNoir = -1;
    }

    if (horsSol) {
        // Un seul capteur blanc ne suffit pas : il faut les deux.
        if (!noirGauche && !noirDroit) {
            if (debutBlanc < 0) debutBlanc = maintenant;
            if (maintenant - debutBlanc >= MS_BLANC) {
                horsSol = false;
                debutBlanc = -1;
                effacerFlecheHorsSol();
                commencerAvance();
                serial.writeLine("Reprise du trajet");
            }
        } else {
            debutBlanc = -1;
        }
        basic.pause(MS_BOUCLE);
        return;
    }

    if (etat == EtatTrajet.PauseChoc) {
        if (maintenant >= finEtape) {
            RobotActionneurs.RobotMovement(MovementDirection.Backward, VITESSE_RECUL, 0);
            if (interruptionDemandee()) {
                arreter();
                basic.pause(MS_BOUCLE);
                return;
            }
            etat = EtatTrajet.Recule;
            finEtape = input.runningTime() + MS_RECUL;
        }
    } else if (etat == EtatTrajet.Recule) {
        if (maintenant >= finEtape) {
            commencerPivot();
        }
    } else if (etat == EtatTrajet.Pivote) {
        if (maintenant >= finEtape) {
            arreter();
            if (interruptionDemandee()) {
                basic.pause(MS_BOUCLE);
                return;
            }
            etat = EtatTrajet.VerifieDistance;
            finVerification = input.runningTime() + MS_VERIFICATION;
            prochaineVerification = 0;
            lecturesProches = 0;
            lecturesLibres = 0;
            serial.writeLine("Pivot temporise termine : verification ultrason");
        }
    } else if (etat == EtatTrajet.VerifieDistance) {
        if (maintenant >= prochaineVerification) {
            let distanceVerifiee = RobotCapteurs.distance_cm();
            if (etat != EtatTrajet.VerifieDistance || horsSol) {
                basic.pause(MS_BOUCLE);
                return;
            }
            prochaineVerification = input.runningTime() + MS_ENTRE_MESURES;
            serial.writeLine("Apres pivot " + tentativesPivot + "/2 : " +
                distanceVerifiee + " cm" +
                (distanceVerifiee == 0 ? " (aucun echo)" : ""));
            if (distanceVerifiee == 0) {
                lecturesProches = 0;
                lecturesLibres = 0;
            } else if (distanceVerifiee <= DISTANCE_OBSTACLE) {
                lecturesProches++;
                lecturesLibres = 0;
            } else {
                lecturesLibres++;
                lecturesProches = 0;
            }
            if (lecturesLibres >= MESURES_CONFIRMATION) {
                serial.writeLine("Voie libre confirmee : reprise");
                commencerAvance();
            } else if (lecturesProches >= MESURES_CONFIRMATION) {
                if (tentativesPivot == 1) {
                    serial.writeLine("Obstacle persistant : pivot de secours");
                    commencerPivot(true);
                } else {
                    securite("obstacle persistant apres pivot de secours");
                }
            } else if (input.runningTime() >= finVerification) {
                securite("distance non confirmee apres pivot");
            }
        } else if (maintenant >= finVerification) {
            securite("distance non confirmee apres pivot");
        }
    } else {
        // Le choc prime sur l'évitement préventif.
        if (chocDetecte) {
            chocDetecte = false;
            arreter();
            if (interruptionDemandee()) {
                basic.pause(MS_BOUCLE);
                return;
            }
            tentativesPivot = 0;
            etat = EtatTrajet.PauseChoc;
            finEtape = input.runningTime() + MS_PAUSE_CHOC;
            serial.writeLine("Choc : arrêt, recul, puis pivot");
        } else {
            if (maintenant >= prochainUltrason) {
                distance = RobotCapteurs.distance_cm();
                if (interruptionDemandee()) {
                    basic.pause(MS_BOUCLE);
                    return;
                }
                let instantMesure = input.runningTime();
                prochainUltrason = instantMesure + MS_ENTRE_MESURES;
                if (distance > 0 && distance <= DISTANCE_OBSTACLE) {
                    serial.writeLine("Ultrason : obstacle a " + distance +
                        " cm (<=" + DISTANCE_OBSTACLE + "), pivot immediat");
                } else if (instantMesure >= prochainRapportUltrason) {
                    let situation = distance == 0 ? "aucun echo, vitesse max"
                        : distance < DISTANCE_RALENTISSEMENT ? "ralentissement et virage" : "voie libre, vitesse max";
                    serial.writeLine("Ultrason : " + distance + " cm, " + situation);
                    prochainRapportUltrason = instantMesure + 500;
                }
            }

            if (distance > 0 && distance <= DISTANCE_OBSTACLE) {
                // Pas de recul ni de pause pour un obstacle simplement détecté.
                commencerPivot();
            } else {
                let instant = input.runningTime();
                let evitementDistant = distance > DISTANCE_OBSTACLE &&
                    distance < DISTANCE_RALENTISSEMENT;
                if (evitementDistant) {
                    debutVoieLibre = -1;
                    if (sensEvitement == 0) {
                        sensEvitement = Math.randomRange(0, 1) == 0 ? -1 : 1;
                    }
                } else if (distance >= DISTANCE_RALENTISSEMENT) {
                    if (debutVoieLibre < 0) debutVoieLibre = instant;
                    if (instant - debutVoieLibre >= MS_VOIE_LIBRE) sensEvitement = 0;
                } else {
                    // Aucun écho ne confirme pas que la voie est libre.
                    debutVoieLibre = -1;
                }

                let vitesse = vitessePourDistance(distance);
                let supplement = evitementDistant
                    ? Math.round((DISTANCE_RALENTISSEMENT - distance) *
                        (VITESSE_MAX - VITESSE_MIN) /
                        (DISTANCE_RALENTISSEMENT - DISTANCE_OBSTACLE))
                    : 0;
                let gauche = vitesse + (sensEvitement == 1 ? supplement : 0);
                let droite = vitesse + (sensEvitement == -1 ? supplement : 0);

                reglerRoues(gauche, droite);
            }
        }
    }

    actualiserSignaux();
    basic.pause(MS_BOUCLE);
});
