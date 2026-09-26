const VITESSE_MIN = 45;
const VITESSE_MAX = 110;
const VITESSE_PIVOT = 25;
const VITESSE_PIVOT_REESSAI = 65;
const VITESSE_RECUL = 55;
const SEUIL_CHOC = 900; // Variation d'accélération, en milli-g, sur deux lectures consécutives.
const ACTIVER_CHOC_LATERAL = false;
const MS_PAR_90_DEGRES = 1000; // Hypothèse à étalonner sur le robot.
const SENS_FREINAGE_Z = 1; // Écran vers l'avant : inverser si les logs montrent le freinage en Z négatif.

let etat = 0; // 0=avance, 1=pause choc, 2=recule, 3=pivote, 4=arrêt sécurité, 5=vérifie distance
let horsSol = true;
let debutNoir = -1;
let debutBlanc = -1;
let finEtape = 0;
let prochainUltrason = 0;
let prochainRapportUltrason = 0;
let prochaineCourbe = 0;
let courbe = 0;
let distance = 0;
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

function arreter(): void {
    RobotActionneurs.RobotMovement(MovementDirection.Stop);
    vitesseGauche = -1;
    vitesseDroite = -1;
}

function securite(message: string): void {
    etat = 4;
    chocDetecte = false;
    arreter();
    serial.writeLine("ARRET SECURITE : " + message);
    basic.showIcon(IconNames.No);
}

function interruptionDemandee(): boolean {
    return etat == 4 || horsSol;
}

