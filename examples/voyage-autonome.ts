const VITESSE_MIN = 45;
const VITESSE_MAX = 110;
const VITESSE_PIVOT = 65;
const VITESSE_RECUL = 55;
const SEUIL_CHOC = 500; // Variation d'accélération, en milli-g

let etat = 0; // 0=avance, 1=pause choc, 2=recule, 3=pivote, 4=arrêt sécurité
let horsSol = true;
let debutNoir = -1;
let debutBlanc = -1;
let finEtape = 0;
let prochainUltrason = 0;
let prochaineCourbe = 0;
let courbe = 0;
let distance = 0;
let vitesseGauche = -1;
let vitesseDroite = -1;
let chocDetecte = false;
let detectionChocActiveApres = 0;

let sensPivot = MovementDirection.Clockwise;
let capPrecedent = 0;
let angleParcouru = 0;
let angleVise = 0;
let debutPivot = 0;

function arreter(): void {
    RobotActionneurs.RobotMovement(MovementDirection.Stop);
    vitesseGauche = -1;
    vitesseDroite = -1;
}

function securite(message: string): void {
    arreter();
    etat = 4;
    serial.writeLine("ARRET SECURITE : " + message);
    basic.showIcon(IconNames.No);
}

function commencerPivot(): void {
    // Relever le cap AVANT d'actionner les moteurs.
    let cap = input.compassHeading();
    if (cap < 0 || cap >= 360) {
        securite("boussole indisponible");
        return;
    }

    capPrecedent = cap;
    angleParcouru = 0;
    angleVise = Math.randomRange(100, 170);
    sensPivot = Math.randomRange(0, 1) == 0
        ? MovementDirection.Clockwise
        : MovementDirection.CounterClockwise;
    debutPivot = input.runningTime();
    etat = 3;
    chocDetecte = false;

    RobotActionneurs.RobotMovement(sensPivot, VITESSE_PIVOT, 0);
    vitesseGauche = -1;
    vitesseDroite = -1;
    serial.writeLine("Pivot : cible " + angleVise + " degres");
}

function commencerAvance(): void {
    etat = 0;
    chocDetecte = false;
    prochaineCourbe = 0;
    prochainUltrason = 0;
    detectionChocActiveApres = input.runningTime() + 400;
    vitesseGauche = -1;
    vitesseDroite = -1;
}

// Échantillonnage rapide des trois axes, indépendant de l'ultrason.
basic.forever(function () {
    let x = input.acceleration(Dimension.X);
    let y = input.acceleration(Dimension.Y);
    let z = input.acceleration(Dimension.Z);

    basic.pause(15);

    let suivantX = input.acceleration(Dimension.X);
    let suivantY = input.acceleration(Dimension.Y);
    let suivantZ = input.acceleration(Dimension.Z);
    let variation = Math.max(
        Math.abs(suivantX - x),
        Math.max(Math.abs(suivantY - y), Math.abs(suivantZ - z))
    );

    if (!horsSol && etat == 0 &&
        input.runningTime() >= detectionChocActiveApres &&
        variation >= SEUIL_CHOC) {
        chocDetecte = true;
    }
});

// A+B : arrêt d'urgence définitif jusqu'au bouton Reset.
input.onButtonPressed(Button.AB, function () {
    securite("boutons A+B");
});

arreter();
basic.showString("CAL");
input.calibrateCompass();
if (input.compassHeading() < 0) {
    securite("calibration boussole");
} else {
    basic.clearScreen();
    serial.writeLine("Pret : poser le robot au sol");
}

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
            etat = 2;
            finEtape = maintenant + 350;
        }
    } else if (etat == 2) {
        if (maintenant >= finEtape) {
            commencerPivot();
        }
    } else if (etat == 3) {
        let cap = input.compassHeading();
        if (cap < 0 || cap >= 360) {
            securite("cap perdu pendant le pivot");
        } else {
            // Différence orientée, y compris au passage de 359 à 0 degrés.
            let pas = sensPivot == MovementDirection.Clockwise
                ? (cap - capPrecedent + 360) % 360
                : (capPrecedent - cap + 360) % 360;

            // Ignorer un saut aberrant du magnétomètre.
            if (pas <= 30) {
                angleParcouru += pas;
                capPrecedent = cap;
            }

            if (angleParcouru >= angleVise) {
                arreter();
                commencerAvance();
                serial.writeLine("Pivot termine : " + angleParcouru + " degres");
            } else if (maintenant - debutPivot >= 1000) {
                securite("pivot non confirme en 1 seconde");
            }
        }
    } else {
        // Le choc prime sur l'évitement préventif.
        if (chocDetecte) {
            chocDetecte = false;
            arreter();
            etat = 1;
            finEtape = maintenant + 200;
            serial.writeLine("Choc : arrêt, recul, puis pivot");
        } else {
            if (maintenant >= prochainUltrason) {
                distance = RobotCapteurs.distance_cm();
                prochainUltrason = input.runningTime() + 150;
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
                    vitesseGauche = gauche;
                    vitesseDroite = droite;
                }
            }
        }
    }

    basic.pause(20);
});
