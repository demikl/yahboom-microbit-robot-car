// Étape 4 : on ajoute le sol et une vitesse adaptée à la distance.
// Tester d'abord roues décollées du sol. A démarre, B arrête, A+B bloque jusqu'au Reset.
const DISTANCE_OBSTACLE = 15;
const DISTANCE_RALENTISSEMENT = 60;
const VITESSE_MIN = 45;
const VITESSE_MAX = 100;
const VITESSE_PIVOT = 55;
const DUREE_PIVOT = 800; // À étalonner sur le robot.
const MS_SOL_STABLE = 1000;

enum Etape {
    Arret,
    Avance,
    Pivote,
    Urgence
}

let etape = Etape.Arret;
let solPret = false;
let blancDepuis = 0;
let finPivot = 0;
let pivotsConsecutifs = 0;

function arreter(): void {
    RobotActionneurs.RobotMovement(MovementDirection.Stop);
}

function verifierSol(): void {
    let noirGauche = RobotCapteurs.line_is_black(MotorSide.Left);
    let noirDroit = RobotCapteurs.line_is_black(MotorSide.Right);
    if (noirGauche || noirDroit) {
        solPret = false;
        blancDepuis = 0;
        if (etape != Etape.Urgence) etape = Etape.Arret;
        arreter();
    } else if (!solPret) {
        if (blancDepuis == 0) blancDepuis = input.runningTime();
        if (input.runningTime() - blancDepuis >= MS_SOL_STABLE) solPret = true;
    }
}

function vitessePourDistance(distance: number): number {
    if (distance >= DISTANCE_RALENTISSEMENT) return VITESSE_MAX;
    return VITESSE_MIN + Math.round(
        (distance - DISTANCE_OBSTACLE) * (VITESSE_MAX - VITESSE_MIN) /
        (DISTANCE_RALENTISSEMENT - DISTANCE_OBSTACLE)
    );
}

function commencerPivot(): void {
    etape = Etape.Pivote;
    pivotsConsecutifs++;
    RobotActionneurs.RobotMovement(MovementDirection.Clockwise, VITESSE_PIVOT, 0);
    if (etape != Etape.Pivote || !solPret) {
        arreter();
        return;
    }
    finPivot = input.runningTime() + DUREE_PIVOT;
}

input.onButtonPressed(Button.A, function () {
    if (solPret && etape != Etape.Urgence) {
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
    if (etape == Etape.Urgence) {
        basic.pause(50);
        return;
    }
    verifierSol();
    if (!solPret || etape == Etape.Arret) {
        arreter();
    } else if (etape == Etape.Pivote) {
        if (input.runningTime() >= finPivot) {
            arreter();
            if (etape == Etape.Pivote && solPret) etape = Etape.Avance;
        }
    } else {
        let distance = RobotCapteurs.distance_cm();
        if (etape != Etape.Avance || !solPret) {
            arreter();
        } else if (distance == 0) {
            arreter(); // Aucun écho : attendre une mesure fiable.
        } else if (distance < DISTANCE_OBSTACLE) {
            arreter();
            if (etape == Etape.Avance && solPret) {
                if (pivotsConsecutifs >= 2) etape = Etape.Arret;
                else commencerPivot();
            }
        } else {
            pivotsConsecutifs = 0;
            RobotActionneurs.RobotMovement(
                MovementDirection.Forward, vitessePourDistance(distance), 0
            );
            if (etape != Etape.Avance || !solPret) arreter();
        }
    }
    basic.pause(50);
});
