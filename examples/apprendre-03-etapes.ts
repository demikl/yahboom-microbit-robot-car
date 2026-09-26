// Étape 3 : les étapes sont comme les cases d'un parcours.
// Tester d'abord roues décollées du sol. A démarre, B arrête, A+B bloque jusqu'au Reset.
const DISTANCE_MINIMALE = 15;
const VITESSE_AVANCE = 55;
const VITESSE_PIVOT = 55;
const DUREE_PIVOT = 800; // À étalonner : il n'y a pas de mesure de l'angle.

enum Etape {
    Arret,
    Avance,
    Pivote,
    Urgence
}

let etape = Etape.Arret;
let finPivot = 0;
let pivotsConsecutifs = 0;

function arreter(): void {
    RobotActionneurs.RobotMovement(MovementDirection.Stop);
}

function commencerPivot(): void {
    etape = Etape.Pivote;
    pivotsConsecutifs++;
    RobotActionneurs.RobotMovement(MovementDirection.Clockwise, VITESSE_PIVOT, 0);
    if (etape != Etape.Pivote) {
        arreter();
        return;
    }
    finPivot = input.runningTime() + DUREE_PIVOT;
}

input.onButtonPressed(Button.A, function () {
    if (etape != Etape.Urgence) {
        pivotsConsecutifs = 0;
        etape = Etape.Avance;
    }
});

input.onButtonPressed(Button.B, function () {
    if (etape != Etape.Urgence) etape = Etape.Arret;
    arreter();
});

input.onButtonPressed(Button.AB, function () {
    etape = Etape.Urgence;
    arreter();
    basic.showIcon(IconNames.No);
});

arreter();
basic.forever(function () {
    if (etape == Etape.Arret || etape == Etape.Urgence) {
        arreter();
    } else if (etape == Etape.Pivote) {
        if (input.runningTime() >= finPivot) {
            arreter();
            if (etape == Etape.Pivote) etape = Etape.Avance;
        }
    } else {
        let distance = RobotCapteurs.distance_cm();
        if (etape != Etape.Avance) {
            arreter();
        } else if (distance == 0) {
            arreter(); // Aucun écho ne prouve pas que le chemin est libre.
        } else if (distance < DISTANCE_MINIMALE) {
            arreter();
            if (etape == Etape.Avance) {
                if (pivotsConsecutifs >= 2) etape = Etape.Arret;
                else commencerPivot();
            }
        } else {
            pivotsConsecutifs = 0;
            RobotActionneurs.RobotMovement(MovementDirection.Forward, VITESSE_AVANCE, 0);
            if (etape != Etape.Avance) arreter();
        }
    }
    basic.pause(50);
});