function commencerPivot(reessai: boolean = false): void {
    if (etat == 4 || horsSol) return;
    let angleVise = Math.randomRange(100, 170);
    if (!reessai) {
        sensPivotPrecedent = Math.randomRange(0, 1) == 0
            ? MovementDirection.Clockwise
            : MovementDirection.CounterClockwise;
    }
    tentativesPivot = reessai ? 2 : 1;
    let duree = Math.round(angleVise * MS_PAR_90_DEGRES / 90);
    let vitessePivot = reessai ? VITESSE_PIVOT_REESSAI : VITESSE_PIVOT;
    etat = 3;
    chocDetecte = false;

    RobotActionneurs.RobotMovement(sensPivotPrecedent, vitessePivot, 0);
    if (etat != 3 || horsSol) {
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
    if (etat == 4 || horsSol) return;
    etat = 0;
    tentativesPivot = 0;
    chocDetecte = false;
    prochaineCourbe = 0;
    prochainUltrason = 0;
    prochainRapportUltrason = 0;
    detectionChocActiveApres = input.runningTime() + 800;
    vitesseGauche = -1;
    vitesseDroite = -1;
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
    if (!horsSol && etat == 0) {
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

            if ((ACTIVER_CHOC_LATERAL && serieLaterale >= 2) || serieFreinage >= 2) {
                chocDetecte = true;
                serial.writeLine("Choc confirme " +
                    (ACTIVER_CHOC_LATERAL && serieLaterale >= 2 ? "lateral" : "avant") +
                    " : dX=" + deltaX + " dZ=" + deltaZ + " mg (seuil " + SEUIL_CHOC + " x2)");
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

arreter();
serial.writeLine("Pret : poser le robot au sol");

basic.forever(function () {
    if (etat == 4) {
        basic.pause(100);
        return;
    }

    let maintenant = input.runningTime();
    let noirGauche = RobotCapteurs.line_is_black(MotorSide.Left);
    let noirDroit = RobotCapteurs.line_is_black(MotorSide.Right);

    if (noirGauche && noirDroit) {
        debutBlanc = -1;
        if (debutNoir < 0) debutNoir = maintenant;

        if (!horsSol && maintenant - debutNoir >= 200) {
            horsSol = true;
            chocDetecte = false;
            arreter();
            serial.writeLine("Suspendu : deux capteurs noirs");
        }
    } else {
        debutNoir = -1;
    }

    if (horsSol) {
        // Un seul capteur blanc ne suffit pas : il faut les deux.
        if (!noirGauche && !noirDroit) {
            if (debutBlanc < 0) debutBlanc = maintenant;
            if (maintenant - debutBlanc >= 1000) {
                horsSol = false;
                debutBlanc = -1;
                commencerAvance();
                serial.writeLine("Reprise du trajet");
            }
        } else {
            debutBlanc = -1;
        }
        basic.pause(20);
        return;
    }

    if (etat == 1) {
        if (maintenant >= finEtape) {
            RobotActionneurs.RobotMovement(MovementDirection.Backward, VITESSE_RECUL, 0);
            if (interruptionDemandee()) {
                arreter();
                basic.pause(20);
                return;
            }
            etat = 2;
            finEtape = input.runningTime() + 350;
        }
    } else if (etat == 2) {
        if (maintenant >= finEtape) {
            commencerPivot();
        }
    } else if (etat == 3) {
        if (maintenant >= finEtape) {
            arreter();
            if (interruptionDemandee()) {
                basic.pause(20);
                return;
            }
            etat = 5;
            finVerification = input.runningTime() + 900;
            prochaineVerification = 0;
            lecturesProches = 0;
            lecturesLibres = 0;
            serial.writeLine("Pivot temporise termine : verification ultrason");
        }
    } else if (etat == 5) {
        if (maintenant >= prochaineVerification) {
            let distanceVerifiee = RobotCapteurs.distance_cm();
            if (etat != 5 || horsSol) {
                basic.pause(20);
                return;
            }
            prochaineVerification = input.runningTime() + 150;
            serial.writeLine("Apres pivot " + tentativesPivot + "/2 : " +
                distanceVerifiee + " cm" +
                (distanceVerifiee == 0 ? " (aucun echo)" : ""));
            if (distanceVerifiee == 0) {
                lecturesProches = 0;
                lecturesLibres = 0;
            } else if (distanceVerifiee < 10) {
                lecturesProches++;
                lecturesLibres = 0;
            } else {
                lecturesLibres++;
                lecturesProches = 0;
            }
            if (lecturesLibres >= 2) {
                serial.writeLine("Voie libre confirmee : reprise");
                commencerAvance();
            } else if (lecturesProches >= 2) {
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
            if (etat == 4 || horsSol) {
                basic.pause(20);
                return;
            }
            tentativesPivot = 0;
            etat = 1;
            finEtape = input.runningTime() + 200;
            serial.writeLine("Choc : arrêt, recul, puis pivot");
        } else {
            if (maintenant >= prochainUltrason) {
                distance = RobotCapteurs.distance_cm();
                if (etat == 4 || horsSol) {
                    basic.pause(20);
                    return;
                }
                let instantMesure = input.runningTime();
                prochainUltrason = instantMesure + 150;
                if (distance > 0 && distance < 10) {
                    serial.writeLine("Ultrason : obstacle a " + distance + " cm (<10), pivot immediat");
                } else if (instantMesure >= prochainRapportUltrason) {
                    let situation = distance == 0 ? "aucun echo, vitesse max"
                        : distance < 60 ? "ralentissement" : "voie libre, vitesse max";
                    serial.writeLine("Ultrason : " + distance + " cm, " + situation);
                    prochainRapportUltrason = instantMesure + 500;
                }
            }

            if (distance > 0 && distance < 10) {
                // Pas de recul ni de pause pour un obstacle simplement détecté.
                commencerPivot();
            } else {
                if (maintenant >= prochaineCourbe) {
                    courbe = Math.randomRange(-18, 18);
                    prochaineCourbe = maintenant + Math.randomRange(1000, 2200);
                }

                // 0 = aucun écho : traité comme « rien en vue ».
                let vitesse = VITESSE_MAX;
                if (distance >= 10 && distance < 60) {
                    vitesse = VITESSE_MIN +
                        Math.round((distance - 10) * (VITESSE_MAX - VITESSE_MIN) / 50);
                }

                let gauche = Math.max(VITESSE_MIN, Math.min(255, vitesse + courbe));
                let droite = Math.max(VITESSE_MIN, Math.min(255, vitesse - courbe));

                if (gauche != vitesseGauche || droite != vitesseDroite) {
                    RobotActionneurs.ChangeMotor(MotorSide.Left, MotorDirection.Forward, gauche, 0);
                    RobotActionneurs.ChangeMotor(MotorSide.Right, MotorDirection.Forward, droite, 0);
                    if (etat == 4 || horsSol) {
                        arreter();
                        basic.pause(20);
                        return;
                    }
                    if (vitesseGauche < 0 && vitesseDroite < 0) {
                        detectionChocActiveApres = input.runningTime() + 800;
                    }
                    vitesseGauche = gauche;
                    vitesseDroite = droite;
                }
            }
        }
    }

    basic.pause(20);
});
